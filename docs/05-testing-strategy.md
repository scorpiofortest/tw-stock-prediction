# 05 - 測試策略與品質保證計劃

## 1. 測試策略總覽

### 1.1 測試金字塔

本專案採用經典測試金字塔架構，確保在成本與信心之間取得最佳平衡：

```
        /  E2E  \          10%  (~20 個測試案例)
       /  整合測試  \        25%  (~60 個測試案例)
      / 單元測試      \      65%  (~200 個測試案例)
     ──────────────────
```

| 層級 | 佔比 | 預估數量 | 執行時間目標 | 說明 |
|------|------|----------|-------------|------|
| 單元測試 | 65% | ~200 | < 30 秒 | 訊號計算、評分邏輯、模擬倉核心 |
| 整合測試 | 25% | ~60 | < 2 分鐘 | API 串接、數據管線、WebSocket |
| E2E 測試 | 10% | ~20 | < 5 分鐘 | 使用者完整操作流程 |

### 1.2 測試框架選型

| 層級 | 後端 (Python) | 前端 (TypeScript/React) |
|------|---------------|------------------------|
| 單元測試 | **pytest** + pytest-cov + pytest-asyncio | **Vitest** + React Testing Library |
| 整合測試 | **pytest** + httpx (AsyncClient) + pytest-mock | **Vitest** + MSW (Mock Service Worker) |
| E2E 測試 | — | **Playwright** |
| 效能測試 | **locust** / pytest-benchmark | **Lighthouse CI** |
| API 測試 | **pytest** + httpx | — |

**選型理由：**
- **pytest**：Python 生態系最成熟的測試框架，豐富的插件生態，fixture 機制強大
- **Vitest**：與 Vite 建構工具原生整合，速度極快，API 相容 Jest
- **Playwright**：跨瀏覽器支援好、穩定性高、內建等待機制優於 Cypress
- **MSW**：在 Service Worker 層攔截 HTTP 請求，不需修改應用程式碼

### 1.3 測試覆蓋率目標

| 模組 | 行覆蓋率目標 | 分支覆蓋率目標 | 優先級 |
|------|-------------|---------------|--------|
| 訊號計算模組 | ≥ 95% | ≥ 90% | P0（最高） |
| 加權評分系統 | ≥ 95% | ≥ 90% | P0 |
| 模擬倉功能 | ≥ 90% | ≥ 85% | P0 |
| 數據收集層 | ≥ 80% | ≥ 75% | P1 |
| API 路由層 | ≥ 80% | ≥ 75% | P1 |
| 前端元件 | ≥ 75% | ≥ 70% | P2 |
| 工具函式 | ≥ 90% | ≥ 85% | P1 |
| **全專案整體** | **≥ 85%** | **≥ 80%** | — |

---

## 2. 單元測試計劃

### 2.1 訊號計算模組測試

每個訊號模組測試遵循以下結構：
- **正常值測試**：驗證典型輸入的計算正確性
- **邊界值測試**：驗證極端參數下的行為
- **異常數據測試**：驗證錯誤輸入的容錯處理
- **預期輸出驗證**：確保分數落在 -100 ~ +100 範圍內

---

#### 2.1.1 外盤比率計算（Signal 1）

**功能說明：** 計算外盤成交量佔總成交量的比率，用於判斷主動買賣力道。

```python
# tests/unit/signals/test_outer_ratio.py

class TestOuterRatio:
    """外盤比率計算測試"""

    # --- 正常值測試 ---
    def test_normal_bullish(self):
        """外盤比率 70%，應回傳正面訊號"""
        # 輸入：外盤量=700, 內盤量=300
        # 預期：正值分數（約 +40 ~ +60）

    def test_normal_bearish(self):
        """外盤比率 30%，應回傳負面訊號"""
        # 輸入：外盤量=300, 內盤量=700
        # 預期：負值分數（約 -40 ~ -60）

    def test_balanced(self):
        """外盤比率 50%，應回傳中性訊號"""
        # 輸入：外盤量=500, 內盤量=500
        # 預期：接近 0 的分數

    # --- 邊界值測試 ---
    def test_all_outer(self):
        """外盤比率 100%（全部外盤）"""
        # 輸入：外盤量=1000, 內盤量=0
        # 預期：最大正值分數（接近 +100）

    def test_all_inner(self):
        """外盤比率 0%（全部內盤）"""
        # 輸入：外盤量=0, 內盤量=1000
        # 預期：最大負值分數（接近 -100）

    def test_very_small_volume(self):
        """成交量極小（1張）"""
        # 輸入：外盤量=1, 內盤量=0
        # 預期：應正常計算，但可標記低可信度

    # --- 異常數據測試 ---
    def test_zero_total_volume(self):
        """總成交量為 0"""
        # 輸入：外盤量=0, 內盤量=0
        # 預期：回傳 0 或 None，不應拋出 ZeroDivisionError

    def test_negative_volume(self):
        """負值成交量（不合法數據）"""
        # 輸入：外盤量=-100, 內盤量=500
        # 預期：拋出 ValueError 或回傳 None

    def test_none_input(self):
        """None 輸入"""
        # 預期：拋出 TypeError 或回傳預設值
```

---

#### 2.1.2 五檔壓力計算（Signal 2）

**功能說明：** 分析買賣五檔掛單量的壓力比，判斷即時供需狀態。

```python
# tests/unit/signals/test_order_book_pressure.py

class TestOrderBookPressure:
    """五檔壓力計算測試"""

    # --- 正常值測試 ---
    def test_buy_pressure_dominant(self):
        """買方掛單量遠大於賣方"""
        # 輸入：買五檔=[500,400,300,200,100], 賣五檔=[50,40,30,20,10]
        # 預期：強正面訊號

    def test_sell_pressure_dominant(self):
        """賣方掛單量遠大於買方"""
        # 輸入：買五檔=[50,40,30,20,10], 賣五檔=[500,400,300,200,100]
        # 預期：強負面訊號

    def test_balanced_pressure(self):
        """買賣掛單均衡"""
        # 輸入：買五檔=[100,100,100,100,100], 賣五檔=[100,100,100,100,100]
        # 預期：中性訊號（接近 0）

    # --- 邊界值測試 ---
    def test_extreme_buy_pressure(self):
        """極度買方偏壓（賣方幾乎無掛單）"""
        # 輸入：買五檔=[9999,9999,9999,9999,9999], 賣五檔=[1,1,1,1,1]
        # 預期：接近 +100 的分數

    def test_extreme_sell_pressure(self):
        """極度賣方偏壓"""
        # 輸入：買五檔=[1,1,1,1,1], 賣五檔=[9999,9999,9999,9999,9999]
        # 預期：接近 -100 的分數

    def test_zero_orders_both_sides(self):
        """雙邊零掛單"""
        # 輸入：買五檔=[0,0,0,0,0], 賣五檔=[0,0,0,0,0]
        # 預期：回傳 0 或 None，不應報錯

    def test_partial_empty_levels(self):
        """部分檔位無掛單（非流動性標的）"""
        # 輸入：買五檔=[100,50,0,0,0], 賣五檔=[200,0,0,0,0]
        # 預期：僅以有效檔位計算

    # --- 異常數據測試 ---
    def test_insufficient_levels(self):
        """掛單檔位不足5檔"""
        # 輸入：買五檔=[100,50], 賣五檔=[200,150,100]
        # 預期：以可用檔位計算或回傳低可信度結果

    def test_negative_order_quantity(self):
        """負數掛單量"""
        # 預期：拋出 ValueError
```

