# 02 - 台股數據收集架構規劃

> 本文件詳細規劃台股預測系統所需的數據來源、收集方式、快取策略與存儲方案，以個人開發者的實際可行性為最高優先。

---

## 1. 即時行情數據來源評估

### 1.1 台灣證券交易所 TWSE OpenAPI

| 項目 | 說明 |
|------|------|
| **官方網址** | https://openapi.twse.com.tw |
| **可取得數據** | 每日收盤行情、三大法人買賣超、融資融券、當日沖銷、信用交易、個股日成交資訊、外資持股比例、每日市場成交資訊 |
| **即時數據** | 盤中即時行情透過 `mis.twse.com.tw` 提供，約每 5 秒更新一次 |
| **更新頻率** | OpenAPI 以每日收盤後更新為主；即時行情 API（mis）每 5 秒更新 |
| **延遲** | 即時行情約 5-15 秒延遲；收盤數據約 16:00 後可取得 |
| **費用** | 完全免費 |
| **Rate Limit** | 每 5 秒最多 3 次請求，超過將被暫時封鎖 IP |
| **穩定性** | ★★★★☆（官方來源，穩定但有嚴格頻率限制） |
| **適用場景** | 每日收盤數據批次下載、基本面資訊、三大法人進出 |

**優點：**
- 官方資料來源，數據準確性最高
- 完全免費，無需申請帳號
- RESTful API，開發友善

**缺點：**
- Rate Limit 極嚴格（3次/5秒），不適合高頻即時查詢
- 即時行情 API 非官方正式支援，穩定性有疑慮
- 無 WebSocket 推送，必須輪詢（polling）

---

### 1.2 證券櫃檯買賣中心 TPEX API

| 項目 | 說明 |
|------|------|
| **官方網址** | https://www.tpex.org.tw/openapi/ |
| **可取得數據** | 上櫃股票每日收盤行情、三大法人買賣超、融資融券統計、外資持股、個股日成交資訊 |
| **更新頻率** | 每日收盤後更新 |
| **延遲** | 收盤後約 16:30 可取得 |
| **費用** | 完全免費 |
| **Rate Limit** | 類似 TWSE，建議每 5 秒不超過 3 次 |
| **穩定性** | ★★★★☆（官方來源，穩定可靠） |
| **適用場景** | 上櫃（OTC）股票的每日收盤數據 |

**優點：**
- 上櫃股票官方唯一來源
- 與 TWSE OpenAPI 格式類似，易於整合

**缺點：**
- 同樣無即時行情推送
- 僅提供上櫃股票數據

---

### 1.3 Yahoo Finance / yfinance

| 項目 | 說明 |
|------|------|
| **套件** | `yfinance`（Python） |
| **可取得數據** | 歷史日K/週K/月K、分鐘K線（1m/5m/15m/30m/60m）、基本面資訊、財務報表 |
| **即時報價** | 支援，但有 15-20 分鐘延遲（台股） |
| **更新頻率** | 日K 每日收盤後；分鐘K 近 7 天內可取得 |
| **延遲** | 台股報價延遲約 15-20 分鐘 |
| **費用** | 免費（非官方 API，透過網頁爬取） |
| **Rate Limit** | 無明確限制，但頻繁請求可能被暫時封鎖 |
| **穩定性** | ★★★☆☆（非官方介面，Yahoo 可能隨時更改結構） |
| **適用場景** | 歷史數據回測、分鐘級K線補充、基本面資料查詢 |

**優點：**
- 免費且使用簡便，一行程式碼即可取得數據
- 台股代號格式：`2330.TW`（上市）、`6488.TWO`（上櫃）
- 提供分鐘K線（近 7 天）可用於回測

**缺點：**
- 台股報價延遲 15-20 分鐘，不適合即時交易
- 非官方 API，穩定性無法保證
- 高頻請求可能被封鎖

---

### 1.4 Fugle 富果 API

| 項目 | 說明 |
|------|------|
| **官方網址** | https://developer.fugle.tw |
| **可取得數據** | 即時 Tick 成交明細、即時五檔報價、即時 K 線（Candles）、行情快照（Quotes）、成交量分佈（Volumes）、歷史 K 線與技術指標、股務事件 |
| **傳輸方式** | REST API（HTTP）+ WebSocket 即時推送 |
| **更新頻率** | WebSocket 即時推送（毫秒級）；REST API 按需查詢 |
| **延遲** | WebSocket 約 100-500ms（接近即時） |
| **SDK** | Python（`fugle-marketdata-python`）、Node.js（`fugle-marketdata-node`） |

**方案與價格：**

| 方案 | 價格 | WebSocket 訂閱數 | 連線數 | REST 呼叫/分 | 快照/分 |
|------|------|-------------------|--------|--------------|---------|
| **基本用戶** | 免費 | 5 檔 | 1 | 60 | 不支援 |
| **開發者** | NT$1,499/月 | 300 檔 | 2 | 600 | 600 |
| **進階用戶** | NT$2,999/月 | 2,000 檔 | 2 | 2,000 | 2,000 |

| 項目 | 說明 |
|------|------|
| **穩定性** | ★★★★★（專業金融數據服務商，SLA 保障） |
| **適用場景** | 即時行情推送、五檔報價、成交明細、盤中策略觸發 |

