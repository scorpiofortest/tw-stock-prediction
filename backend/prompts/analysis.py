"""AI prompt templates for Taiwan stock analysis (Google Gemma / Gemini)."""

from datetime import datetime


SYSTEM_PROMPT = """你是一位專業的台灣股票分析師，擅長綜合技術面、籌碼面、基本面與即時新聞做判斷。
你會收到：
- 15 大分析訊號（技術面、籌碼面、大盤連動等，每個已計算 -100 到 +100 分數）及加權總分
- 關鍵基本面數據（PE、EPS、殖利率、52 週區間等）
- 近期 5 則該股相關新聞標題
- 預測區間

你的任務：
1. 綜合技術面、籌碼面、大盤、基本面、新聞五方面，判斷該股在指定區間的走勢方向
2. 用繁體中文輸出 150 字內的推論說明，直接切入重點，不使用 emoji
3. 明確指出哪個因素最關鍵（技術動能／籌碼動向／大盤環境／估值／新聞事件）
4. 若出現訊號衝突（例如技術面偏多但籌碼偏空，或法人買超但RSI超買），必須點出矛盾並給出權衡
5. 籌碼面判讀指引：
   - 三大法人（尤其外資、投信）連續買超 → 中長線偏多
   - 法人賣超但技術面強 → 短線或許可持有，但注意風險
   - 融資大增且股價漲 → 散戶追多，留意回檔
   - 融券大增 → 可能有軋空機會
6. 考量區間長短：
   - 短線（1日/3日）：以動能、RSI、KD、盤中買賣壓、量價結構為主
   - 中線（1週/2週）：技術面 + 籌碼面 + 大盤連動 + 新聞事件
   - 長線（1個月）：基本面估值 + 籌碼趨勢 + 產業趨勢 + 新聞催化
7. 市場狀態判讀（極重要）：
   - 若市場狀態為「週末休市」或「盤後」：你分析的數據是最後一個交易日的收盤數據，請以**前瞻視角**分析，預估下一個交易日（通常是週一）的開盤走勢
   - 週末分析重點：上週五收盤走勢、法人上週動向、國際市場（費半指數）週五表現、週末是否有重大新聞
   - 盤後分析重點：當日收盤總結 + 預估隔日走勢
   - 盤中分析：即時走勢判斷
   - 分析文字應明確反映時間情境，例如「目前為週末休市，綜合上週五收盤走勢與國際盤表現，預估週一...」
8. 如果某類資料為「無資料」，就略過該面向判斷，並註明資訊不完整

輸出規則（極度重要）：
- 直接輸出最終分析文字，不要輸出任何思考過程、草稿、問題拆解、bullet points 或中間推理步驟
- 不要輸出 "Draft 1:"、"Question:"、"Target:"、"Constraint:"、"Analysis:" 這類標記
- 不要用星號 (*)、井號 (#)、減號 (-) 開頭條列
- 全程使用繁體中文，禁止使用英文（技術指標名稱如 RSI、MACD、KD 可保留英文縮寫）
- 輸出一段完整、連貫的繁體中文摘要分析（約 150~200 字），不要只擷取片段
- 必須綜合考量全部 15 個訊號（技術面 9 個 + 籌碼面、量價、大盤、均線、波動率、時間因子各 1 個），並在分析中體現關鍵訊號的判讀
- 分析需為重新整理後的摘要，將所有面向融合成一段流暢文字，而非逐項列舉
- 在分析文字結束後，必須另起一行輸出 [SCORE:X]，X 為 -100 到 +100 的整數，代表你的綜合判斷（+100 極度看漲，-100 極度看跌，0 中性）。例如：[SCORE:35] 或 [SCORE:-20]
- 你的 SCORE 非常重要：當訊號之間互相矛盾時，系統會提高你的 SCORE 權重（最高 55%），因此你的判斷對最終結果有決定性影響。請務必深思熟慮後才給出分數。"""


