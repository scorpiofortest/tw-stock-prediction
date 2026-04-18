"""9-Signal Weighted Scoring Engine per PRD Section 3."""

import asyncio
import math
import statistics
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import numpy as np
from loguru import logger


# ─── Data classes ──────────────────────────────────────────────────

@dataclass
class SignalResult:
    name: str
    value: float           # raw indicator value
    score: float           # -100 to +100
    weight: float          # 0.0 to 1.0
    weighted_score: float  # score * weight
    description: str
    reliability: float = 1.0  # 0.0 to 1.0


@dataclass
class CompositeScore:
    stock_id: str
    stock_name: str
    total_score: float
    direction: str
    confidence: float
    signal_agreement: str
    signals: list[SignalResult]
    calculated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class MarketData:
    """All data needed for signal calculations."""
    stock_id: str
    stock_name: str
    current_price: float
    prev_close: float
    open_price: float
    high_price: float
    low_price: float
    volume: int
    # Tick data
    outer_volume: int = 0
    inner_volume: int = 0
    # 5-level order book
    bid_volumes: list[int] = field(default_factory=lambda: [0]*5)
    ask_volumes: list[int] = field(default_factory=lambda: [0]*5)
    # Recent 10 ticks
    recent_ticks: list[dict] = field(default_factory=list)
    # Minute OHLC bars for technical indicators (oldest first)
    minute_closes: list[float] = field(default_factory=list)
    minute_highs: list[float] = field(default_factory=list)
    minute_lows: list[float] = field(default_factory=list)
    # Previous minute change_pct for momentum
    prev_minute_change_pct: float = 0.0
    # Prices for acceleration (t-2, t-1, t)
    price_t_minus_2: Optional[float] = None
    price_t_minus_1: Optional[float] = None
    # --- New fields for 6 additional signals ---
    # Institutional (法人) data from TWSE
    institutional_data: Optional[dict] = None   # {foreign_net, trust_net, dealer_net, total_net, ...}
    margin_data: Optional[dict] = None          # {margin_net, short_net, ...}
    # Daily volumes list for volume-price analysis (oldest first)
    daily_volumes: list[int] = field(default_factory=list)
    # TAIEX (加權指數) data
    taiex_current: Optional[float] = None
    taiex_prev_close: Optional[float] = None
    # SOX (費半) data
    sox_current: Optional[float] = None
    sox_prev_close: Optional[float] = None
    # Market timestamp for time factor
    market_timestamp: Optional[datetime] = None


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


# ─── Base Signal ───────────────────────────────────────────────────