---

#### 2.1.3 成交明細方向（Signal 3）

**功能說明：** 分析最近 N 筆成交明細的買賣方向分佈。

```python
# tests/unit/signals/test_tick_direction.py

class TestTickDirection:
    """成交明細方向測試"""

    # --- 正常值測試 ---
    def test_mostly_buy_ticks(self):
        """多數成交為外盤主動買"""
        # 輸入：最近20筆中15筆為外盤成交
        # 預期：正面訊號

    def test_mostly_sell_ticks(self):
        """多數成交為內盤主動賣"""
        # 輸入：最近20筆中15筆為內盤成交
        # 預期：負面訊號

    def test_mixed_ticks(self):
        """買賣交替混合"""
        # 輸入：10筆外盤、10筆內盤
        # 預期：中性訊號

    # --- 邊界值測試 ---
    def test_all_buy_ticks(self):
        """全部為外盤成交"""
        # 輸入：20筆全部為外盤
        # 預期：最大正值分數

    def test_all_sell_ticks(self):
        """全部為內盤成交"""
        # 輸入：20筆全部為內盤
        # 預期：最大負值分數

    def test_insufficient_ticks(self):
        """成交明細不足10筆"""
        # 輸入：僅5筆成交明細
        # 預期：回傳低可信度結果或 None

    def test_single_tick(self):
        """僅一筆成交"""
        # 預期：回傳結果但標記為低可信度

    # --- 異常數據測試 ---
    def test_empty_tick_list(self):
        """空的成交明細列表"""
        # 預期：回傳 None 或 0

    def test_tick_with_missing_direction(self):
        """成交明細缺少方向欄位"""
        # 預期：略過該筆或拋出適當錯誤
```

---

#### 2.1.4 日內高低位置（Signal 4）

**功能說明：** 計算當前價格在日內最高與最低價之間的相對位置。

```python
# tests/unit/signals/test_intraday_position.py

class TestIntradayPosition:
    """日內高低位置測試"""

    # --- 正常值測試 ---
    def test_near_high(self):
        """當前價接近日內最高"""
        # 輸入：high=110, low=100, current=108
        # 預期：正面訊號（位於上方 80%）

    def test_near_low(self):
        """當前價接近日內最低"""
        # 輸入：high=110, low=100, current=102
        # 預期：負面訊號（位於下方 20%）

    def test_middle_position(self):
        """當前價位於中間"""
        # 輸入：high=110, low=100, current=105
        # 預期：中性訊號

    # --- 邊界值測試 ---
    def test_at_high(self):
        """當前價 = 日內最高價"""
        # 輸入：high=110, low=100, current=110
        # 預期：最大正值分數

    def test_at_low(self):
        """當前價 = 日內最低價"""
        # 輸入：high=110, low=100, current=100
        # 預期：最大負值分數

    def test_open_equals_high(self):
        """開盤價 = 最高價（開高走低）"""
        # 輸入：open=110, high=110, low=102, current=105
        # 預期：中偏負（高點出現在開盤）

    def test_open_equals_low(self):
        """開盤價 = 最低價（開低走高）"""
        # 輸入：open=100, high=108, low=100, current=105
        # 預期：中偏正

    def test_no_volatility(self):
        """平盤無波動（high = low = current）"""
        # 輸入：high=100, low=100, current=100
        # 預期：回傳 0，不應拋出 ZeroDivisionError

    # --- 異常數據測試 ---
    def test_current_above_high(self):
        """當前價超過最高價（數據延遲導致）"""
        # 輸入：high=110, low=100, current=112
        # 預期：截斷至 +100 或更新 high

    def test_current_below_low(self):
        """當前價低於最低價"""
        # 預期：截斷至 -100 或更新 low
```

---

#### 2.1.5 漲跌幅動能（Signal 5）

**功能說明：** 計算當前漲跌幅並轉換為動能訊號。

```python
# tests/unit/signals/test_price_momentum.py

class TestPriceMomentum:
    """漲跌幅動能測試"""

    # --- 正常值測試 ---
    def test_moderate_gain(self):
        """溫和上漲 +3%"""
        # 輸入：prev_close=100, current=103
        # 預期：正面訊號

    def test_moderate_loss(self):
        """溫和下跌 -3%"""
        # 輸入：prev_close=100, current=97
        # 預期：負面訊號

    def test_flat(self):
        """平盤 ±0%"""
        # 輸入：prev_close=100, current=100
        # 預期：0

    # --- 邊界值測試 ---
    def test_limit_up(self):
        """漲停 +10%"""
        # 輸入：prev_close=100, current=110
        # 預期：最大正值分數（+100）

    def test_limit_down(self):
        """跌停 -10%"""
        # 輸入：prev_close=100, current=90
        # 預期：最大負值分數（-100）

    def test_near_limit_up(self):
        """接近漲停 +9.5%"""
        # 預期：高正值但非滿分

    def test_near_limit_down(self):
        """接近跌停 -9.5%"""
        # 預期：高負值但非滿分

    def test_tiny_change(self):
        """微幅變動 +0.01%"""
        # 預期：接近 0 的分數

    # --- 異常數據測試 ---
    def test_zero_prev_close(self):
        """前日收盤價為 0"""
        # 預期：處理 ZeroDivisionError

    def test_negative_price(self):
        """負價格（不合法）"""
        # 預期：拋出 ValueError
```

---

#### 2.1.6 RSI 計算（Signal 6）

**功能說明：** 計算相對強弱指標 (RSI)，用於判斷超買超賣狀態。

```python
# tests/unit/signals/test_rsi.py

class TestRSI:
    """RSI 計算測試"""

    # --- 正常值測試 ---
    def test_rsi_calculation_accuracy(self):
        """用已知數據驗證 RSI 計算結果"""
        # 輸入：14期收盤價序列（已知答案）
        # 預期：計算值與已知 RSI 值誤差 < 0.01

    def test_overbought_signal(self):
        """RSI > 80 超買區"""
        # 預期：負面訊號（可能反轉下跌）

    def test_oversold_signal(self):
        """RSI < 20 超賣區"""
        # 預期：正面訊號（可能反轉上漲）

    def test_neutral_rsi(self):
        """RSI 在 40~60 中性區"""
        # 預期：中性訊號

    # --- 邊界值測試 ---
    def test_overbought_reversal(self):
        """RSI 從 85 跌破 80（超買反轉訊號）"""
        # 預期：強負面訊號

    def test_oversold_reversal(self):
        """RSI 從 15 突破 20（超賣反轉訊號）"""
        # 預期：強正面訊號

    def test_rsi_at_50(self):
        """RSI 剛好 50"""
        # 預期：完全中性（分數 = 0）

    def test_rsi_at_0(self):
        """RSI = 0（連續下跌）"""
        # 預期：極端超賣訊號

    def test_rsi_at_100(self):
        """RSI = 100（連續上漲）"""
        # 預期：極端超買訊號

    # --- 異常數據測試 ---
    def test_insufficient_data(self):
        """數據不足14期"""
        # 輸入：僅5筆收盤價
        # 預期：回傳 None 或使用可用數據計算並標記低可信度

    def test_all_same_prices(self):
        """所有價格相同（無漲跌）"""
        # 預期：RSI = 50 或 None（avg_gain = avg_loss = 0）

    def test_single_data_point(self):
        """僅一筆數據"""
        # 預期：回傳 None
```