ANALYSIS_USER_TEMPLATE = """以下是 {stock_name}({stock_code}) 在 {timestamp} 的綜合分析數據：

目前股價：{current_price}（漲跌幅 {change_pct}）

【九大技術訊號】
1. 外盤比率：{outer_ratio_score}分 → {outer_ratio_desc}
2. 五檔壓力：{bid_ask_score}分 → {bid_ask_desc}
3. 10筆成交：{tick_dir_score}分 → {tick_dir_desc}
4. 日內位置：{intraday_score}分 → {intraday_desc}
5. 漲跌動能：{momentum_score}分 → {momentum_desc}
6. RSI(14)：{rsi_score}分 → {rsi_desc}
7. MACD OSC：{macd_score}分 → {macd_desc}
8. KD交叉：{kd_score}分 → {kd_desc}
9. 走勢加速度：{accel_score}分 → {accel_desc}

【籌碼面與市場環境】
10. 籌碼面：{institutional_score}分 → {institutional_desc}
11. 量價結構：{volume_price_score}分 → {volume_price_desc}
12. 大盤連動：{market_corr_score}分 → {market_corr_desc}
13. 均線系統：{ma_system_score}分 → {ma_system_desc}
14. 波動率：{volatility_score}分 → {volatility_desc}
15. 時間因子：{time_factor_score}分 → {time_factor_desc}

加權總分：{weighted_total_score}（{direction}）
信心值：{confidence}%
訊號一致性：{signal_agreement}

【基本面快照】
{fundamentals_block}

【近期相關新聞】
{news_block}

【市場狀態】：{market_status}
【預測區間】：未來 {horizon_label}

請綜合以上全部 15 個訊號（技術面、籌碼面、大盤環境）及基本面與新聞，用繁體中文輸出一段完整的摘要分析（約 150~200 字），判斷該股在**未來 {horizon_label}**的走勢方向（看漲／看跌／中性），並說明核心依據。請將各面向融合成連貫文字，不要逐項條列或只取片段。分析應反映當前市場狀態（{market_status}），若為休市或盤後則以前瞻預測角度撰寫。"""


def _format_fundamentals(fundamentals: dict) -> str:
    """Format fundamentals dict into a prompt-friendly block."""
    if not fundamentals:
        return "（無基本面資料）"

    lines = []
    if fundamentals.get("pe"):
        pe_str = f"本益比(PE)：{fundamentals['pe']}"
        if fundamentals.get("forward_pe"):
            pe_str += f"（預估 PE {fundamentals['forward_pe']}）"
        lines.append(pe_str)
    if fundamentals.get("pb"):
        lines.append(f"股價淨值比(PB)：{fundamentals['pb']}")
    if fundamentals.get("eps"):
        lines.append(f"EPS(TTM)：{fundamentals['eps']}")
    if fundamentals.get("dividend_yield"):
        lines.append(f"殖利率：{fundamentals['dividend_yield']}%")
    if fundamentals.get("week_52_high") and fundamentals.get("week_52_low"):
        lines.append(
            f"52週區間：{fundamentals['week_52_low']} ~ {fundamentals['week_52_high']}"
        )
    if fundamentals.get("beta"):
        lines.append(f"Beta：{fundamentals['beta']}")
    if fundamentals.get("sector"):
        sector = fundamentals["sector"]
        industry = fundamentals.get("industry", "")
        lines.append(f"產業：{sector}{f' / {industry}' if industry else ''}")

    return "\n".join(lines) if lines else "（無基本面資料）"


def _format_news(news: list[dict]) -> str:
    """Format news list into a prompt-friendly block."""
    if not news:
        return "（暫無相關新聞）"

    lines = []
    for i, item in enumerate(news[:5], 1):
        title = item.get("title", "")
        source = item.get("source", "")
        published = item.get("published", "")

        tags = []
        if source:
            tags.append(source)
        if published:
            tags.append(published)
        prefix = f"[{' · '.join(tags)}] " if tags else ""

        lines.append(f"{i}. {prefix}{title}")

    return "\n".join(lines)