class BaseSignal(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def weight(self) -> float: ...

    @abstractmethod
    async def calculate(self, data: MarketData) -> SignalResult: ...

    def _result(self, value: float, score: float, desc: str, reliability: float = 1.0) -> SignalResult:
        s = _clamp(score, -100, 100)
        return SignalResult(
            name=self.name,
            value=round(value, 4),
            score=round(s, 2),
            weight=self.weight,
            weighted_score=round(s * self.weight, 4),
            description=desc,
            reliability=reliability,
        )


# ─── Signal 1: Outer Ratio (15%) ──────────────────────────────────

class OuterRatioSignal(BaseSignal):
    name = "外盤比率"
    weight = 0.08

    async def calculate(self, data: MarketData) -> SignalResult:
        total = data.outer_volume + data.inner_volume
        if total == 0:
            return self._result(50.0, 0, "無成交量資料", 0.3)

        ratio = data.outer_volume / total * 100  # percentage 0-100

        if ratio >= 75:
            score = 80 + (ratio - 75) * 0.8
        elif ratio >= 60:
            score = 30 + (ratio - 60) * (50 / 15)
        elif ratio >= 55:
            score = 10 + (ratio - 55) * (20 / 5)
        elif ratio >= 45:
            score = (ratio - 50) * 2
        elif ratio >= 40:
            score = -10 - (45 - ratio) * (20 / 5)
        elif ratio >= 25:
            score = -30 - (40 - ratio) * (50 / 15)
        else:
            score = -80 - (25 - ratio) * 0.8

        desc = f"外盤比率{ratio:.1f}%，"
        if score >= 30:
            desc += "買方主動攻擊明顯"
        elif score >= 5:
            desc += "略偏買方"
        elif score >= -5:
            desc += "買賣均衡"
        elif score >= -30:
            desc += "略偏賣方"
        else:
            desc += "賣方主動拋售明顯"

        return self._result(ratio, score, desc)


# ─── Signal 2: Bid-Ask Pressure (12%) ─────────────────────────────

class BidAskPressureSignal(BaseSignal):
    name = "五檔委買委賣壓力"
    weight = 0.07

    async def calculate(self, data: MarketData) -> SignalResult:
        bid_total = sum(data.bid_volumes)
        ask_total = sum(data.ask_volumes)
        total = bid_total + ask_total

        if total == 0:
            return self._result(0.0, 0, "無五檔資料", 0.3)

        pressure = (bid_total - ask_total) / total  # -1.0 to +1.0

        # Low volume reliability discount
        reliability = 1.0
        if min(bid_total, ask_total) < 50:
            reliability = 0.5

        if pressure >= 0.5:
            score = 80 + (pressure - 0.5) * 40
        elif pressure >= 0.2:
            score = 30 + (pressure - 0.2) * (50 / 0.3)
        elif pressure >= 0.05:
            score = 5 + (pressure - 0.05) * (25 / 0.15)
        elif pressure >= -0.05:
            score = pressure * 100
        elif pressure >= -0.2:
            score = -5 - (abs(pressure) - 0.05) * (25 / 0.15)
        elif pressure >= -0.5:
            score = -30 - (abs(pressure) - 0.2) * (50 / 0.3)
        else:
            score = -80 - (abs(pressure) - 0.5) * 40

        desc = f"壓力比{pressure:+.2f}，"
        if score >= 30:
            desc += "委買量明顯大於委賣"
        elif score >= 5:
            desc += "委買略大於委賣"
        elif score >= -5:
            desc += "買賣掛單均衡"
        elif score >= -30:
            desc += "委賣略大於委買"
        else:
            desc += "委賣量明顯大於委買"

        return self._result(pressure, score, desc, reliability)


# ─── Signal 3: Tick Direction (10%) ───────────────────────────────

class TickDirectionSignal(BaseSignal):
    name = "最近10筆成交方向"
    weight = 0.06

    async def calculate(self, data: MarketData) -> SignalResult:
        ticks = data.recent_ticks[-10:] if data.recent_ticks else []
        n = len(ticks)
        if n == 0:
            return self._result(0.0, 0, "無成交明細", 0.3)

        outer_count = sum(1 for t in ticks if t.get("side") == "buy")
        inner_count = n - outer_count
        direction_ratio = (outer_count - inner_count) / n

        # Weighted by volume
        w_outer = sum(t.get("volume", 1) for t in ticks if t.get("side") == "buy")
        w_inner = sum(t.get("volume", 1) for t in ticks if t.get("side") != "buy")
        w_total = w_outer + w_inner
        weighted_direction = (w_outer - w_inner) / w_total if w_total > 0 else 0

        final_direction = 0.4 * direction_ratio + 0.6 * weighted_direction
        score = _clamp(final_direction * 100, -100, 100)

        desc = f"近{n}筆外盤{outer_count}筆，"
        if score >= 20:
            desc += "以外盤為主"
        elif score >= -20:
            desc += "內外盤均衡"
        else:
            desc += "以內盤為主"

        return self._result(final_direction, score, desc)


# ─── Signal 4: Intraday Position (8%) ─────────────────────────────

class IntradayPositionSignal(BaseSignal):
    name = "日內高低位置"
    weight = 0.05

    async def calculate(self, data: MarketData) -> SignalResult:
        high = data.high_price
        low = data.low_price
        current = data.current_price
        open_price = data.open_price

        if high == low or high == 0:
            return self._result(50.0, 0, "無振幅", 0.3)

        pos_pct = (current - low) / (high - low) * 100

        # Non-linear scoring
        if pos_pct >= 90:
            score = 70 + (pos_pct - 90) * 3
        elif pos_pct >= 70:
            score = 20 + (pos_pct - 70) * 2.5
        elif pos_pct >= 50:
            score = (pos_pct - 50) * 1
        elif pos_pct >= 30:
            score = (pos_pct - 50) * 1
        elif pos_pct >= 10:
            score = -20 - (30 - pos_pct) * 2.5
        else:
            score = -70 - (10 - pos_pct) * 3

        # Amplitude attenuation
        amplitude = (high - low) / open_price * 100 if open_price > 0 else 0
        if amplitude < 0.3:
            score *= 0.3
        elif amplitude < 0.8:
            score *= 0.6

        desc = f"位於日內{pos_pct:.0f}%位置，"
        if pos_pct >= 70:
            desc += "偏高檔"
        elif pos_pct >= 30:
            desc += "中間位置"
        else:
            desc += "偏低檔"

        reliability = 1.0 if amplitude >= 0.8 else (0.6 if amplitude >= 0.3 else 0.3)
        return self._result(pos_pct, score, desc, reliability)


# ─── Signal 5: Momentum (10%) ─────────────────────────────────────

class MomentumSignal(BaseSignal):
    name = "即時漲跌幅動能"
    weight = 0.06

    async def calculate(self, data: MarketData) -> SignalResult:
        if data.prev_close == 0:
            return self._result(0.0, 0, "無昨收價資料", 0.3)

        change_pct = (data.current_price - data.prev_close) / data.prev_close * 100
        momentum_delta = change_pct - data.prev_minute_change_pct

        # Base score from absolute change
        abs_chg = abs(change_pct)
        if change_pct >= 5:
            base = 80
        elif change_pct >= 2:
            base = 40 + (change_pct - 2) * (40 / 3)
        elif change_pct >= 0.5:
            base = 10 + (change_pct - 0.5) * (30 / 1.5)
        elif change_pct >= -0.5:
            base = change_pct * 20
        elif change_pct >= -2:
            base = -10 - (abs_chg - 0.5) * (30 / 1.5)
        elif change_pct >= -5:
            base = -40 - (abs_chg - 2) * (40 / 3)
        else:
            base = -80

        momentum_score = _clamp(momentum_delta * 100, -20, 20)
        score = _clamp(base + momentum_score, -100, 100)

        desc = f"漲跌幅{change_pct:+.2f}%，"
        if momentum_delta > 0.05:
            desc += "動能持續擴大"
        elif momentum_delta < -0.05:
            desc += "動能收斂中"
        else:
            desc += "動能穩定"

        return self._result(change_pct, score, desc)


# ─── Signal 6: RSI with reversal logic (12%) ──────────────────────

class RSISignal(BaseSignal):
    name = "RSI"
    weight = 0.07

    async def calculate(self, data: MarketData) -> SignalResult:
        closes = data.minute_closes
        if len(closes) < 15:
            return self._result(50.0, 0, "RSI數據不足", 0.5)

        rsi = self._calc_rsi(closes, period=14)

        # Reversal-aware scoring per PRD
        if rsi > 80:
            score = -50 - (rsi - 80) * 2.5  # overbought -> bearish reversal
        elif rsi > 65:
            score = 30 + (rsi - 65) * (20 / 15)
        elif rsi > 55:
            score = 10 + (rsi - 55) * 2
        elif rsi >= 45:
            score = (rsi - 50) * 2
        elif rsi >= 35:
            score = -10 - (45 - rsi) * 2
        elif rsi >= 20:
            score = -30 - (35 - rsi) * (20 / 15)
        else:
            score = 50 + (20 - rsi) * 2.5  # oversold -> bullish reversal

        desc = f"RSI(14)={rsi:.1f}，"
        if rsi > 80:
            desc += "超買區，預期回檔"
        elif rsi > 65:
            desc += "偏多區間"
        elif rsi > 55:
            desc += "溫和多方"
        elif rsi >= 45:
            desc += "中性區間"
        elif rsi >= 35:
            desc += "溫和空方"
        elif rsi >= 20:
            desc += "偏空區間"
        else:
            desc += "超賣區，預期反彈"

        return self._result(rsi, score, desc)

    @staticmethod
    def _calc_rsi(closes: list[float], period: int = 14) -> float:
        if len(closes) < period + 1:
            return 50.0
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))