---

#### 2.1.7 MACD OSC（Signal 7）

**功能說明：** 計算 MACD 柱狀體 (OSC/Histogram)，判斷趨勢動能。

```python
# tests/unit/signals/test_macd_osc.py

class TestMACDOsc:
    """MACD 柱狀體測試"""

    # --- 正常值測試 ---
    def test_positive_histogram(self):
        """MACD 柱狀體為正"""
        # 預期：正面訊號

    def test_negative_histogram(self):
        """MACD 柱狀體為負"""
        # 預期：負面訊號

    def test_macd_calculation_accuracy(self):
        """用已知數據驗證 MACD 計算"""
        # 輸入：已知收盤價序列
        # 預期：EMA12, EMA26, Signal Line, Histogram 皆正確

    # --- 邊界值測試 ---
    def test_positive_to_negative_cross(self):
        """MACD 柱狀體正轉負（死亡交叉訊號）"""
        # 輸入：前一期 OSC=+0.5, 當期 OSC=-0.3
        # 預期：強負面訊號

    def test_negative_to_positive_cross(self):
        """MACD 柱狀體負轉正（黃金交叉訊號）"""
        # 輸入：前一期 OSC=-0.5, 當期 OSC=+0.3
        # 預期：強正面訊號

    def test_zero_histogram(self):
        """MACD 柱狀體 = 0（MACD 線與信號線重合）"""
        # 預期：中性訊號，可能即將交叉

    def test_expanding_positive(self):
        """正值柱狀體持續擴大"""
        # 預期：趨勢增強的正面訊號

    def test_contracting_positive(self):
        """正值柱狀體持續縮小"""
        # 預期：趨勢減弱的警告訊號

    # --- 異常數據測試 ---
    def test_insufficient_data_for_ema26(self):
        """數據不足26期，無法計算 EMA26"""
        # 預期：回傳 None

    def test_insufficient_data_for_signal(self):
        """數據不足35期（26+9），無法計算信號線"""
        # 預期：回傳 None 或僅回傳 MACD 線
```

---

#### 2.1.8 KD 交叉（Signal 8）

**功能說明：** 計算隨機指標 (KD)，偵測 K 線與 D 線的交叉。

```python
# tests/unit/signals/test_kd_cross.py

class TestKDCross:
    """KD 交叉測試"""

    # --- 正常值測試 ---
    def test_golden_cross(self):
        """黃金交叉：K 線由下往上穿越 D 線"""
        # 輸入：前期 K=30 < D=40, 當期 K=45 > D=40
        # 預期：強正面訊號

    def test_death_cross(self):
        """死亡交叉：K 線由上往下穿越 D 線"""
        # 輸入：前期 K=70 > D=60, 當期 K=55 < D=60
        # 預期：強負面訊號

    def test_k_above_d_no_cross(self):
        """K > D 但無交叉（持續看漲）"""
        # 預期：中偏正訊號

    def test_k_below_d_no_cross(self):
        """K < D 但無交叉（持續看跌）"""
        # 預期：中偏負訊號

    # --- 邊界值測試 ---
    def test_golden_cross_in_oversold(self):
        """超賣區黃金交叉（K, D < 20）"""
        # 預期：最強正面訊號（低位黃金交叉）

    def test_death_cross_in_overbought(self):
        """超買區死亡交叉（K, D > 80）"""
        # 預期：最強負面訊號（高位死亡交叉）

    def test_kd_entangled(self):
        """KD 糾結（K ≈ D，反覆交叉）"""
        # 輸入：K 與 D 差距 < 2
        # 預期：中性或低可信度訊號

    def test_k_equals_d(self):
        """K = D 完全重合"""
        # 預期：中性，不算交叉

    def test_kd_at_extreme_high(self):
        """K = D = 99（極端超買）"""
        # 預期：強烈超買警告

    def test_kd_at_extreme_low(self):
        """K = D = 1（極端超賣）"""
        # 預期：強烈超賣訊號

    # --- 異常數據測試 ---
    def test_insufficient_data(self):
        """數據不足9期"""
        # 預期：回傳 None

    def test_kd_out_of_range(self):
        """KD 值超出 0~100 範圍"""
        # 預期：截斷或拋出 ValueError
```

---

#### 2.1.9 走勢加速度（Signal 9）

**功能說明：** 計算價格變化的加速度（二階導數），判斷走勢是否在加速或減速。

```python
# tests/unit/signals/test_trend_acceleration.py

class TestTrendAcceleration:
    """走勢加速度測試"""

    # --- 正常值測試 ---
    def test_accelerating_up(self):
        """加速上漲（急拉）"""
        # 輸入：價格序列呈加速上升
        # 預期：強正面訊號

    def test_accelerating_down(self):
        """加速下跌（急殺）"""
        # 輸入：價格序列呈加速下降
        # 預期：強負面訊號

    def test_decelerating_up(self):
        """上漲減速"""
        # 輸入：價格上漲但漲幅遞減
        # 預期：偏弱正面或即將反轉

    def test_decelerating_down(self):
        """下跌減速"""
        # 輸入：價格下跌但跌幅遞減
        # 預期：偏弱負面或即將反轉

    # --- 邊界值測試 ---
    def test_sharp_rally(self):
        """急拉（短時間大幅上漲）"""
        # 輸入：5秒內漲幅 > 2%
        # 預期：最大正值分數

    def test_sharp_drop(self):
        """急殺（短時間大幅下跌）"""
        # 輸入：5秒內跌幅 > 2%
        # 預期：最大負值分數

    def test_consolidation(self):
        """盤整（價格幾乎不動）"""
        # 輸入：價格在 ±0.1% 範圍內震盪
        # 預期：接近 0 的分數

    def test_constant_speed_up(self):
        """等速上漲（加速度 = 0）"""
        # 輸入：每期漲幅相同
        # 預期：中性加速度訊號

    # --- 異常數據測試 ---
    def test_insufficient_data_points(self):
        """數據點不足以計算加速度"""
        # 預期：回傳 None

    def test_single_price_point(self):
        """僅一個價格數據"""
        # 預期：回傳 None

    def test_identical_prices(self):
        """所有價格完全相同"""
        # 預期：加速度 = 0
```

---

### 2.2 加權評分系統測試