def _detect_market_status() -> str:
    """Detect current Taiwan stock market status."""
    now = datetime.now()
    weekday = now.weekday()  # 0=Mon, 4=Fri, 5=Sat, 6=Sun
    hour = now.hour
    minute = now.minute
    time_minutes = hour * 60 + minute

    if weekday >= 5:
        return "週末休市（資料為上週五收盤，下個交易日為週一）"

    # Taiwan market hours: 9:00 - 13:30
    if time_minutes < 9 * 60:
        return "盤前（尚未開盤，資料為前一交易日收盤）"
    elif time_minutes <= 13 * 60 + 30:
        return "盤中交易時段"
    else:
        if weekday == 4:  # Friday after close
            return "盤後（週五收盤，下個交易日為週一）"
        return "盤後（已收盤，資料為今日收盤）"


def build_analysis_prompt(
    stock_code: str,
    stock_name: str,
    current_price: float,
    change_pct: float,
    signals: list[dict],
    weighted_total_score: float,
    direction: str,
    confidence: float,
    signal_agreement: str,
    horizon_label: str = "1週",
    news: list[dict] = None,
    fundamentals: dict = None,
) -> str:
    """Build the user prompt from signals + news + fundamentals."""
    signal_map = {s["name"]: s for s in signals}

    def _get(name: str, key: str, default="N/A"):
        s = signal_map.get(name, {})
        return s.get(key, default)

    market_status = _detect_market_status()

    return ANALYSIS_USER_TEMPLATE.format(
        stock_code=stock_code,
        stock_name=stock_name,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        current_price=f"{current_price:.2f}",
        change_pct=f"{change_pct:+.2f}%",
        # Original 9 signals
        outer_ratio_score=_get("外盤比率", "score"),
        outer_ratio_desc=_get("外盤比率", "description"),
        bid_ask_score=_get("五檔委買委賣壓力", "score"),
        bid_ask_desc=_get("五檔委買委賣壓力", "description"),
        tick_dir_score=_get("最近10筆成交方向", "score"),
        tick_dir_desc=_get("最近10筆成交方向", "description"),
        intraday_score=_get("日內高低位置", "score"),
        intraday_desc=_get("日內高低位置", "description"),
        momentum_score=_get("即時漲跌幅動能", "score"),
        momentum_desc=_get("即時漲跌幅動能", "description"),
        rsi_score=_get("RSI", "score"),
        rsi_desc=_get("RSI", "description"),
        macd_score=_get("MACD OSC", "score"),
        macd_desc=_get("MACD OSC", "description"),
        kd_score=_get("KD交叉", "score"),
        kd_desc=_get("KD交叉", "description"),
        accel_score=_get("盤中走勢加速度", "score"),
        accel_desc=_get("盤中走勢加速度", "description"),
        # New 6 signals
        institutional_score=_get("籌碼面", "score"),
        institutional_desc=_get("籌碼面", "description"),
        volume_price_score=_get("量價結構", "score"),
        volume_price_desc=_get("量價結構", "description"),
        market_corr_score=_get("大盤連動", "score"),
        market_corr_desc=_get("大盤連動", "description"),
        ma_system_score=_get("均線系統", "score"),
        ma_system_desc=_get("均線系統", "description"),
        volatility_score=_get("波動率", "score"),
        volatility_desc=_get("波動率", "description"),
        time_factor_score=_get("時間因子", "score"),
        time_factor_desc=_get("時間因子", "description"),
        # Composite
        weighted_total_score=f"{weighted_total_score:.1f}",
        direction=direction,
        confidence=f"{confidence:.1f}",
        signal_agreement=signal_agreement,
        horizon_label=horizon_label,
        fundamentals_block=_format_fundamentals(fundamentals or {}),
        news_block=_format_news(news or []),
        market_status=market_status,
    )