**優點：**
- 唯一提供 WebSocket 即時推送的獨立數據平台
- 免費方案即可訂閱 5 檔即時行情（含 Tick、五檔）
- 官方 Python/Node.js SDK，開發體驗極佳
- 涵蓋上市、上櫃、興櫃、ETF、權證、指數
- 資料來源為交易所官方資料

**缺點：**
- 免費方案僅 5 檔訂閱，監控多檔需付費
- 付費方案費用較高（個人開發者考量）

---

### 1.5 台股資訊爬蟲方案

#### Goodinfo! 台灣股市資訊網

| 項目 | 說明 |
|------|------|
| **網址** | https://goodinfo.tw |
| **可取得數據** | 個股基本面、財務報表、技術指標、股利資訊、法人買賣、主力進出、融資融券、產業分類 |
| **爬取方式** | HTTP 請求 + HTML 解析（需設定 User-Agent 模擬瀏覽器） |
| **更新頻率** | 收盤後更新 |
| **費用** | 免費（爬蟲） |
| **穩定性** | ★★☆☆☆（反爬蟲機制持續加強，需維護爬蟲程式） |
| **適用場景** | 基本面數據補充、歷史財報分析 |

**注意事項：**
- Goodinfo 已加強反爬蟲機制，需模擬瀏覽器 headers
- 建議使用 `requests` + `BeautifulSoup`，並設定合理請求間隔
- 不適合高頻即時數據取得

#### Wantgoo 玩股網

| 項目 | 說明 |
|------|------|
| **網址** | https://wantgoo.com |
| **可取得數據** | 盤中走勢、技術分析、法人買賣、主力動態 |
| **爬取方式** | 部分數據透過 AJAX/JSON API 可取得 |
| **穩定性** | ★★☆☆☆ |
| **適用場景** | 補充性數據來源 |

#### twstock（Python 模組）

| 項目 | 說明 |
|------|------|
| **GitHub** | https://github.com/mlouielu/twstock |
| **可取得數據** | 即時股價（透過 TWSE mis API）、歷史價格、均價、均量、BFP 分析 |
| **穩定性** | ★★★☆☆（社群維護，依賴 TWSE API 結構） |
| **適用場景** | 快速原型開發、歷史數據取得 |

---

### 1.6 券商 API

#### 永豐金 Shioaji API

| 項目 | 說明 |
|------|------|
| **官方網址** | https://sinotrade.github.io |
| **前置條件** | 需開立永豐金證券帳戶 |
| **可取得數據** | 即時 Tick 成交明細（含內外盤）、即時五檔委買委賣、即時報價、歷史 K 線 |
| **傳輸方式** | WebSocket 即時推送（訂閱後自動回傳） |
| **行情訂閱類型** | `tick`（成交明細）、`bidask`（五檔）、`quote`（五檔+明細） |
| **SDK** | Python（`shioaji`） |
| **費用** | 免費（需為永豐金客戶） |
| **穩定性** | ★★★★★（市佔率近五成，經多次改版後極穩定） |
| **適用場景** | 即時行情全面取得、程式交易下單 |

**優點：**
- 台灣最成熟的券商 API，穩定性極高
- 免費提供即時 Tick + 五檔數據（開戶即可使用）
- WebSocket 即時推送，延遲低（毫秒級）
- 可同時訂閱多檔標的行情
- 支援下單功能，可做完整交易系統

**缺點：**
- 必須開立永豐金證券帳戶
- 僅提供 Python SDK
- 盤後需重新登入

#### 富邦新一代 API（Fubon API）

| 項目 | 說明 |
|------|------|
| **官方網址** | https://www.fbs.com.tw/TradeAPI/ |
| **前置條件** | 需開立富邦證券帳戶 |
| **可取得數據** | 即時行情、五檔、Tick、期貨行情 |
| **SDK** | 基於 Fugle SDK 架構 |
| **穩定性** | ★★★★☆ |

#### 元富 Nova API（Masterlink）

| 項目 | 說明 |
|------|------|
| **官方網址** | https://ml-fugle-api.masterlink.com.tw |
| **說明** | 基於 Fugle SDK 架構的元富版本 |
| **穩定性** | ★★★★☆ |

---

### 數據來源綜合評比

| 數據源 | 即時性 | 數據完整度 | 穩定性 | 費用 | 開發友善度 | 綜合推薦 |
|--------|--------|-----------|--------|------|-----------|---------|
| **Shioaji（永豐金）** | ★★★★★ | ★★★★★ | ★★★★★ | 免費 | ★★★★☆ | **首選** |
| **Fugle 基本方案** | ★★★★★ | ★★★★☆ | ★★★★★ | 免費 | ★★★★★ | **次選** |
| **TWSE OpenAPI** | ★★☆☆☆ | ★★★★☆ | ★★★★☆ | 免費 | ★★★★☆ | 收盤數據 |
| **yfinance** | ★★☆☆☆ | ★★★☆☆ | ★★★☆☆ | 免費 | ★★★★★ | 歷史回測 |
| **Goodinfo 爬蟲** | ★☆☆☆☆ | ★★★★★ | ★★☆☆☆ | 免費 | ★★☆☆☆ | 基本面補充 |

---

## 2. 各訊號所需數據的具體取得方案

### 訊號 1：外盤比率