# ─── Signal 7: MACD OSC (13%) ─────────────────────────────────────

class MACDOscSignal(BaseSignal):
    name = "MACD OSC"
    weight = 0.07

    async def calculate(self, data: MarketData) -> SignalResult:
        closes = data.minute_closes
        if len(closes) < 35:
            return self._result(0.0, 0, "MACD數據不足", 0.5)

        dif_list, signal_list, osc_list = self._calc_macd(closes)
        if len(osc_list) < 2:
            return self._result(0.0, 0, "MACD數據不足", 0.5)

        osc = osc_list[-1]
        osc_prev = osc_list[-2]

        # Normalize by max |OSC| over last 60 bars
        recent_osc = osc_list[-60:] if len(osc_list) >= 60 else osc_list
        max_osc = max(abs(v) for v in recent_osc) if recent_osc else 1
        normalized = osc / max_osc if max_osc != 0 else 0

        base = normalized * 70

        # Direction correction
        osc_delta = osc - osc_prev
        if osc_delta > 0 and osc > 0:
            direction_adj = 15   # bullish acceleration
        elif osc_delta < 0 and osc < 0:
            direction_adj = -15  # bearish acceleration
        elif osc_delta > 0 and osc < 0:
            direction_adj = 10   # bearish converging
        elif osc_delta < 0 and osc > 0:
            direction_adj = -10  # bullish converging
        else:
            direction_adj = 0

        # Zero-axis crossing
        zero_cross = 0
        if osc_prev < 0 and osc > 0:
            zero_cross = 15
        elif osc_prev > 0 and osc < 0:
            zero_cross = -15

        score = _clamp(base + direction_adj + zero_cross, -100, 100)

        desc = f"OSC={osc:.4f}，"
        if zero_cross > 0:
            desc += "由負轉正（多頭訊號）"
        elif zero_cross < 0:
            desc += "由正轉負（空頭訊號）"
        elif osc > 0 and osc_delta > 0:
            desc += "正值且持續放大"
        elif osc > 0 and osc_delta < 0:
            desc += "正值但收斂中"
        elif osc < 0 and osc_delta < 0:
            desc += "負值且持續擴大"
        elif osc < 0 and osc_delta > 0:
            desc += "負值但收斂中"
        else:
            desc += "接近零軸"

        return self._result(osc, score, desc)

    @staticmethod
    def _calc_macd(closes: list[float], fast=12, slow=26, signal_period=9):
        def ema(data, period):
            result = [data[0]]
            k = 2 / (period + 1)
            for i in range(1, len(data)):
                result.append(data[i] * k + result[-1] * (1 - k))
            return result

        ema12 = ema(closes, fast)
        ema26 = ema(closes, slow)
        dif = [a - b for a, b in zip(ema12, ema26)]
        signal_line = ema(dif, signal_period)
        osc = [d - s for d, s in zip(dif, signal_line)]
        return dif, signal_line, osc


# ─── Signal 8: KD Cross (12%) ─────────────────────────────────────