```python
# tests/unit/test_weighted_scoring.py

class TestWeightedScoring:
    """加權評分系統測試"""

    # --- 權重驗證 ---
    def test_weights_sum_to_100(self):
        """所有訊號權重加總必須等於 100%"""
        weights = get_signal_weights()
        assert abs(sum(weights.values()) - 1.0) < 1e-9

    def test_all_signals_have_weights(self):
        """9大訊號皆有對應權重"""
        weights = get_signal_weights()
        assert len(weights) == 9

    def test_no_negative_weights(self):
        """權重不得為負值"""
        weights = get_signal_weights()
        assert all(w >= 0 for w in weights.values())

    # --- 極端情況 ---
    def test_all_bullish_signals(self):
        """全部訊號看漲（+100）"""
        signals = {f"signal_{i}": 100 for i in range(1, 10)}
        score = calculate_weighted_score(signals)
        assert score == 100

    def test_all_bearish_signals(self):
        """全部訊號看跌（-100）"""
        signals = {f"signal_{i}": -100 for i in range(1, 10)}
        score = calculate_weighted_score(signals)
        assert score == -100

    def test_contradicting_signals(self):
        """訊號矛盾（部分看漲、部分看跌）"""
        signals = {
            "signal_1": 100, "signal_2": -100, "signal_3": 100,
            "signal_4": -100, "signal_5": 50, "signal_6": -50,
            "signal_7": 0, "signal_8": 80, "signal_9": -80,
        }
        score = calculate_weighted_score(signals)
        assert -100 <= score <= 100

    def test_all_neutral_signals(self):
        """全部訊號中性（0）"""
        signals = {f"signal_{i}": 0 for i in range(1, 10)}
        score = calculate_weighted_score(signals)
        assert score == 0

    # --- 分數範圍驗證 ---
    def test_score_within_range(self):
        """任何輸入組合，分數必須在 -100 ~ +100"""
        import random
        for _ in range(1000):
            signals = {f"signal_{i}": random.uniform(-100, 100) for i in range(1, 10)}
            score = calculate_weighted_score(signals)
            assert -100 <= score <= 100

    # --- 缺失訊號處理 ---
    def test_partial_signals(self):
        """部分訊號缺失（回傳 None）"""
        signals = {
            "signal_1": 50, "signal_2": None, "signal_3": 30,
            "signal_4": None, "signal_5": -20, "signal_6": 60,
            "signal_7": None, "signal_8": -40, "signal_9": 10,
        }
        score = calculate_weighted_score(signals)
        # 預期：以可用訊號的權重重新正規化後計算
        assert -100 <= score <= 100

    def test_all_signals_none(self):
        """全部訊號缺失"""
        signals = {f"signal_{i}": None for i in range(1, 10)}
        score = calculate_weighted_score(signals)
        assert score is None or score == 0

    # --- 加權邏輯正確性 ---
    def test_high_weight_signal_dominates(self):
        """高權重訊號對結果影響更大"""
        # 只有最高權重的訊號為 +100，其餘為 0
        # 預期：正面分數，且數值等於該訊號的權重 * 100
```

---

### 2.3 模擬倉功能測試

```python
# tests/unit/test_paper_trading.py

class TestPaperTradingBuy:
    """模擬倉買入邏輯測試"""

    def test_buy_full_lots(self):
        """整張買入（1000股）"""
        # 輸入：資金=1,000,000, 價格=50, 數量=1張
        # 預期：扣除 50,000 + 手續費 71.25 (50000*0.1425%)
        # 持倉增加 1000 股

    def test_buy_odd_lots(self):
        """零股買入"""
        # 輸入：資金=100,000, 價格=500, 數量=50股
        # 預期：扣除 25,000 + 手續費 35.63

    def test_buy_insufficient_balance(self):
        """餘額不足"""
        # 輸入：資金=10,000, 價格=500, 數量=1張
        # 預期：交易失敗，餘額不變

    def test_buy_exact_balance(self):
        """餘額剛好足夠（含手續費）"""
        # 預期：交易成功，餘額接近 0

    def test_buy_zero_quantity(self):
        """買入數量為 0"""
        # 預期：交易失敗

    def test_buy_negative_quantity(self):
        """買入負數量"""
        # 預期：拋出 ValueError

    def test_commission_calculation(self):
        """手續費計算（0.1425%，折讓後若有）"""
        # 輸入：買入金額=100,000
        # 預期：手續費 = 100,000 * 0.001425 = 142.5（取整規則視實作而定）

    def test_commission_minimum(self):
        """手續費最低收取（若有最低門檻，通常為 20 元）"""
        # 輸入：買入金額=1,000
        # 預期：手續費 = max(1.425, 20) = 20


class TestPaperTradingSell:
    """模擬倉賣出邏輯測試"""

    def test_sell_all_position(self):
        """賣出全部持倉"""
        # 輸入：持有 1000 股，賣出 1000 股，價格=55
        # 預期：
        #   賣出金額 = 55,000
        #   手續費 = 55,000 * 0.001425 = 78.38
        #   交易稅 = 55,000 * 0.003 = 165
        #   實收 = 55,000 - 78.38 - 165 = 54,756.62

    def test_sell_partial_position(self):
        """賣出部分持倉"""
        # 輸入：持有 2000 股，賣出 500 股
        # 預期：持倉減少至 1500 股

    def test_sell_more_than_holding(self):
        """賣出超過持倉"""
        # 輸入：持有 500 股，賣出 1000 股
        # 預期：交易失敗

    def test_sell_with_no_position(self):
        """無持倉賣出"""
        # 預期：交易失敗

    def test_sell_zero_quantity(self):
        """賣出數量為 0"""
        # 預期：交易失敗

    def test_transaction_tax_calculation(self):
        """交易稅計算（0.3%）"""
        # 輸入：賣出金額=100,000
        # 預期：交易稅 = 100,000 * 0.003 = 300

    def test_sell_tax_only_on_sell(self):
        """交易稅僅在賣出時收取"""
        # 驗證買入時不收交易稅


class TestPaperTradingPnL:
    """模擬倉損益計算測試"""

    def test_profit_calculation(self):
        """獲利計算（含手續費 + 交易稅）"""
        # 買入：100股 * 50元 = 5,000 + 手續費 7.13
        # 賣出：100股 * 55元 = 5,500 - 手續費 7.84 - 交易稅 16.5
        # 淨利 = 5,500 - 5,000 - 7.13 - 7.84 - 16.5 = 468.53
        # 報酬率 = 468.53 / 5,007.13 ≈ 9.36%

    def test_loss_calculation(self):
        """虧損計算"""
        # 買入：100股 * 50元，賣出：100股 * 45元
        # 預期：負報酬率

    def test_breakeven_price(self):
        """計算打平價格（含交易成本）"""
        # 買入成本 + 雙向手續費 + 賣出交易稅 = 0
        # 驗證打平價格計算正確

    def test_unrealized_pnl(self):
        """未實現損益計算"""
        # 輸入：持有 1000 股，成本 50，現價 55
        # 預期：未實現獲利 = (55-50)*1000 - 預估賣出成本

    def test_total_asset_calculation(self):
        """總資產計算"""
        # 總資產 = 現金餘額 + Σ(持股數量 * 現價)
        # 輸入：現金=500,000, 持股A=1000股*50元, 持股B=500股*100元
        # 預期：500,000 + 50,000 + 50,000 = 600,000

    def test_multiple_positions(self):
        """多檔持股損益計算"""
        # 預期：各檔獨立計算損益，總計正確

    def test_average_cost_after_multiple_buys(self):
        """多次買入後平均成本計算"""
        # 第一次：100股 * 50元
        # 第二次：200股 * 55元
        # 預期：平均成本 = (5000+11000)/(100+200) ≈ 53.33
```

---

## 3. 整合測試計劃

### 3.1 數據收集 → 訊號計算 → 評分 → 推送 完整管線

```python
# tests/integration/test_data_pipeline.py

class TestDataPipeline:
    """端到端數據管線測試"""

    async def test_full_pipeline(self):
        """完整管線：原始數據 → 9 大訊號 → 加權分數 → 推送"""
        # 1. 注入模擬市場數據（fixture）
        # 2. 觸發數據收集模組
        # 3. 驗證9大訊號皆有計算結果
        # 4. 驗證加權分數在合理範圍
        # 5. 驗證 WebSocket 有推送結果

    async def test_pipeline_with_partial_data(self):
        """部分數據缺失時管線行為"""
        # 輸入：缺少五檔數據
        # 預期：跳過該訊號，以其餘訊號計算分數

    async def test_pipeline_data_freshness(self):
        """數據新鮮度檢查"""
        # 輸入：注入 5 分鐘前的數據
        # 預期：標記為過期或觸發重新獲取

    async def test_pipeline_concurrent_stocks(self):
        """同時處理多檔股票"""
        # 輸入：同時注入 2330, 2317, 2454 的數據
        # 預期：各檔獨立計算，結果互不干擾
```