| 項目 | 說明 |
|------|------|
| **所需數據** | 每筆成交明細（Tick data），需區分內盤/外盤 |
| **數據定義** | 外盤 = 成交價 ≥ 委賣價（買方主動成交）；內盤 = 成交價 ≤ 委買價（賣方主動成交） |
| **推薦來源** | **Shioaji API**（首選）/ Fugle API |
| **取得方式** | WebSocket 訂閱 `tick` 類型，每筆成交自動推送 |
| **數據欄位** | 成交價、成交量、成交時間、買賣別（bid/ask） |
| **更新頻率** | 逐筆即時推送 |
| **計算方式** | `外盤比率 = 外盤成交量 / (外盤成交量 + 內盤成交量) × 100%` |

**Shioaji 實作要點：**
```python
# 訂閱 tick 行情
api.quote.subscribe(contract, quote_type=sj.constant.QuoteType.Tick)

# tick 回傳欄位包含：
# - close: 成交價
# - volume: 成交量
# - bid_price / ask_price: 對應的委買/委賣價
# 透過比較 close 與 bid/ask 判斷內外盤
```

---

### 訊號 2：五檔委買委賣

| 項目 | 說明 |
|------|------|
| **所需數據** | 即時五檔委買價量 + 五檔委賣價量（共 10 個價位） |
| **推薦來源** | **Shioaji API**（首選）/ Fugle API |
| **取得方式** | WebSocket 訂閱 `bidask` 類型 |
| **數據欄位** | bid_price[1-5]、bid_volume[1-5]、ask_price[1-5]、ask_volume[1-5] |
| **更新頻率** | 即時推送（五檔變動時推送） |

**Shioaji 實作要點：**
```python
# 訂閱五檔行情
api.quote.subscribe(contract, quote_type=sj.constant.QuoteType.BidAsk)

# 回傳：bid_price, bid_volume, ask_price, ask_volume (各5檔)
```

**Fugle WebSocket 實作要點：**
```python
from fugle_marketdata import WebSocketClient

client = WebSocketClient(api_key='YOUR_API_KEY')
stock = client.stock
stock.connect()
stock.subscribe({'channel': 'trades', 'symbol': '2330'})  # 成交
stock.subscribe({'channel': 'books', 'symbol': '2330'})    # 五檔
```

---

### 訊號 3：最近 10 筆成交明細

| 項目 | 說明 |
|------|------|
| **所需數據** | 最近 10 筆逐筆成交記錄（價格、數量、時間） |
| **推薦來源** | **Shioaji API**（首選）/ Fugle API |
| **取得方式** | WebSocket 訂閱 `tick`，本地維護 10 筆滾動緩衝區 |
| **數據欄位** | 成交價、成交量、成交時間、累計成交量 |
| **更新頻率** | 逐筆即時推送 |
| **實作策略** | 使用 `collections.deque(maxlen=10)` 維護最近 10 筆 |

```python
from collections import deque

recent_ticks = deque(maxlen=10)

def on_tick(tick_data):
    recent_ticks.append({
        'price': tick_data.close,
        'volume': tick_data.volume,
        'time': tick_data.datetime,
        'total_volume': tick_data.total_volume
    })
```

---

### 訊號 4：日內高低位置

| 項目 | 說明 |
|------|------|
| **所需數據** | 當日開盤價、最高價、最低價、現價 |
| **推薦來源** | **Shioaji API**（tick 累計計算）/ Fugle REST API（Quote） |
| **取得方式** | 方案A：從 tick 資料即時計算當日高低；方案B：REST API 查詢日內行情 |
| **數據欄位** | open、high、low、close（即時） |
| **更新頻率** | 逐筆更新（方案A）/ 按需查詢（方案B） |
| **計算方式** | `日內位置 = (現價 - 最低價) / (最高價 - 最低價) × 100%` |

**推薦方案A - 即時累計計算：**
```python
class IntradayTracker:
    def __init__(self):
        self.open_price = None
        self.high_price = float('-inf')
        self.low_price = float('inf')
        self.current_price = None

    def update(self, tick):
        if self.open_price is None:
            self.open_price = tick.close
        self.high_price = max(self.high_price, tick.close)
        self.low_price = min(self.low_price, tick.close)
        self.current_price = tick.close

    @property
    def position_pct(self):
        if self.high_price == self.low_price:
            return 50.0
        return (self.current_price - self.low_price) / (self.high_price - self.low_price) * 100
```

---

### 訊號 5：即時漲跌幅

| 項目 | 說明 |
|------|------|
| **所需數據** | 現價 + 昨日收盤價 |
| **推薦來源** | **Shioaji API**（tick 內含參考價）/ TWSE OpenAPI（昨收價） |
| **取得方式** | tick 推送中取得現價；昨收價於開盤前查詢一次並快取 |
| **計算方式** | `漲跌幅 = (現價 - 昨收價) / 昨收價 × 100%` |
| **更新頻率** | 逐筆即時 |

**昨收價取得策略：**
- 開盤前（08:30）呼叫 TWSE OpenAPI 取得前一交易日收盤價
- 存入記憶體快取，盤中不需重複查詢
- 備用方案：yfinance 查詢前一日收盤價

---

### 訊號 6：RSI（相對強弱指標）