class KDCrossSignal(BaseSignal):
    name = "KD交叉"
    weight = 0.06

    async def calculate(self, data: MarketData) -> SignalResult:
        highs = data.minute_highs
        lows = data.minute_lows
        closes = data.minute_closes
        if len(closes) < 10:
            return self._result(0.0, 0, "KD數據不足", 0.5)

        k_list, d_list = self._calc_kd(highs, lows, closes, period=9)
        if len(k_list) < 2:
            return self._result(0.0, 0, "KD數據不足", 0.5)

        k_curr, k_prev = k_list[-1], k_list[-2]
        d_curr, d_prev = d_list[-1], d_list[-2]

        golden_cross = (k_prev < d_prev) and (k_curr > d_curr)
        death_cross = (k_prev > d_prev) and (k_curr < d_curr)
        k_above_d = k_curr > d_curr
        k_below_d = k_curr < d_curr

        # Cross event score
        if golden_cross:
            cross_score = 50
        elif death_cross:
            cross_score = -50
        elif k_above_d:
            cross_score = 15
        elif k_below_d:
            cross_score = -15
        else:
            cross_score = 0

        # Position bonus
        pos_bonus = 0
        if golden_cross and k_curr < 30:
            pos_bonus = 30
        elif golden_cross and k_curr < 50:
            pos_bonus = 15
        elif death_cross and k_curr > 70:
            pos_bonus = -30
        elif death_cross and k_curr > 50:
            pos_bonus = -15

        # Trend score
        k_trend = k_curr - k_prev
        trend_score = _clamp(k_trend * 2, -20, 20)

        score = _clamp(cross_score + pos_bonus + trend_score, -100, 100)

        desc = f"K={k_curr:.1f} D={d_curr:.1f}，"
        if golden_cross:
            desc += "黃金交叉" + ("（低檔強勢）" if k_curr < 30 else "")
        elif death_cross:
            desc += "死亡交叉" + ("（高檔弱勢）" if k_curr > 70 else "")
        elif k_above_d:
            desc += "K在D上方，多頭持續"
        elif k_below_d:
            desc += "K在D下方，空頭持續"
        else:
            desc += "K與D接近"

        return self._result(k_curr, score, desc)

    @staticmethod
    def _calc_kd(highs, lows, closes, period=9):
        n = len(closes)
        if n < period:
            return [], []
        k_list, d_list = [], []
        k_prev, d_prev = 50.0, 50.0
        for i in range(period - 1, n):
            h = max(highs[i-period+1:i+1])
            l = min(lows[i-period+1:i+1])
            if h == l:
                rsv = 50.0
            else:
                rsv = (closes[i] - l) / (h - l) * 100
            k = k_prev * (2/3) + rsv * (1/3)
            d = d_prev * (2/3) + k * (1/3)
            k_list.append(k)
            d_list.append(d)
            k_prev, d_prev = k, d
        return k_list, d_list


# ─── Signal 9: Trend Acceleration (8%) ────────────────────────────

class TrendAccelerationSignal(BaseSignal):
    name = "盤中走勢加速度"
    weight = 0.03

    async def calculate(self, data: MarketData) -> SignalResult:
        p0 = data.price_t_minus_2
        p1 = data.price_t_minus_1
        p2 = data.current_price

        if p0 is None or p1 is None or p0 == 0 or p1 == 0:
            return self._result(0.0, 0, "加速度數據不足", 0.5)

        v1 = (p1 - p0) / p0 * 100
        v2 = (p2 - p1) / p1 * 100
        acceleration = v2 - v1

        normalized_acc = _clamp(acceleration / 0.2, -1.0, 1.0)
        base = normalized_acc * 60

        # Direction consistency bonus
        if v2 > 0 and acceleration > 0:
            consistency = 20   # rising accelerating
        elif v2 < 0 and acceleration < 0:
            consistency = -20  # falling accelerating
        elif v2 > 0 and acceleration < 0:
            consistency = -10  # rising decelerating
        elif v2 < 0 and acceleration > 0:
            consistency = 10   # falling decelerating
        else:
            consistency = 0

        score = _clamp(base + consistency, -100, 100)

        desc = f"加速度={acceleration:+.4f}%，"
        if v2 > 0 and acceleration > 0:
            desc += "上漲加速中"
        elif v2 < 0 and acceleration < 0:
            desc += "下跌加速中"
        elif v2 > 0 and acceleration < 0:
            desc += "上漲減速，留意反轉"
        elif v2 < 0 and acceleration > 0:
            desc += "下跌減速，可能反彈"
        else:
            desc += "走勢平穩"

        return self._result(acceleration, score, desc)


# ─── Signal 10: Institutional Flow (15%) ─────────────────────────