### 3.2 Groq API 整合測試（Mock 方案）

```python
# tests/integration/test_groq_integration.py

class TestGroqAPIIntegration:
    """Groq API 整合測試（使用 Mock）"""

    # --- Mock 策略 ---
    # 使用 pytest-mock 或 responses/respx 攔截 HTTP 請求
    # 不直接呼叫 Groq API，避免：
    #   1. API 費用
    #   2. 速率限制
    #   3. 網路不穩定導致測試失敗

    @pytest.fixture
    def mock_groq_response(self):
        """模擬 Groq API 回應"""
        return {
            "choices": [{
                "message": {
                    "content": "根據分析，2330台積電目前呈現偏多格局..."
                }
            }],
            "usage": {"total_tokens": 500}
        }

    async def test_groq_api_call_format(self):
        """驗證發送給 Groq 的請求格式正確"""
        # 驗證 prompt 包含所有9大訊號數據
        # 驗證 model 參數正確
        # 驗證 temperature 設置合理

    async def test_groq_response_parsing(self):
        """驗證 Groq 回應的解析"""
        # 輸入：Mock 回應
        # 預期：正確提取 AI 分析文字

    async def test_groq_api_timeout(self):
        """Groq API 超時處理"""
        # 模擬超時（10秒無回應）
        # 預期：優雅降級，回傳「AI 分析暫不可用」

    async def test_groq_api_rate_limit(self):
        """Groq API 速率限制處理"""
        # 模擬 429 Too Many Requests
        # 預期：指數退避重試，最多3次

    async def test_groq_api_error_response(self):
        """Groq API 錯誤回應"""
        # 模擬 500 Internal Server Error
        # 預期：記錄錯誤，回傳 fallback 結果

    async def test_groq_toggle_off(self):
        """AI 推論關閉時不呼叫 API"""
        # 設定 ai_inference=False
        # 預期：不發送 API 請求，僅回傳訊號數據
```

### 3.3 62 秒驗證機制整合測試

```python
# tests/integration/test_verification_cycle.py

class TestVerificationCycle:
    """62秒驗證機制測試"""

    async def test_normal_verification_cycle(self):
        """正常的62秒驗證週期"""
        # 1. T=0s: 發出預測
        # 2. T=62s: 取得實際價格
        # 3. 比對預測方向與實際方向
        # 4. 計算預測準確率

    async def test_verification_timing(self):
        """驗證時間間隔準確性"""
        # 使用 freezegun 或 time mock
        # 預期：驗證在 60~65 秒內觸發（允許小誤差）

    async def test_verification_during_market_close(self):
        """收盤後的驗證行為"""
        # 預期：不執行驗證或使用最後收盤價

    async def test_verification_result_storage(self):
        """驗證結果的儲存"""
        # 預期：結果正確寫入資料庫/檔案

    async def test_consecutive_verifications(self):
        """連續多次驗證的累積統計"""
        # 模擬10次預測-驗證循環
        # 驗證準確率統計正確

    async def test_verification_with_price_unchanged(self):
        """驗證時價格不變"""
        # 預期：判定為預測中性/未觸發
```

### 3.4 WebSocket 推送整合測試

```python
# tests/integration/test_websocket.py

class TestWebSocketPush:
    """WebSocket 推送測試"""

    async def test_client_connection(self):
        """客戶端連線"""
        # 預期：連線成功，收到歡迎訊息

    async def test_signal_update_broadcast(self):
        """訊號更新推送"""
        # 觸發訊號計算
        # 預期：所有連線的客戶端收到更新

    async def test_subscription_to_specific_stock(self):
        """訂閱特定股票"""
        # 客戶端訂閱 2330
        # 預期：只收到 2330 的更新

    async def test_multiple_client_connections(self):
        """多客戶端同時連線"""
        # 10 個客戶端同時連線
        # 預期：所有客戶端都收到推送

    async def test_client_disconnection_handling(self):
        """客戶端斷線處理"""
        # 客戶端異常斷線
        # 預期：伺服器不報錯，清理連線資源

    async def test_reconnection(self):
        """重連機制"""
        # 客戶端斷線後重連
        # 預期：重連成功，恢復訂閱

    async def test_message_format(self):
        """推送訊息格式驗證"""
        # 預期：JSON 格式，包含 stock_id, signals, score, timestamp
```

---

## 4. E2E 測試計劃

### 4.1 測試框架配置

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30000,
  retries: 2,
  use: {
    baseURL: 'http://localhost:3000',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
    { name: 'firefox', use: { browserName: 'firefox' } },
    { name: 'webkit', use: { browserName: 'webkit' } },
  ],
});
```

### 4.2 使用者完整操作流程

```typescript
// tests/e2e/stock-analysis.spec.ts

test.describe('股票分析完整流程', () => {

  test('輸入股票代碼 → 看到分析結果', async ({ page }) => {
    // 1. 開啟首頁
    await page.goto('/');

    // 2. 輸入股票代碼
    await page.fill('[data-testid="stock-input"]', '2330');
    await page.click('[data-testid="analyze-btn"]');

    // 3. 等待載入完成
    await page.waitForSelector('[data-testid="signal-panel"]');

    // 4. 驗證9大訊號皆有顯示
    for (let i = 1; i <= 9; i++) {
      await expect(page.locator(`[data-testid="signal-${i}"]`)).toBeVisible();
    }

    // 5. 驗證加權分數顯示
    await expect(page.locator('[data-testid="weighted-score"]')).toBeVisible();

    // 6. 驗證分數在合理範圍
    const scoreText = await page.locator('[data-testid="weighted-score"]').textContent();
    const score = parseFloat(scoreText!);
    expect(score).toBeGreaterThanOrEqual(-100);
    expect(score).toBeLessThanOrEqual(100);
  });

  test('無效股票代碼顯示錯誤', async ({ page }) => {
    await page.goto('/');
    await page.fill('[data-testid="stock-input"]', '9999');
    await page.click('[data-testid="analyze-btn"]');
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
  });

  test('空白股票代碼不送出', async ({ page }) => {
    await page.goto('/');
    await page.click('[data-testid="analyze-btn"]');
    await expect(page.locator('[data-testid="stock-input"]')).toHaveAttribute('aria-invalid', 'true');
  });
});
```

### 4.3 模擬倉操作流程

```typescript
// tests/e2e/paper-trading.spec.ts