| 項目 | 說明 |
|------|------|
| **所需數據** | 歷史收盤價序列（至少 N+1 個週期，N 為 RSI 週期參數，通常 N=14） |
| **時間粒度** | 分鐘級 RSI → 需分鐘 K 線；日級 RSI → 需日 K 線 |
| **推薦來源（即時分鐘級）** | **Fugle API**（Candles endpoint）/ Shioaji tick 自行聚合 |
| **推薦來源（歷史日級）** | **yfinance** / TWSE OpenAPI |
| **計算方式** | Wilder's smoothing method |

**數據取得策略：**
1. **盤前載入歷史數據**：透過 yfinance 取得近 30 日日 K 線，計算日級 RSI 基礎值
2. **盤中即時更新**：透過 tick 數據聚合為分鐘 K，滾動計算分鐘級 RSI
3. **分鐘 K 聚合方式**：每分鐘取 tick 的 OHLCV

```python
import yfinance as yf

# 盤前載入歷史數據
hist = yf.download('2330.TW', period='3mo', interval='1d')

# 計算 RSI
def calc_rsi(prices, period=14):
    deltas = prices.diff()
    gain = deltas.where(deltas > 0, 0).rolling(window=period).mean()
    loss = (-deltas.where(deltas < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))
```

---

### 訊號 7：MACD OSC（MACD 柱狀圖/振盪指標）

| 項目 | 說明 |
|------|------|
| **所需數據** | 歷史收盤價序列（至少 35 個週期：26 + 9 緩衝） |
| **時間粒度** | 分鐘級 / 日級 |
| **推薦來源（歷史）** | **yfinance**（日 K）/ TWSE OpenAPI |
| **推薦來源（即時）** | Shioaji tick → 聚合分鐘 K → 即時計算 |
| **計算方式** | DIF = EMA12 - EMA26；MACD = DIF 的 EMA9；OSC = DIF - MACD |

**數據取得策略：**
1. 盤前載入近 60 日日 K 線計算日級 MACD 基礎值
2. 盤中使用分鐘收盤價即時更新分鐘級 MACD OSC

---

### 訊號 8：KD 值（隨機指標）

| 項目 | 說明 |
|------|------|
| **所需數據** | 歷史最高價、最低價、收盤價序列（至少 N 個週期，通常 N=9） |
| **時間粒度** | 分鐘級 / 日級 |
| **推薦來源（歷史）** | **yfinance**（含 High/Low/Close） |
| **推薦來源（即時）** | Shioaji tick → 聚合分鐘 K（OHLC） |
| **計算方式** | RSV = (Close - Low_N) / (High_N - Low_N) × 100；K = 2/3 × K_prev + 1/3 × RSV；D = 2/3 × D_prev + 1/3 × K |

**數據取得策略：**
1. 盤前載入近 30 日日 K（含 High/Low/Close）
2. 盤中即時追蹤滾動 N 期的 High/Low 窗口，逐筆更新 KD

---

### 訊號 9：盤中走勢加速度

| 項目 | 說明 |
|------|------|
| **所需數據** | 高頻 Tick 數據（價格時間序列） |
| **推薦來源** | **Shioaji API** tick 推送 |
| **取得方式** | WebSocket 逐筆 tick，維護時間窗口內的價格序列 |
| **計算方式** | 速度 = Δ價格/Δ時間；加速度 = Δ速度/Δ時間（二階微分） |
| **更新頻率** | 逐筆即時計算 |

**實作策略：**
```python
class MomentumTracker:
    def __init__(self, window_seconds=60):
        self.ticks = deque()  # (timestamp, price)
        self.window = window_seconds

    def update(self, timestamp, price):
        self.ticks.append((timestamp, price))
        # 清除窗口外的舊數據
        cutoff = timestamp - self.window
        while self.ticks and self.ticks[0][0] < cutoff:
            self.ticks.popleft()

    def get_acceleration(self):
        if len(self.ticks) < 3:
            return 0.0
        # 取前半段與後半段的斜率差
        mid = len(self.ticks) // 2
        v1 = self._slope(list(self.ticks)[:mid])
        v2 = self._slope(list(self.ticks)[mid:])
        dt = (self.ticks[-1][0] - self.ticks[0][0]) / 2
        return (v2 - v1) / dt if dt > 0 else 0.0

    def _slope(self, points):
        if len(points) < 2:
            return 0.0
        dt = points[-1][0] - points[0][0]
        dp = points[-1][1] - points[0][1]
        return dp / dt if dt > 0 else 0.0
```

---

### 訊號數據需求彙總表

| 訊號 | 核心數據 | 即時來源 | 歷史來源 | 更新頻率 |
|------|---------|---------|---------|---------|
| 外盤比率 | Tick（含內外盤） | Shioaji tick | - | 逐筆 |
| 五檔委買委賣 | 五檔報價 | Shioaji bidask | - | 即時 |
| 最近10筆成交 | Tick 明細 | Shioaji tick | - | 逐筆 |
| 日內高低位置 | 當日 OHLC | Shioaji tick 累計 | - | 逐筆 |
| 即時漲跌幅 | 現價+昨收 | Shioaji tick | TWSE OpenAPI | 逐筆 |
| RSI | 收盤價序列 | tick→分鐘K | yfinance | 每分鐘 |
| MACD OSC | 收盤價序列 | tick→分鐘K | yfinance | 每分鐘 |
| KD 值 | HLC 序列 | tick→分鐘K | yfinance | 每分鐘 |
| 走勢加速度 | 高頻 Tick | Shioaji tick | - | 逐筆 |