class InstitutionalFlowSignal(BaseSignal):
    name = "籌碼面"
    weight = 0.15

    async def calculate(self, data: MarketData) -> SignalResult:
        inst = data.institutional_data
        margin = data.margin_data

        if inst is None:
            return self._result(0.0, 0, "無法取得籌碼資料", 0.2)

        total_net = inst.get("total_net", 0)
        avg_vol = sum(data.daily_volumes[-5:]) / 5 if data.daily_volumes else data.volume
        if avg_vol <= 0:
            avg_vol = 1

        # Normalize: net buy/sell as fraction of avg daily volume
        net_ratio = total_net / avg_vol
        institutional_score = _clamp(net_ratio * 200, -100, 100) * 0.7

        # Margin component (30%)
        margin_score = 0.0
        if margin and (margin.get("margin_net", 0) != 0 or margin.get("short_net", 0) != 0):
            margin_net = margin.get("margin_net", 0)
            short_net = margin.get("short_net", 0)
            # Margin decrease + short increase = bearish for retail, bullish signal
            # Margin increase + short decrease = bullish for retail, bearish signal (contrarian)
            margin_signal = -margin_net / max(avg_vol * 0.01, 1) + short_net / max(avg_vol * 0.01, 1)
            margin_score = _clamp(margin_signal * 50, -100, 100) * 0.3

        score = _clamp(institutional_score + margin_score, -100, 100)

        # Description
        parts = []
        if total_net > 0:
            parts.append(f"法人買超{total_net:,}股")
        elif total_net < 0:
            parts.append(f"法人賣超{abs(total_net):,}股")
        else:
            parts.append("法人無明顯動作")

        foreign_net = inst.get("foreign_net", 0)
        trust_net = inst.get("trust_net", 0)
        if foreign_net > 0:
            parts.append("外資買超")
        elif foreign_net < 0:
            parts.append("外資賣超")
        if trust_net > 0:
            parts.append("投信買超")
        elif trust_net < 0:
            parts.append("投信賣超")

        desc = "，".join(parts)
        return self._result(total_net, score, desc)


# ─── Signal 11: Volume-Price Structure (8%) ──────────────────────

class VolumePriceStructureSignal(BaseSignal):
    name = "量價結構"
    weight = 0.08

    async def calculate(self, data: MarketData) -> SignalResult:
        volumes = data.daily_volumes
        closes = data.minute_closes

        if len(volumes) < 5 or len(closes) < 5:
            return self._result(0.0, 0, "量價數據不足", 0.3)

        today_vol = volumes[-1] if volumes else data.volume
        avg_vol_5 = sum(volumes[-6:-1]) / 5 if len(volumes) >= 6 else sum(volumes[-5:]) / max(len(volumes[-5:]), 1)
        avg_vol_20 = sum(volumes[-21:-1]) / 20 if len(volumes) >= 21 else avg_vol_5

        if avg_vol_5 <= 0:
            avg_vol_5 = 1
        if avg_vol_20 <= 0:
            avg_vol_20 = 1

        # Relative volume ratio
        vol_ratio_5 = today_vol / avg_vol_5
        vol_ratio_20 = today_vol / avg_vol_20

        # Volume score: above average = stronger signal
        vol_score = _clamp((vol_ratio_5 - 1.0) * 40 + (vol_ratio_20 - 1.0) * 20, -60, 60)

        # Price direction
        price_change = closes[-1] - closes[-2] if len(closes) >= 2 else 0
        price_up = price_change > 0

        # Divergence detection
        divergence = 0
        if price_up and vol_ratio_5 < 0.7:
            # Price up but volume shrinking → bearish divergence
            divergence = -30
        elif not price_up and vol_ratio_5 > 1.3:
            # Price down but volume expanding → potential capitulation or bearish
            divergence = -20
        elif price_up and vol_ratio_5 > 1.3:
            # Price up with volume → bullish confirmation
            divergence = 25
        elif not price_up and vol_ratio_5 < 0.7:
            # Price down with low volume → less bearish
            divergence = 10

        # Combine: direction * volume strength + divergence
        direction_mult = 1 if price_up else -1
        score = _clamp(direction_mult * abs(vol_score) * 0.6 + divergence, -100, 100)

        desc = f"量比{vol_ratio_5:.1f}倍，"
        if vol_ratio_5 > 1.5:
            desc += "爆量"
        elif vol_ratio_5 > 1.0:
            desc += "量增"
        elif vol_ratio_5 > 0.7:
            desc += "量平"
        else:
            desc += "量縮"

        if divergence < -15:
            desc += "，量價背離"
        elif divergence > 15:
            desc += "，量價配合"

        return self._result(vol_ratio_5, score, desc)


# ─── Signal 12: Market Correlation (8%) ──────────────────────────

class MarketCorrelationSignal(BaseSignal):
    name = "大盤連動"
    weight = 0.08

    async def calculate(self, data: MarketData) -> SignalResult:
        taiex_current = data.taiex_current
        taiex_prev = data.taiex_prev_close
        sox_current = data.sox_current
        sox_prev = data.sox_prev_close

        has_taiex = taiex_current is not None and taiex_prev is not None and taiex_prev > 0
        has_sox = sox_current is not None and sox_prev is not None and sox_prev > 0

        if not has_taiex and not has_sox:
            return self._result(0.0, 0, "無大盤資料", 0.3)

        score = 0.0
        parts = []

        if has_taiex:
            taiex_chg = (taiex_current - taiex_prev) / taiex_prev * 100
            taiex_score = _clamp(taiex_chg * 25, -100, 100)
            score += taiex_score * 0.6
            parts.append(f"加權{taiex_chg:+.2f}%")

        if has_sox:
            sox_chg = (sox_current - sox_prev) / sox_prev * 100
            sox_score = _clamp(sox_chg * 20, -100, 100)
            score += sox_score * 0.4
            parts.append(f"費半{sox_chg:+.2f}%")

        score = _clamp(score, -100, 100)
        desc = "，".join(parts)

        if score > 20:
            desc += "，大盤偏多"
        elif score < -20:
            desc += "，大盤偏空"
        else:
            desc += "，大盤中性"

        reliability = 1.0 if has_taiex and has_sox else 0.6
        return self._result(score, score, desc, reliability)