test.describe('模擬倉操作', () => {

  test('買入股票流程', async ({ page }) => {
    await page.goto('/paper-trading');
    // 1. 選擇股票
    await page.fill('[data-testid="trade-stock-input"]', '2330');
    // 2. 輸入數量
    await page.fill('[data-testid="trade-quantity"]', '1000');
    // 3. 選擇買入
    await page.click('[data-testid="buy-btn"]');
    // 4. 確認交易
    await page.click('[data-testid="confirm-trade-btn"]');
    // 5. 驗證持倉顯示
    await expect(page.locator('[data-testid="position-2330"]')).toBeVisible();
    // 6. 驗證餘額減少
    const balance = await page.locator('[data-testid="cash-balance"]').textContent();
    expect(parseFloat(balance!.replace(/,/g, ''))).toBeLessThan(1000000);
  });

  test('賣出股票流程', async ({ page }) => {
    // 前置：先買入持倉
    // 然後執行賣出流程
    // 驗證持倉減少、餘額增加
  });

  test('餘額不足時顯示警告', async ({ page }) => {
    // 嘗試買入超過餘額的數量
    // 預期：顯示「餘額不足」提示
  });
});
```

### 4.4 AI 推論開關功能

```typescript
// tests/e2e/ai-toggle.spec.ts

test.describe('AI 推論開關', () => {

  test('開啟 AI 推論顯示 AI 分析', async ({ page }) => {
    await page.goto('/');
    await page.fill('[data-testid="stock-input"]', '2330');
    await page.click('[data-testid="ai-toggle"]'); // 開啟
    await page.click('[data-testid="analyze-btn"]');
    await expect(page.locator('[data-testid="ai-analysis"]')).toBeVisible();
  });

  test('關閉 AI 推論只顯示訊號數據', async ({ page }) => {
    await page.goto('/');
    await page.fill('[data-testid="stock-input"]', '2330');
    // 確認 AI toggle 關閉
    await page.click('[data-testid="analyze-btn"]');
    await expect(page.locator('[data-testid="ai-analysis"]')).not.toBeVisible();
    await expect(page.locator('[data-testid="signal-panel"]')).toBeVisible();
  });

  test('切換 AI 開關不影響既有數據', async ({ page }) => {
    // 先分析一次，然後切換開關
    // 預期：訊號數據保持不變
  });
});
```

### 4.5 響應式佈局測試

```typescript
// tests/e2e/responsive.spec.ts

test.describe('響應式佈局', () => {

  const viewports = [
    { name: 'Mobile', width: 375, height: 812 },
    { name: 'Tablet', width: 768, height: 1024 },
    { name: 'Desktop', width: 1440, height: 900 },
  ];

  for (const vp of viewports) {
    test(`${vp.name} 佈局正確顯示`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto('/');

      // 驗證主要元素可見
      await expect(page.locator('[data-testid="stock-input"]')).toBeVisible();
      await expect(page.locator('[data-testid="analyze-btn"]')).toBeVisible();

      // 驗證無水平捲動
      const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
      const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
      expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 1);
    });
  }

  test('Mobile 導航選單展開/收合', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    await page.click('[data-testid="mobile-menu-btn"]');
    await expect(page.locator('[data-testid="nav-menu"]')).toBeVisible();
  });
});
```

---

## 5. 效能測試計劃

### 5.1 效能指標與目標

| 指標 | 目標值 | 測量方法 |
|------|--------|----------|
| 單一訊號計算延遲 | < 10 ms | pytest-benchmark |
| 9大訊號完整計算 | < 100 ms | pytest-benchmark |
| WebSocket 推送延遲 | < 50 ms | 客戶端時間戳比對 |
| API 回應時間 (P95) | < 200 ms | locust / k6 |
| 首頁載入時間 (LCP) | < 2.5 s | Lighthouse CI |
| 首次互動延遲 (FID) | < 100 ms | Lighthouse CI |
| 記憶體使用量 | < 512 MB | psutil 監控 |

### 5.2 訊號計算效能測試

```python
# tests/performance/test_signal_performance.py

class TestSignalPerformance:

    @pytest.mark.benchmark
    def test_single_signal_latency(self, benchmark):
        """單一訊號計算延遲 < 10ms"""
        result = benchmark(calculate_outer_ratio, sample_data)
        assert benchmark.stats['mean'] < 0.01  # 10ms

    @pytest.mark.benchmark
    def test_all_signals_latency(self, benchmark):
        """9大訊號完整計算 < 100ms"""
        result = benchmark(calculate_all_signals, sample_data)
        assert benchmark.stats['mean'] < 0.1  # 100ms

    @pytest.mark.benchmark
    def test_weighted_score_latency(self, benchmark):
        """加權評分計算 < 5ms"""
        result = benchmark(calculate_weighted_score, sample_signals)
        assert benchmark.stats['mean'] < 0.005
```

### 5.3 並發連線測試

```python
# tests/performance/locustfile.py

from locust import HttpUser, task, between

class StockAnalysisUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def get_stock_analysis(self):
        """取得股票分析結果"""
        self.client.get("/api/analysis/2330")

    @task(1)
    def get_paper_trading_portfolio(self):
        """取得模擬倉投資組合"""
        self.client.get("/api/portfolio")

    @task(1)
    def submit_trade(self):
        """提交模擬交易"""
        self.client.post("/api/trade", json={
            "stock_id": "2330",
            "action": "buy",
            "quantity": 1000
        })
```

**並發測試場景：**

| 場景 | 並發數 | 持續時間 | 通過標準 |
|------|--------|----------|----------|
| 正常負載 | 10 users | 5 min | P95 < 200ms, 0% error |
| 高峰負載 | 50 users | 5 min | P95 < 500ms, < 1% error |
| 壓力測試 | 100 users | 10 min | P95 < 1s, < 5% error |
| 極限測試 | 200 users | 5 min | 識別系統上限 |

### 5.4 WebSocket 並發測試

```python
# tests/performance/test_websocket_load.py

async def test_websocket_concurrent_connections():
    """測試 WebSocket 並發連線"""
    NUM_CLIENTS = 100
    clients = []

    for i in range(NUM_CLIENTS):
        ws = await websockets.connect("ws://localhost:8000/ws")
        await ws.send(json.dumps({"subscribe": "2330"}))
        clients.append(ws)

    # 觸發一次訊號更新
    trigger_signal_update("2330")

    # 驗證所有客戶端都收到推送
    for ws in clients:
        msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
        data = json.loads(msg)
        assert "score" in data

    # 清理
    for ws in clients:
        await ws.close()
```

### 5.5 資料庫查詢效能

```python
# tests/performance/test_db_performance.py

class TestDBPerformance:

    @pytest.mark.benchmark
    def test_latest_signal_query(self, benchmark):
        """查詢最新訊號數據 < 10ms"""
        result = benchmark(db.get_latest_signals, "2330")
        assert benchmark.stats['mean'] < 0.01

    @pytest.mark.benchmark
    def test_historical_data_query(self, benchmark):
        """查詢30天歷史數據 < 50ms"""
        result = benchmark(db.get_history, "2330", days=30)
        assert benchmark.stats['mean'] < 0.05

    @pytest.mark.benchmark
    def test_portfolio_query(self, benchmark):
        """查詢投資組合 < 20ms"""
        result = benchmark(db.get_portfolio, user_id="test")
        assert benchmark.stats['mean'] < 0.02
```

---

## 6. 數據驗證測試

### 6.1 模擬市場數據的測試數據集設計

#### 數據集結構

```
tests/fixtures/
├── market_data/
│   ├── bullish_scenario.json      # 多頭行情數據
│   ├── bearish_scenario.json      # 空頭行情數據
│   ├── consolidation.json         # 盤整行情數據
│   ├── limit_up.json              # 漲停板數據
│   ├── limit_down.json            # 跌停板數據
│   ├── opening_auction.json       # 開盤競價數據
│   ├── closing_auction.json       # 收盤競價數據
│   └── low_liquidity.json         # 低流動性數據
├── historical/
│   ├── tsmc_2330_2025Q1.json      # 台積電2025Q1歷史數據
│   ├── hon_hai_2317_2025Q1.json   # 鴻海2025Q1歷史數據
│   └── mediatek_2454_2025Q1.json  # 聯發科2025Q1歷史數據
└── edge_cases/
    ├── market_open_moment.json    # 開盤瞬間
    ├── market_close_moment.json   # 收盤瞬間
    ├── ex_dividend_day.json       # 除息日
    └── circuit_breaker.json       # 暫停交易