---

## 3. 數據收集架構設計

### 3.1 推薦的主要數據源組合方案

基於個人開發者的可行性與成本考量，推薦以下分層數據源方案：

```
┌─────────────────────────────────────────────────┐
│              數據源分層架構                        │
├─────────────────────────────────────────────────┤
│                                                   │
│  【第一層：即時行情 - 核心層】                      │
│   永豐金 Shioaji API（免費，需開戶）                │
│   ├── WebSocket Tick 推送（內外盤、成交明細）       │
│   ├── WebSocket BidAsk 推送（五檔委買委賣）        │
│   └── 即時報價（現價、漲跌幅）                     │
│                                                   │
│  【第二層：即時補充 - 擴展層】                      │
│   Fugle API 基本方案（免費，5檔）                   │
│   ├── REST API 日內行情查詢                        │
│   └── WebSocket（備用即時通道）                     │
│                                                   │
│  【第三層：歷史數據 - 基礎層】                      │
│   yfinance + TWSE/TPEX OpenAPI（免費）             │
│   ├── 歷史日K/分鐘K（技術指標計算）                 │
│   ├── 每日收盤行情                                 │
│   └── 三大法人、融資融券等輔助資訊                  │
│                                                   │
│  【第四層：基本面 - 輔助層】                        │
│   TWSE OpenAPI + Goodinfo 爬蟲（免費）             │
│   ├── 財務報表                                     │
│   └── 股利、營收等基本面資訊                       │
│                                                   │
└─────────────────────────────────────────────────┘
```

**此方案優點：完全免費（僅需永豐金開戶）、涵蓋所有 9 大訊號需求。**

---

### 3.2 WebSocket 即時數據推送架構

```
                        ┌──────────────┐
                        │   Shioaji     │
                        │  WebSocket    │
                        │   Server      │
                        └──────┬───────┘
                               │ tick / bidask 推送
                               ▼
┌─────────────────────────────────────────────────┐
│              DataStreamManager                    │
│  ┌───────────────────────────────────────────┐   │
│  │         WebSocket Connection Pool          │   │
│  │  - 自動重連機制（指數退避）               │   │
│  │  - 心跳檢測（30秒間隔）                   │   │
│  │  - 連線狀態監控                            │   │
│  └───────────────┬───────────────────────────┘   │
│                  │                                │
│  ┌───────────────▼───────────────────────────┐   │
│  │          Message Router                    │   │
│  │  - 依股票代號分發至對應處理器              │   │
│  │  - 依數據類型（tick/bidask）路由           │   │
│  └───┬───────────┬───────────┬───────────────┘   │
│      │           │           │                    │
│      ▼           ▼           ▼                    │
│  ┌───────┐  ┌───────┐  ┌───────┐                │
│  │ Stock  │  │ Stock  │  │ Stock  │  ...          │
│  │ 2330   │  │ 2317   │  │ 2454   │               │
│  │Handler │  │Handler │  │Handler │               │
│  └───┬───┘  └───┬───┘  └───┬───┘                │
│      │          │          │                      │
│      ▼          ▼          ▼                      │
│  ┌──────────────────────────────────────────┐    │
│  │         Signal Calculator Engine          │    │
│  │  - 9大訊號即時計算                        │    │
│  │  - 事件驅動（每筆tick觸發重算）           │    │
│  └──────────────┬───────────────────────────┘    │
│                 │                                  │
│                 ▼                                  │
│  ┌──────────────────────────────────────────┐    │
│  │         In-Memory Cache (快取層)          │    │
│  │  - 最新訊號值                             │    │
│  │  - 最近N筆Tick緩衝                        │    │
│  │  - 分鐘K線聚合結果                        │    │
│  └──────────────┬───────────────────────────┘    │
│                 │                                  │
└─────────────────┼──────────────────────────────────┘
                  │
                  ▼
        ┌─────────────────┐
        │   Backend API    │
        │  (FastAPI /      │
        │   WebSocket)     │
        └────────┬────────┘
                 │ 推送至前端
                 ▼
        ┌─────────────────┐
        │    Frontend      │
        │  (瀏覽器)        │
        └─────────────────┘
```

---

### 3.3 數據快取策略

#### 三層快取架構

| 快取層級 | 儲存位置 | 數據類型 | 存活時間 | 用途 |
|---------|---------|---------|---------|------|
| **L1：即時快取** | Python dict / deque（記憶體） | 最新 tick、五檔、訊號值 | 即時覆蓋 | 訊號計算、前端推送 |
| **L2：短期快取** | Redis（或記憶體） | 分鐘 K、近期訊號歷史 | 1 交易日 | 盤中技術指標計算 |
| **L3：持久快取** | SQLite / PostgreSQL | 日 K、歷史訊號、預測記錄 | 永久 | 歷史回測、模型訓練 |

**個人開發者簡化方案（推薦）：**
- L1 + L2 統一使用 Python 記憶體（dict + deque），免去 Redis 部署
- L3 使用 SQLite，零配置免部署