# ─── Signal 13: Moving Average System (7%) ───────────────────────

class MovingAverageSystemSignal(BaseSignal):
    name = "均線系統"
    weight = 0.07

    async def calculate(self, data: MarketData) -> SignalResult:
        closes = data.minute_closes
        if len(closes) < 60:
            return self._result(0.0, 0, "均線數據不足", 0.3)

        current = closes[-1]
        ma5 = sum(closes[-5:]) / 5
        ma10 = sum(closes[-10:]) / 10
        ma20 = sum(closes[-20:]) / 20
        ma60 = sum(closes[-60:]) / 60

        # 1. Position score: how many MAs is price above?
        above_count = sum(1 for ma in [ma5, ma10, ma20, ma60] if current > ma)
        position_score = (above_count - 2) * 25  # -50 to +50

        # 2. Alignment score: bullish/bearish alignment
        alignment_score = 0
        if ma5 > ma10 > ma20 > ma60:
            alignment_score = 40  # perfect bullish alignment
        elif ma5 > ma10 > ma20:
            alignment_score = 25
        elif ma5 > ma10:
            alignment_score = 10
        elif ma5 < ma10 < ma20 < ma60:
            alignment_score = -40  # perfect bearish alignment
        elif ma5 < ma10 < ma20:
            alignment_score = -25
        elif ma5 < ma10:
            alignment_score = -10

        # 3. BIAS (乖離率) from MA20
        bias_20 = (current - ma20) / ma20 * 100 if ma20 > 0 else 0
        # Extreme bias means reversion: high positive bias → overbought (slightly bearish)
        if abs(bias_20) > 10:
            bias_score = -bias_20 * 2  # mean reversion
        else:
            bias_score = bias_20 * 3   # trend following

        bias_score = _clamp(bias_score, -30, 30)

        score = _clamp(position_score * 0.4 + alignment_score * 0.35 + bias_score * 0.25, -100, 100)

        # Description
        if alignment_score >= 25:
            align_desc = "多頭排列"
        elif alignment_score <= -25:
            align_desc = "空頭排列"
        else:
            align_desc = "均線糾結"

        desc = f"價在MA{'上' if current > ma20 else '下'}，{align_desc}，乖離{bias_20:+.1f}%"
        return self._result(bias_20, score, desc)


# ─── Signal 14: Volatility Risk (4%) ─────────────────────────────

class VolatilityRiskSignal(BaseSignal):
    name = "波動率"
    weight = 0.04

    async def calculate(self, data: MarketData) -> SignalResult:
        closes = data.minute_closes
        if len(closes) < 20:
            return self._result(0.0, 0, "波動率數據不足", 0.3)

        current = closes[-1]

        # Bollinger Bands (20MA ± 2σ)
        ma20 = sum(closes[-20:]) / 20
        std20 = (sum((c - ma20) ** 2 for c in closes[-20:]) / 20) ** 0.5
        upper_band = ma20 + 2 * std20
        lower_band = ma20 - 2 * std20
        band_width = upper_band - lower_band

        if band_width <= 0:
            return self._result(0.0, 0, "布林帶寬度為零", 0.3)

        # Position within Bollinger Bands (0 = lower, 1 = upper)
        bb_position = (current - lower_band) / band_width

        # BB score: near upper = overbought (bearish), near lower = oversold (bullish)
        if bb_position > 0.95:
            bb_score = -60
        elif bb_position > 0.8:
            bb_score = -30
        elif bb_position > 0.6:
            bb_score = -10
        elif bb_position > 0.4:
            bb_score = 0
        elif bb_position > 0.2:
            bb_score = 10
        elif bb_position > 0.05:
            bb_score = 30
        else:
            bb_score = 60

        # ATR(14)
        highs = data.minute_highs
        lows = data.minute_lows
        if len(highs) >= 15 and len(lows) >= 15:
            trs = []
            for i in range(-14, 0):
                tr = max(
                    highs[i] - lows[i],
                    abs(highs[i] - closes[i - 1]),
                    abs(lows[i] - closes[i - 1]),
                )
                trs.append(tr)
            atr = sum(trs) / len(trs)
            atr_pct = atr / current * 100 if current > 0 else 0
        else:
            atr_pct = 0

        # High volatility reduces reliability
        reliability = 1.0
        if atr_pct > 5:
            reliability = 0.4
        elif atr_pct > 3:
            reliability = 0.6
        elif atr_pct > 2:
            reliability = 0.8

        score = _clamp(bb_score, -100, 100)

        desc = f"BB位置{bb_position:.0%}，ATR{atr_pct:.1f}%，"
        if bb_position > 0.8:
            desc += "接近上軌（超買）"
        elif bb_position < 0.2:
            desc += "接近下軌（超賣）"
        else:
            desc += "通道中間"

        return self._result(bb_position, score, desc, reliability)