```

#### 數據集欄位定義

```json
{
  "stock_id": "2330",
  "timestamp": "2025-03-15T09:30:00+08:00",
  "price": {
    "open": 880,
    "high": 895,
    "low": 875,
    "close": 890,
    "prev_close": 878
  },
  "volume": {
    "total": 25000,
    "outer": 14000,
    "inner": 11000
  },
  "order_book": {
    "bid": [
      {"price": 889, "qty": 150},
      {"price": 888, "qty": 200},
      {"price": 887, "qty": 180},
      {"price": 886, "qty": 120},
      {"price": 885, "qty": 100}
    ],
    "ask": [
      {"price": 890, "qty": 130},
      {"price": 891, "qty": 170},
      {"price": 892, "qty": 210},
      {"price": 893, "qty": 160},
      {"price": 894, "qty": 140}
    ]
  },
  "ticks": [
    {"time": "09:30:00", "price": 890, "qty": 5, "direction": "buy"},
    {"time": "09:30:01", "price": 889, "qty": 3, "direction": "sell"}
  ],
  "technical": {
    "rsi_14": 62.5,
    "macd": {"dif": 2.5, "macd": 1.8, "osc": 0.7},
    "kd": {"k": 72.3, "d": 65.8}
  }
}
```

### 6.2 歷史回測驗證方案

#### 回測流程

```
歷史數據 ──→ 訊號計算模組 ──→ 加權評分 ──→ 預測方向 ──→ 比對實際走勢
                                                              │
                                                              ▼
                                                        準確率統計
```

#### 回測程式設計

```python
# tests/backtest/test_prediction_accuracy.py

class TestBacktestAccuracy:

    @pytest.fixture
    def historical_data(self):
        """載入歷史回測數據"""
        return load_fixture("historical/tsmc_2330_2025Q1.json")

    def test_direction_accuracy(self, historical_data):
        """方向預測準確率"""
        correct = 0
        total = 0

        for i in range(len(historical_data) - 62):  # 62秒後驗證
            t0_data = historical_data[i]
            t62_data = historical_data[i + 62]

            prediction = calculate_all_signals(t0_data)
            predicted_direction = "up" if prediction["score"] > 0 else "down"

            actual_direction = "up" if t62_data["price"] > t0_data["price"] else "down"

            if predicted_direction == actual_direction:
                correct += 1
            total += 1

        accuracy = correct / total
        # 預測準確率應顯著高於隨機（50%）
        assert accuracy > 0.52, f"準確率 {accuracy:.2%} 未達基準"

    def test_strong_signal_accuracy(self, historical_data):
        """強訊號的預測準確率應更高"""
        # 僅驗證 |score| > 50 的預測
        # 預期：強訊號準確率 > 55%

    def test_accuracy_by_market_condition(self, historical_data):
        """不同行情下的準確率"""
        # 分別統計趨勢行情 vs 盤整行情的準確率
        # 預期：趨勢行情準確率更高
```

### 6.3 預測準確率的統計檢驗方法

```python
# tests/backtest/test_statistical_validation.py

from scipy import stats

class TestStatisticalValidation:

    def test_prediction_better_than_random(self):
        """二項檢定：預測是否顯著優於隨機"""
        # H0: p = 0.5（預測等同隨機）
        # H1: p > 0.5（預測優於隨機）
        n_trials = 1000
        n_correct = 540  # 從回測結果取得

        p_value = stats.binom_test(n_correct, n_trials, 0.5, alternative='greater')
        assert p_value < 0.05, f"p-value={p_value:.4f}，預測不顯著優於隨機"

    def test_prediction_consistency(self):
        """卡方檢定：預測在不同時段的一致性"""
        # 將回測數據分為早盤/中盤/尾盤
        # 驗證各時段準確率無顯著差異

    def test_signal_correlation(self):
        """Pearson 相關係數：訊號分數與實際漲跌幅的相關性"""
        # 預期：r > 0.1（正相關）且 p < 0.05

    def test_sharpe_ratio(self):
        """基於模擬交易的 Sharpe Ratio"""
        # 使用訊號進行模擬交易
        # Sharpe Ratio > 1.0 為合格

    def test_confusion_matrix(self):
        """混淆矩陣分析"""
        # 計算 Precision, Recall, F1-Score
        # 分析看漲/看跌/中性三類的分類表現

    def test_rolling_accuracy(self):
        """滾動視窗準確率穩定性"""
        # 使用 20 期滾動視窗計算準確率
        # 預期：標準差 < 10%，無明顯趨勢性下降
```

---

## 7. CI/CD 流程設計

### 7.1 自動化測試觸發時機

```yaml
# .github/workflows/test.yml

name: Test Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 1 * * 1-5'  # 每週一至五凌晨1點（回測驗證）

jobs:
  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install Python dependencies
        run: pip install -r requirements.txt -r requirements-test.txt

      - name: Install Node dependencies
        run: npm ci

      - name: Run Python unit tests
        run: pytest tests/unit/ -v --cov=src --cov-report=xml --cov-fail-under=85

      - name: Run Frontend unit tests
        run: npx vitest run --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v4

  integration-tests:
    name: Integration Tests
    needs: unit-tests
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7
        ports: ['6379:6379']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-test.txt

      - name: Run integration tests
        run: pytest tests/integration/ -v --timeout=60
        env:
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY_TEST }}
          REDIS_URL: redis://localhost:6379

  e2e-tests:
    name: E2E Tests
    needs: integration-tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Build application
        run: npm run build

      - name: Run E2E tests
        run: npx playwright test

      - name: Upload test artifacts
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: playwright-report/

  performance-tests:
    name: Performance Tests (Weekly)
    if: github.event_name == 'schedule'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-test.txt

      - name: Run benchmark tests
        run: pytest tests/performance/ -v --benchmark-json=benchmark.json

      - name: Store benchmark result
        uses: benchmark-action/github-action-benchmark@v1
        with:
          tool: 'pytest'
          output-file-path: benchmark.json
```

### 7.2 測試環境配置

| 環境 | 用途 | 數據來源 | 外部 API |
|------|------|----------|----------|
| **Local** | 開發者本地測試 | fixtures / SQLite | Mock |
| **CI** | 自動化測試 | fixtures / SQLite | Mock |
| **Staging** | 預發佈驗證 | 歷史真實數據副本 | Groq (test key) |
| **Production** | 線上監控 | 即時數據 | Groq (prod key) |

**環境變數管理：**

```bash
# .env.test
DATABASE_URL=sqlite:///test.db
GROQ_API_KEY=test-mock-key
GROQ_ENABLED=false
WEBSOCKET_URL=ws://localhost:8000/ws
LOG_LEVEL=DEBUG
```

### 7.3 部署前檢查清單

```yaml
# 部署前 Gate 檢查（所有項目必須通過）