```python
# 快取結構範例
cache = {
    '2330': {
        'latest_tick': {...},           # L1: 最新一筆 tick
        'latest_bidask': {...},         # L1: 最新五檔
        'recent_ticks': deque(maxlen=100),  # L1: 近100筆tick
        'minute_bars': deque(maxlen=300),   # L2: 近300根分鐘K
        'signals': {                    # L1: 最新訊號值
            'outer_ratio': 0.62,
            'bid_ask_strength': 1.35,
            'rsi': 58.3,
            'macd_osc': 0.12,
            'kd_k': 72.5,
            'kd_d': 68.1,
            'intraday_position': 0.75,
            'change_pct': 1.23,
            'acceleration': 0.05
        },
        'metadata': {
            'prev_close': 580.0,
            'open_price': 582.0,
            'day_high': 588.0,
            'day_low': 579.0,
        }
    }
}
```

---

### 3.4 數據更新頻率建議

| 更新層級 | 頻率 | 數據內容 | 觸發方式 |
|---------|------|---------|---------|
| **即時層（Tick-level）** | 逐筆（~100ms） | tick 成交明細、五檔報價 | WebSocket push |
| **秒級層** | 每 1-3 秒 | 外盤比率、漲跌幅、日內位置、走勢加速度 | tick 驅動計算 |
| **分鐘層** | 每 1 分鐘 | RSI、MACD OSC、KD 值（分鐘級） | 分鐘 K 完成時 |
| **盤前載入** | 每日 08:30 | 歷史日 K（RSI/MACD/KD 基礎值）、昨收價 | 排程觸發 |
| **盤後批次** | 每日 14:30 後 | 當日收盤數據、法人買賣、預測結果驗證 | 排程觸發 |

---

### 3.5 數據格式標準化規範

#### Tick 數據 JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "TickData",
  "type": "object",
  "required": ["symbol", "timestamp", "price", "volume", "side"],
  "properties": {
    "symbol": {
      "type": "string",
      "description": "股票代號",
      "example": "2330"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "成交時間 (ISO 8601)",
      "example": "2026-04-09T09:01:23.456+08:00"
    },
    "price": {
      "type": "number",
      "description": "成交價",
      "example": 585.0
    },
    "volume": {
      "type": "integer",
      "description": "成交張數",
      "example": 3
    },
    "side": {
      "type": "string",
      "enum": ["buy", "sell", "unknown"],
      "description": "內外盤別 (buy=外盤, sell=內盤)"
    },
    "total_volume": {
      "type": "integer",
      "description": "累計成交量"
    }
  }
}
```

#### 五檔報價 JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "OrderBookData",
  "type": "object",
  "required": ["symbol", "timestamp", "bids", "asks"],
  "properties": {
    "symbol": { "type": "string" },
    "timestamp": { "type": "string", "format": "date-time" },
    "bids": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "price": { "type": "number" },
          "volume": { "type": "integer" }
        }
      },
      "minItems": 5,
      "maxItems": 5,
      "description": "五檔委買 (由高到低)"
    },
    "asks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "price": { "type": "number" },
          "volume": { "type": "integer" }
        }
      },
      "minItems": 5,
      "maxItems": 5,
      "description": "五檔委賣 (由低到高)"
    }
  }
}
```

#### 訊號輸出 JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SignalOutput",
  "type": "object",
  "required": ["symbol", "timestamp", "signals", "prediction"],
  "properties": {
    "symbol": { "type": "string" },
    "timestamp": { "type": "string", "format": "date-time" },
    "signals": {
      "type": "object",
      "properties": {
        "outer_ratio": { "type": "number", "minimum": 0, "maximum": 100 },
        "bid_ask_strength": { "type": "number" },
        "recent_trades_trend": { "type": "number", "minimum": -1, "maximum": 1 },
        "intraday_position": { "type": "number", "minimum": 0, "maximum": 100 },
        "change_pct": { "type": "number" },
        "rsi": { "type": "number", "minimum": 0, "maximum": 100 },
        "macd_osc": { "type": "number" },
        "kd_k": { "type": "number", "minimum": 0, "maximum": 100 },
        "kd_d": { "type": "number", "minimum": 0, "maximum": 100 },
        "acceleration": { "type": "number" }
      }
    },
    "prediction": {
      "type": "object",
      "properties": {
        "direction": { "type": "string", "enum": ["up", "down", "neutral"] },
        "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
        "weighted_score": { "type": "number" }
      }
    }
  }
}
```

---

### 3.6 異常處理與容錯機制

#### WebSocket 連線管理

| 異常類型 | 處理策略 |
|---------|---------|
| **連線斷開** | 指數退避重連（1s → 2s → 4s → 8s → 最大 60s） |
| **心跳超時** | 30 秒無數據視為斷線，主動重連 |
| **認證過期** | 自動重新登入（Shioaji 需重新 login） |
| **數據異常** | 價格跳動超過漲跌停範圍，標記並跳過 |
| **重複數據** | 依 timestamp 去重 |

#### 數據品質檢查

```python
class DataValidator:
    @staticmethod
    def validate_tick(tick):
        """驗證 tick 數據合理性"""
        checks = [
            tick.price > 0,                    # 價格為正
            tick.volume > 0,                    # 成交量為正
            tick.price <= tick.limit_up,        # 不超過漲停
            tick.price >= tick.limit_down,      # 不低於跌停
        ]
        return all(checks)

    @staticmethod
    def validate_bidask(bidask):
        """驗證五檔數據合理性"""
        # 委買價遞減、委賣價遞增
        bids_desc = all(bidask.bid_price[i] >= bidask.bid_price[i+1]
                       for i in range(4))
        asks_asc = all(bidask.ask_price[i] <= bidask.ask_price[i+1]
                      for i in range(4))
        return bids_desc and asks_asc