# ─── Signal 15: Time Factor (3%) ─────────────────────────────────

class TimeFactorSignal(BaseSignal):
    name = "時間因子"
    weight = 0.03

    async def calculate(self, data: MarketData) -> SignalResult:
        ts = data.market_timestamp or datetime.now()
        weekday = ts.weekday()  # 0=Mon, 4=Fri, 5=Sat, 6=Sun

        # Weekend / holiday detection
        is_weekend = weekday >= 5

        if is_weekend:
            # Weekend: market closed, focus on Monday outlook
            # Use last trading day's data context to project Monday
            # Historically Taiwan market has slight Monday bullish bias
            # (weekend news digestion, institutional repositioning)
            session_score = 5
            session_desc = "週末休市"

            # Check international market cues (SOX for tech-heavy TWSE)
            sox_cue = 0
            sox_desc = ""
            if data.sox_current and data.sox_prev_close and data.sox_prev_close > 0:
                sox_chg = (data.sox_current - data.sox_prev_close) / data.sox_prev_close * 100
                if sox_chg > 1:
                    sox_cue = 15
                    sox_desc = "，費半上漲有利週一開盤"
                elif sox_chg < -1:
                    sox_cue = -15
                    sox_desc = "，費半下跌週一恐開低"
                else:
                    sox_desc = "，國際盤變化不大"

            score = _clamp(session_score + sox_cue, -100, 100)
            day_name = "週六" if weekday == 5 else "週日"
            desc = f"{day_name}{session_desc}，預估週一開盤走勢{sox_desc}"

            return self._result(score, score, desc, 0.4)

        # Trading day logic
        hour = ts.hour
        minute = ts.minute
        time_minutes = hour * 60 + minute

        if 9 * 60 <= time_minutes < 9 * 60 + 15:
            session_score = 10
            session_desc = "開盤階段"
        elif 9 * 60 + 15 <= time_minutes < 10 * 60:
            session_score = 5
            session_desc = "盤初"
        elif 10 * 60 <= time_minutes < 12 * 60:
            session_score = 0
            session_desc = "午前盤"
        elif 12 * 60 <= time_minutes < 13 * 60:
            session_score = -5
            session_desc = "午盤"
        elif 13 * 60 <= time_minutes <= 13 * 60 + 30:
            session_score = 5
            session_desc = "尾盤"
        elif time_minutes < 9 * 60:
            session_score = 5
            session_desc = "盤前"
        else:
            session_score = 0
            session_desc = "盤後"

        # Day of week effect
        day_scores = {
            0: 10,   # Monday: slight bullish
            1: 5,    # Tuesday: mild
            2: 0,    # Wednesday: neutral
            3: -5,   # Thursday: mild bearish
            4: -10,  # Friday: slight bearish (weekend risk)
        }
        day_score = day_scores.get(weekday, 0)
        day_names = {0: "週一", 1: "週二", 2: "週三", 3: "週四", 4: "週五"}
        day_name = day_names.get(weekday, "")

        score = _clamp(session_score * 0.6 + day_score * 0.4, -100, 100)
        desc = f"{session_desc}，{day_name}效應"

        return self._result(score, score, desc, 0.5)


# ─── Signal Engine ─────────────────────────────────────────────────