pre_deploy_checklist:
  - name: 單元測試通過
    command: pytest tests/unit/ --tb=short
    required: true

  - name: 整合測試通過
    command: pytest tests/integration/ --tb=short
    required: true

  - name: E2E 測試通過
    command: npx playwright test
    required: true

  - name: 覆蓋率達標
    command: pytest --cov=src --cov-fail-under=85
    required: true

  - name: 無安全漏洞
    command: safety check && npm audit --audit-level=high
    required: true

  - name: 型別檢查通過
    command: mypy src/ && npx tsc --noEmit
    required: true

  - name: Lint 通過
    command: ruff check src/ && npx eslint .
    required: true

  - name: 效能回歸檢查
    command: pytest tests/performance/ --benchmark-compare
    required: false  # 警告但不阻擋
```

---

## 8. 測試數據管理

### 8.1 模擬數據生成策略

```python
# tests/conftest.py - 共用 Fixtures

import pytest
from tests.factories import MarketDataFactory, OrderBookFactory

@pytest.fixture
def sample_market_data():
    """標準市場數據 fixture"""
    return MarketDataFactory.create(
        stock_id="2330",
        price=890,
        prev_close=878,
        volume=25000,
    )

@pytest.fixture
def bullish_market_data():
    """多頭行情 fixture"""
    return MarketDataFactory.create_bullish(stock_id="2330")

@pytest.fixture
def bearish_market_data():
    """空頭行情 fixture"""
    return MarketDataFactory.create_bearish(stock_id="2330")
```

**Factory 設計：**

```python
# tests/factories.py

class MarketDataFactory:
    """市場數據工廠"""

    @staticmethod
    def create(stock_id, price, prev_close, volume, **kwargs):
        outer_ratio = kwargs.get('outer_ratio', 0.55)
        return {
            "stock_id": stock_id,
            "price": {"open": price * 0.99, "high": price * 1.01,
                      "low": price * 0.98, "close": price,
                      "prev_close": prev_close},
            "volume": {"total": volume,
                       "outer": int(volume * outer_ratio),
                       "inner": int(volume * (1 - outer_ratio))},
            "order_book": OrderBookFactory.create_balanced(price),
            "ticks": TickFactory.create_random(price, count=20),
            "technical": TechnicalFactory.create_neutral(),
        }

    @staticmethod
    def create_bullish(stock_id):
        """生成多頭行情數據"""
        return MarketDataFactory.create(
            stock_id=stock_id,
            price=900, prev_close=870,  # +3.4%
            volume=50000, outer_ratio=0.72,
        )

    @staticmethod
    def create_bearish(stock_id):
        """生成空頭行情數據"""
        return MarketDataFactory.create(
            stock_id=stock_id,
            price=850, prev_close=880,  # -3.4%
            volume=45000, outer_ratio=0.32,
        )

class OrderBookFactory:
    """五檔掛單工廠"""

    @staticmethod
    def create_balanced(base_price):
        return {
            "bid": [{"price": base_price - i, "qty": 100 + i * 20}
                    for i in range(5)],
            "ask": [{"price": base_price + i + 1, "qty": 100 + i * 20}
                    for i in range(5)],
        }

    @staticmethod
    def create_buy_heavy(base_price):
        """買方強勢掛單"""
        return {
            "bid": [{"price": base_price - i, "qty": 500 + i * 50}
                    for i in range(5)],
            "ask": [{"price": base_price + i + 1, "qty": 20 + i * 5}
                    for i in range(5)],
        }
```

### 8.2 測試 Fixture 設計

```
tests/
├── conftest.py                     # 全域 fixture（DB session, test client）
├── factories.py                    # 數據工廠
├── fixtures/
│   ├── market_data/                # 靜態 JSON fixture
│   ├── historical/                 # 歷史回測數據
│   └── edge_cases/                 # 邊界條件數據
├── unit/
│   ├── conftest.py                 # 單元測試專用 fixture
│   ├── signals/
│   │   ├── conftest.py             # 訊號測試 fixture
│   │   ├── test_outer_ratio.py
│   │   ├── test_order_book_pressure.py
│   │   ├── test_tick_direction.py
│   │   ├── test_intraday_position.py
│   │   ├── test_price_momentum.py
│   │   ├── test_rsi.py
│   │   ├── test_macd_osc.py
│   │   ├── test_kd_cross.py
│   │   └── test_trend_acceleration.py
│   ├── test_weighted_scoring.py
│   └── test_paper_trading.py
├── integration/
│   ├── conftest.py                 # 整合測試 fixture（test server, mock API）
│   ├── test_data_pipeline.py
│   ├── test_groq_integration.py
│   ├── test_verification_cycle.py
│   └── test_websocket.py
├── e2e/
│   ├── stock-analysis.spec.ts
│   ├── paper-trading.spec.ts
│   ├── ai-toggle.spec.ts
│   └── responsive.spec.ts
├── performance/
│   ├── test_signal_performance.py
│   ├── test_db_performance.py
│   └── locustfile.py
└── backtest/
    ├── test_prediction_accuracy.py
    └── test_statistical_validation.py
```

### 8.3 測試資料庫方案

| 測試類型 | 資料庫方案 | 說明 |
|---------|-----------|------|
| 單元測試 | 無資料庫（純函式測試） | 不依賴外部資源 |
| 整合測試 | SQLite in-memory | 每個測試自動建立/銷毀 |
| E2E 測試 | SQLite 檔案 | 預載 seed 數據 |
| 效能測試 | PostgreSQL (Docker) | 模擬生產環境 |

```python
# tests/integration/conftest.py

@pytest.fixture
async def test_db():
    """整合測試用的 in-memory 資料庫"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        # 插入基礎 seed 數據
        await seed_test_data(session)
        yield session

    await engine.dispose()


@pytest.fixture
async def test_client(test_db):
    """整合測試用的 HTTP 客戶端"""
    app.dependency_overrides[get_db] = lambda: test_db
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

---

## 附錄 A：測試命名規範

```
test_<被測功能>_<場景>_<預期結果>

範例：
test_outer_ratio_all_outer_returns_max_positive
test_buy_insufficient_balance_raises_error
test_pipeline_partial_data_skips_missing_signal
```

## 附錄 B：測試執行命令快速參考

```bash
# 執行全部單元測試
pytest tests/unit/ -v

# 執行特定訊號模組測試
pytest tests/unit/signals/test_rsi.py -v

# 執行整合測試
pytest tests/integration/ -v --timeout=60

# 執行 E2E 測試
npx playwright test

# 執行效能測試
pytest tests/performance/ -v --benchmark-only

# 生成覆蓋率報告
pytest tests/unit/ --cov=src --cov-report=html
open htmlcov/index.html

# 執行回測驗證
pytest tests/backtest/ -v --timeout=300

# 前端測試
npx vitest run --coverage
```

## 附錄 C：品質門檻 (Quality Gates)

| 門檻 | 條件 | 阻擋部署 |
|------|------|---------|
| 單元測試 | 100% 通過 | 是 |
| 整合測試 | 100% 通過 | 是 |
| E2E 測試 | ≥ 95% 通過（允許 flaky 重試） | 是 |
| 行覆蓋率 | ≥ 85% | 是 |
| 分支覆蓋率 | ≥ 80% | 是 |
| 安全掃描 | 無高風險漏洞 | 是 |
| 型別檢查 | 0 錯誤 | 是 |
| Lint | 0 錯誤 | 是 |
| 效能回歸 | 無超過 20% 的退化 | 否（警告） |