```

#### 降級策略

```
主要來源不可用時的降級路徑：

Shioaji 斷線 → 切換至 Fugle WebSocket（備用）
                → 切換至 TWSE mis API 輪詢（最終備用）

yfinance 異常 → 切換至 TWSE OpenAPI 取歷史數據
               → 切換至 twstock 模組

全部來源不可用 → 暫停訊號計算
                → 記錄異常日誌
                → 前端顯示「數據源異常」警告
```

---

## 4. 歷史數據存儲

### 4.1 歷史行情數據存儲方案

#### 推薦方案：SQLite（個人開發者首選）

**選擇理由：**
- 零配置、零部署，單一檔案即可
- Python 內建支援（`sqlite3`）
- 讀取效能足夠支撐個人規模的歷史查詢
- 易於備份（複製檔案即可）

#### 資料表設計

```sql
-- 日K線歷史數據
CREATE TABLE daily_ohlcv (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    date DATE NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume INTEGER NOT NULL,
    turnover REAL,              -- 成交金額
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date)
);
CREATE INDEX idx_daily_symbol_date ON daily_ohlcv(symbol, date);

-- 分鐘K線（盤中使用，盤後可選擇性保存）
CREATE TABLE minute_bars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    datetime TIMESTAMP NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume INTEGER NOT NULL,
    UNIQUE(symbol, datetime)
);
CREATE INDEX idx_minute_symbol_dt ON minute_bars(symbol, datetime);

-- 每日快照（收盤後保存當日各訊號最終值）
CREATE TABLE daily_signals_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    date DATE NOT NULL,
    outer_ratio REAL,
    bid_ask_strength REAL,
    rsi_14 REAL,
    macd_osc REAL,
    kd_k REAL,
    kd_d REAL,
    intraday_position REAL,
    change_pct REAL,
    acceleration REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date)
);
```

---

### 4.2 預測記錄與驗證結果存儲

```sql
-- 預測記錄
CREATE TABLE predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    predict_time TIMESTAMP NOT NULL,    -- 預測產生時間
    predict_direction TEXT NOT NULL,     -- 'up' / 'down' / 'neutral'
    confidence REAL NOT NULL,           -- 信心度 0-1
    weighted_score REAL NOT NULL,       -- 加權總分
    price_at_predict REAL NOT NULL,     -- 預測時價格
    signals_json TEXT NOT NULL,         -- 預測時9大訊號值（JSON）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 預測驗證結果
CREATE TABLE prediction_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id INTEGER NOT NULL,
    verify_time TIMESTAMP NOT NULL,     -- 驗證時間
    verify_interval TEXT NOT NULL,      -- '1min' / '5min' / '15min' / '30min'
    price_at_verify REAL NOT NULL,      -- 驗證時價格
    actual_change_pct REAL NOT NULL,    -- 實際漲跌幅
    actual_direction TEXT NOT NULL,     -- 實際方向
    is_correct BOOLEAN NOT NULL,        -- 預測是否正確
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prediction_id) REFERENCES predictions(id)
);
CREATE INDEX idx_pred_symbol_time ON predictions(symbol, predict_time);
CREATE INDEX idx_result_pred_id ON prediction_results(prediction_id);