class SignalEngine:
    """Core engine that evaluates all 15 signals and produces a composite score."""

    def __init__(self):
        self.signals: list[BaseSignal] = [
            # Original 9 signals (55% total)
            OuterRatioSignal(),             # 8%
            BidAskPressureSignal(),         # 7%
            TickDirectionSignal(),          # 6%
            IntradayPositionSignal(),       # 5%
            MomentumSignal(),               # 6%
            RSISignal(),                    # 7%
            MACDOscSignal(),                # 7%
            KDCrossSignal(),                # 6%
            TrendAccelerationSignal(),      # 3%
            # New 6 signals (45% total)
            InstitutionalFlowSignal(),      # 15%
            VolumePriceStructureSignal(),   # 8%
            MarketCorrelationSignal(),      # 8%
            MovingAverageSystemSignal(),    # 7%
            VolatilityRiskSignal(),         # 4%
            TimeFactorSignal(),             # 3%
        ]

    async def evaluate(self, data: MarketData) -> CompositeScore:
        """Run all 15 signals in parallel and produce a composite score."""
        results = await asyncio.gather(
            *[sig.calculate(data) for sig in self.signals]
        )

        # Apply conflict resolution
        results = self._resolve_conflicts(results)

        # Reliability-adjusted scoring: signals with low reliability contribute less
        total_effective_weight = sum(r.weight * r.reliability for r in results)
        if total_effective_weight > 0:
            total_score = sum(r.score * r.weight * r.reliability for r in results) / total_effective_weight
        else:
            total_score = 0
        total_score = _clamp(total_score, -100, 100)

        direction = self._determine_direction(total_score)
        confidence = self._calculate_confidence(results, total_score)

        # Signal agreement
        n = len(results)
        if total_score >= 5:
            same_dir = sum(1 for r in results if r.score > 0)
        elif total_score <= -5:
            same_dir = sum(1 for r in results if r.score < 0)
        else:
            same_dir = sum(1 for r in results if -4 <= r.score <= 4)
        agreement = f"{same_dir}/{n}訊號同向"

        return CompositeScore(
            stock_id=data.stock_id,
            stock_name=data.stock_name,
            total_score=round(total_score, 2),
            direction=direction,
            confidence=round(confidence, 1),
            signal_agreement=agreement,
            signals=results,
        )

    def _determine_direction(self, score: float) -> str:
        if score >= 40:
            return "強烈看漲"
        elif score >= 20:
            return "看漲"
        elif score >= 5:
            return "微幅看漲"
        elif score >= -5:
            return "中性"
        elif score >= -20:
            return "微幅看跌"
        elif score >= -40:
            return "看跌"
        else:
            return "強烈看跌"

    def _calculate_confidence(self, results: list[SignalResult], total_score: float) -> float:
        scores = [r.score for r in results]
        n = len(scores)

        # 1. Direction consistency
        if total_score >= 5:
            same = sum(1 for s in scores if s > 0)
        elif total_score <= -5:
            same = sum(1 for s in scores if s < 0)
        else:
            same = sum(1 for s in scores if -4 <= s <= 4)
        direction_consistency = same / n * 100

        # 2. Strength factor
        strength = abs(total_score)

        # 3. Dispersion factor
        if len(scores) >= 2:
            std_dev = statistics.stdev(scores)
        else:
            std_dev = 0
        dispersion = max(0, 1 - std_dev / 80) * 100

        confidence = direction_consistency * 0.45 + strength * 0.30 + dispersion * 0.25
        return _clamp(confidence, 10, 95)

    def _resolve_conflicts(self, results: list[SignalResult]) -> list[SignalResult]:
        """Apply conflict resolution rules."""
        result_map = {r.name: r for r in results}

        outer = result_map.get("外盤比率")
        rsi = result_map.get("RSI")
        kd = result_map.get("KD交叉")
        macd = result_map.get("MACD OSC")
        institutional = result_map.get("籌碼面")

        # Conflict 1: Volume vs RSI overbought → attenuate RSI score only
        if outer and rsi and outer.score > 60 and rsi.score < -50:
            rsi_new = SignalResult(
                name=rsi.name, value=rsi.value, score=round(rsi.score * 0.5, 2),
                weight=rsi.weight, weighted_score=round(rsi.score * 0.5 * rsi.weight, 4),
                description=rsi.description + "（衰減：量能主導）",
                reliability=rsi.reliability,
            )
            result_map[rsi.name] = rsi_new

        # Conflict 2: KD golden cross vs MACD death cross (or vice versa)
        if kd and macd and kd.score > 40 and macd.score < -40:
            kd_new = SignalResult(
                name=kd.name, value=kd.value, score=round(kd.score * 0.6, 2),
                weight=kd.weight, weighted_score=round(kd.score * 0.6 * kd.weight, 4),
                description=kd.description + "（衰減：與MACD矛盾）",
                reliability=kd.reliability,
            )
            macd_new = SignalResult(
                name=macd.name, value=macd.value, score=round(macd.score * 0.6, 2),
                weight=macd.weight, weighted_score=round(macd.score * 0.6 * macd.weight, 4),
                description=macd.description + "（衰減：與KD矛盾）",
                reliability=macd.reliability,
            )
            result_map[kd.name] = kd_new
            result_map[macd.name] = macd_new

        if kd and macd and kd.score < -40 and macd.score > 40:
            kd_new = SignalResult(
                name=kd.name, value=kd.value, score=round(kd.score * 0.6, 2),
                weight=kd.weight, weighted_score=round(kd.score * 0.6 * kd.weight, 4),
                description=kd.description + "（衰減：與MACD矛盾）",
                reliability=kd.reliability,
            )
            macd_new = SignalResult(
                name=macd.name, value=macd.value, score=round(macd.score * 0.6, 2),
                weight=macd.weight, weighted_score=round(macd.score * 0.6 * macd.weight, 4),
                description=macd.description + "（衰減：與KD矛盾）",
                reliability=macd.reliability,
            )
            result_map[kd.name] = kd_new
            result_map[macd.name] = macd_new

        # Conflict 3: Institutional bullish vs RSI overbought
        if institutional and rsi and institutional.score > 50 and rsi.score < -40:
            # Institutional flow dominates RSI reversal signal
            rsi_r = result_map.get("RSI", rsi)
            rsi_new = SignalResult(
                name=rsi_r.name, value=rsi_r.value, score=round(rsi_r.score * 0.5, 2),
                weight=rsi_r.weight, weighted_score=round(rsi_r.score * 0.5 * rsi_r.weight, 4),
                description=rsi_r.description + "（衰減：法人力挺）",
                reliability=rsi_r.reliability,
            )
            result_map[rsi_r.name] = rsi_new

        # Rebuild list preserving original order
        return [result_map[r.name] for r in results]