-- 每日統計報表
CREATE TABLE daily_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    symbol TEXT NOT NULL,
    total_predictions INTEGER NOT NULL,
    correct_predictions INTEGER NOT NULL,
    accuracy_rate REAL NOT NULL,         -- 準確率
    avg_confidence REAL,                 -- 平均信心度
    profit_loss_pct REAL,               -- 模擬損益（%）
    UNIQUE(date, symbol)
);
```

---

### 4.3 資料庫方案比較

| 方案 | 適用規模 | 部署難度 | 查詢效能 | 推薦情境 |
|------|---------|---------|---------|---------|
| **SQLite** | 個人/小型 | ★☆☆☆☆ | ★★★☆☆ | **個人開發首選** |
| **PostgreSQL** | 中大型 | ★★★☆☆ | ★★★★★ | 未來擴展、多用戶 |
| **TimescaleDB** | 時序數據 | ★★★★☆ | ★★★★★ | 大量 tick 數據存儲 |
| **InfluxDB** | 時序專用 | ★★★☆☆ | ★★★★★ | 純時序指標存儲 |

**推薦路徑：** SQLite 起步 → 數據量增大後遷移至 PostgreSQL/TimescaleDB

---

## 5. 成本與限制分析

### 5.1 免費方案 vs 付費方案比較

#### 方案 A：完全免費方案（推薦起步）

| 組件 | 來源 | 費用 | 限制 |
|------|------|------|------|
| 即時 Tick + 五檔 | Shioaji（永豐金） | 免費 | 需開戶 |
| 即時備用 | Fugle 基本方案 | 免費 | 5 檔訂閱、60 次/分 |
| 歷史日 K | yfinance | 免費 | 偶爾被封鎖 |
| 每日收盤 | TWSE/TPEX OpenAPI | 免費 | 3 次/5 秒 |
| 基本面 | TWSE OpenAPI | 免費 | 3 次/5 秒 |
| **月成本** | | **NT$0** | |

#### 方案 B：進階免費 + 低成本方案

| 組件 | 來源 | 費用 | 優勢 |
|------|------|------|------|
| 即時行情 | Shioaji | 免費 | 無限檔數 |
| 即時擴展 | Fugle 開發者方案 | NT$1,499/月 | 300 檔 WebSocket、600 次/分 REST |
| 歷史數據 | yfinance + TWSE | 免費 | - |
| **月成本** | | **NT$1,499** | |

#### 方案 C：專業級方案

| 組件 | 來源 | 費用 | 優勢 |
|------|------|------|------|
| 即時行情 | Shioaji | 免費 | 核心即時數據 |
| 行情擴展 | Fugle 進階方案 | NT$2,999/月 | 2000 檔、2000 次/分 |
| 歷史+回測 | TEJ 數據庫 | ~NT$5,000/月 | 專業級歷史數據 |
| **月成本** | | **~NT$8,000** | |

---

### 5.2 各 API 請求限制（Rate Limit）彙整

| API | Rate Limit | 封鎖機制 | 建議使用方式 |
|-----|-----------|---------|-------------|
| **TWSE OpenAPI** | 3 次/5 秒 | 暫時封鎖 IP | 批次查詢、設定間隔 ≥2 秒 |
| **TWSE mis（即時）** | 3 次/5 秒 | 暫時封鎖 IP | 改用 Shioaji WebSocket |
| **TPEX OpenAPI** | ~3 次/5 秒 | 暫時封鎖 IP | 同 TWSE 策略 |
| **Fugle 基本** | 60 次/分鐘（REST） | 回傳 429 | 搭配快取減少請求 |
| **Fugle 開發者** | 600 次/分鐘 | 回傳 429 | 充裕 |
| **Shioaji** | WebSocket 無限制 | 依連線數限制 | 盤中保持連線即可 |
| **yfinance** | 無明確限制 | 隨機封鎖 IP | 集中於盤前/盤後批次 |
| **Goodinfo** | 無明確限制 | User-Agent 檢查 | 低頻使用，設定間隔 ≥3 秒 |

---

### 5.3 建議的最佳實踐方案

#### 個人開發者推薦方案（方案 A：完全免費）

```
推薦架構：Shioaji（核心即時）+ yfinance（歷史）+ TWSE OpenAPI（收盤）

時間軸：

  08:30  盤前準備
         ├── yfinance 下載最新歷史 K 線（日K、分鐘K）
         ├── TWSE OpenAPI 取得昨日收盤數據
         └── 計算 RSI/MACD/KD 基礎值

  08:45  啟動 Shioaji 連線
         ├── 登入 API
         ├── 訂閱目標股票的 tick + bidask
         └── 初始化即時計算引擎

  09:00  開盤 → 即時數據流
   ~     ├── 逐筆接收 tick → 更新 9 大訊號
  13:30  ├── 每分鐘聚合分鐘K → 更新技術指標
         ├── 訊號達閾值 → 產生預測 → 推送前端
         └── 記錄預測至資料庫

  13:30  收盤
         ├── 儲存當日分鐘K至資料庫
         ├── 儲存當日訊號快照
         └── 斷開 Shioaji 連線

  14:30  盤後驗證
         ├── TWSE OpenAPI 取得正式收盤數據
         ├── 比對盤中預測結果
         ├── 計算預測準確率
         └── 更新每日績效報表
```

#### 關鍵實踐建議

1. **永豐金開戶是第一步**：Shioaji 是免費方案中唯一能提供即時 Tick + 五檔的來源，務必優先開戶
2. **善用 WebSocket 而非輪詢**：WebSocket 推送比 REST 輪詢更即時、更省資源
3. **盤前預載歷史數據**：避免盤中頻繁查詢歷史 API，降低延遲風險
4. **本地計算優先**：9 大訊號全部在本地計算，減少外部 API 依賴
5. **分層快取降低 I/O**：即時數據放記憶體、盤後才寫入資料庫
6. **異步架構（asyncio）**：WebSocket 接收與訊號計算使用異步模式，避免阻塞
7. **監控連線健康**：Shioaji 盤中偶爾斷線，務必實作自動重連

---

## 附錄：參考資源

| 資源 | 網址 |
|------|------|
| TWSE OpenAPI | https://openapi.twse.com.tw |
| TPEX OpenAPI | https://www.tpex.org.tw/openapi/ |
| Fugle Developer Docs | https://developer.fugle.tw |
| Fugle 台股行情方案價格 | https://developer.fugle.tw/docs/pricing/ |
| Shioaji 官方文件 | https://sinotrade.github.io |
| Shioaji 行情訂閱教學 | https://eyetrading.github.io/tutor/sj_api_data/ |
| 永豐金即時內外盤實作 | https://www.pj-worklife.com.tw/shioaji-api-real-time/ |
| yfinance 台股使用 | https://www.pj-worklife.com.tw/yfinance-api/ |
| twstock GitHub | https://github.com/mlouielu/twstock |
