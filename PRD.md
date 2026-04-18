# 台股實驗預測及模擬倉 — 產品需求與架構規劃書 (PRD)

> **版本**：v1.0
> **日期**：2026-04-09
> **團隊**：台股分析師 / 股票資訊收集師 / 後端工程師 / 前端工程師 / 測試工程師

---

## 目錄

1. [專案概述與目標](#1-專案概述與目標)
2. [核心功能需求](#2-核心功能需求)
3. [9大訊號加權評分系統](#3-9大訊號加權評分系統)
4. [綜合判斷與信心值](#4-綜合判斷與信心值)
5. [AI 推論整合（Groq API）](#5-ai-推論整合groq-api)
6. [62秒自動驗證機制](#6-62秒自動驗證機制)
7. [數據來源與收集架構](#7-數據來源與收集架構)
8. [後端系統架構](#8-後端系統架構)
9. [RESTful API 設計](#9-restful-api-設計)
10. [WebSocket 即時推送](#10-websocket-即時推送)
11. [資料庫 Schema 設計](#11-資料庫-schema-設計)
12. [模擬倉功能設計](#12-模擬倉功能設計)
13. [前端 UI/UX 設計](#13-前端-uiux-設計)
14. [技術棧總覽](#14-技術棧總覽)
15. [測試策略與品質保證](#15-測試策略與品質保證)
16. [開發階段與里程碑](#16-開發階段與里程碑)
17. [風險評估與對策](#17-風險評估與對策)

---

## 1. 專案概述與目標

### 1.1 專案簡介

本系統為一個**個人使用的台股即時分析與模擬交易平台**，核心能力為：

- 輸入股票代碼後，自動從多面向分析未來短線走勢的可能性
- 透過 **9 大訊號加權評分系統**（-100 ~ +100）即時推論漲跌
- 顯示 📈 **看漲** / 📉 **看跌** / ⚖️ **中性** + 信心值 %
- 整合 **Groq API（Llama 3.3）** 生成 80 字以內繁體中文推論說明（可開關）
- **62 秒後自動驗證**預測是否正確，並持續記錄成功率
- 提供**模擬倉**功能，可模擬買賣與追蹤損益

### 1.2 目標使用者

個人開發者 / 台股投資研究者（單機部署）

### 1.3 非目標

- 本系統**不構成投資建議**，僅為實驗性分析工具
- 不提供真實下單功能
- 不支援多用戶同時使用（初版）

---

## 2. 核心功能需求

### 2.1 即時推論漲跌

每次觸發推演流程：

```
股票代碼輸入
    │
    ▼
9大訊號即時計算（加權評分 -100 ~ +100）
    │
    ▼
綜合判斷：📈 看漲 / 📉 看跌 / ⚖️ 中性 + 信心值%
    │
    ├──(AI 開啟)──► Groq API → 80字繁體中文推論說明
    │
    ▼
前端大字顯示結果
    │
    ▼
62秒後自動驗證 → 記錄成功/失敗 → 更新成功率
```

### 2.2 9大訊號一覽

| # | 訊號名稱 | 權重 | 類別 | 更新頻率 |
|---|---------|------|------|---------|
| 1 | 外盤比率 | 15% | 量能方向 | 逐筆 |
| 2 | 五檔委買 vs 委賣壓力 | 12% | 掛單意圖 | 即時 |
| 3 | 最近10筆成交明細方向 | 10% | 短線動量 | 逐筆 |
| 4 | 日內高低位置 | 8% | 價格結構 | 逐筆 |
| 5 | 即時漲跌幅動能 | 10% | 動能趨勢 | 逐筆 |
| 6 | RSI（含超買/超賣反轉） | 12% | 技術指標 | 每分鐘 |
| 7 | MACD OSC 正負 | 13% | 趨勢確認 | 每分鐘 |
| 8 | KD 黃金/死亡交叉 | 12% | 交叉訊號 | 每分鐘 |
| 9 | 盤中走勢加速度 | 8% | 加速度 | 逐筆 |
| | **合計** | **100%** | | |

### 2.3 模擬倉功能

- 預設初始資金 100 萬 NT$
- 支援買入 / 賣出操作
- 手續費 0.1425%（6 折）、交易稅 0.3%（賣出）
- 即時計算未實現損益、已實現損益
- 每日資產快照與歷史損益追蹤

---

## 3. 9大訊號加權評分系統

每個訊號獨立計算分數，範圍 **-100 ~ +100**（正值看漲、負值看跌、0 中性）。

### 3.1 外盤比率（權重：15%）

```
外盤比率 = 外盤成交量 / (外盤成交量 + 內盤成交量) × 100%

評分轉換：
  ≥ 75% → +80 ~ +100（強烈看漲）
  60~74% → +30 ~ +80
  55~59% → +10 ~ +30
  45~54% → -10 ~ +10（中性區）
  40~44% → -10 ~ -30
  25~39% → -30 ~ -80
  ≤ 25% → -80 ~ -100（強烈看跌）
```

### 3.2 五檔委買 vs 委賣壓力（權重：12%）

```
壓力比 = (委買總量 - 委賣總量) / (委買總量 + 委賣總量)
範圍：-1.0 ~ +1.0

評分轉換：
  ≥ 0.5 → +80 ~ +100
  0.2~0.49 → +30 ~ +80
  0.05~0.19 → +5 ~ +30
  ±0.04 → -5 ~ +5（中性區）
  -0.19~-0.05 → -5 ~ -30
  -0.49~-0.2 → -30 ~ -80
  ≤ -0.5 → -80 ~ -100
```

**注意**：委買/委賣總量任一方 < 50 張時可信度降低，權重減半。

### 3.3 最近10筆成交明細方向（權重：10%）

```
方向比 = (外盤筆數 - 內盤筆數) / 10
加權方向比 = (加權外盤量 - 加權內盤量) / (加權外盤量 + 加權內盤量)
最終方向值 = 0.4 × 方向比 + 0.6 × 加權方向比
score = clamp(最終方向值 × 100, -100, +100)
```

### 3.4 日內高低位置（權重：8%）

```
位置百分比 = (目前價 - 最低價) / (最高價 - 最低價) × 100%

非線性評分：≥90% → +70~+100 / 70~89% → +20~+70 / 30~69% → ±20 / 10~29% → -20~-70 / <10% → -70~-100

振幅修正：振幅 < 0.3% 時分數衰減至 30%、< 0.8% 衰減至 60%
```

### 3.5 即時漲跌幅動能（權重：10%）

```
漲跌幅 = (目前價 - 昨收價) / 昨收價 × 100%
動能變化 = 漲跌幅 - 前一分鐘漲跌幅

score = clamp(基礎分 + 動能分, -100, +100)
  基礎分：按漲跌幅分段計算（±5%=±80, ±2%=±40~80, ±0.5%=±10~40）
  動能分：clamp(動能變化 × 100, -20, +20)
```

### 3.6 RSI（權重：12%，含反轉邏輯）

使用 14 期 RSI（盤中 1 分 K 線）：

```
RSI > 80 → score = -50 ~ -100（超買，預期回檔）
RSI 65~80 → score = +30 ~ +50
RSI 55~64 → score = +10 ~ +30
RSI 45~54 → score = -10 ~ +10（中性）
RSI 35~44 → score = -10 ~ -30
RSI 20~34 → score = -30 ~ -50
RSI < 20 → score = +50 ~ +100（超賣，預期反彈）
```

**反轉邏輯**：RSI > 80 評為負值（預期回檔）、RSI < 20 評為正值（預期反彈），符合均值回歸的短線交易邏輯。

### 3.7 MACD OSC 正負（權重：13%）

```
OSC = DIF - Signal（EMA12, EMA26, Signal=EMA9(DIF)）
正規化：normalized_osc = OSC / max(|OSC| over 60 bars)

score = clamp(基礎分 + 方向修正 + 零軸加分, -100, +100)
  基礎分 = normalized_osc × 70
  方向修正：OSC增大+正=+15 / OSC減小+負=-15 / 負轉收斂=+10 / 正轉收斂=-10
  零軸穿越：負→正=+15 / 正→負=-15
```

### 3.8 KD 黃金/死亡交叉（權重：12%）

```
KD(9, 3, 3)：RSV → K = 2/3×K_prev + 1/3×RSV → D = 2/3×D_prev + 1/3×K

score = clamp(交叉分 + 位置加分 + 趨勢分, -100, +100)
  黃金交叉=+50 / 死亡交叉=-50 / K>D=+15 / K<D=-15
  低檔(<30)黃金交叉加分+30 / 高檔(>70)死亡交叉加分-30
  趨勢分 = clamp((K_curr - K_prev) × 2, -20, +20)
```

### 3.9 盤中走勢加速度（權重：8%）

```
v1 = (price[t-1] - price[t-2]) / price[t-2] × 100%
v2 = (price[t] - price[t-1]) / price[t-1] × 100%
acceleration = v2 - v1

score = clamp(基礎分 + 一致性加分, -100, +100)
  基礎分 = clamp(acceleration / 0.2, -1, +1) × 60
  上漲加速=+20 / 下跌加速=-20 / 上漲減速=-10 / 下跌減速=+10
```

---

## 4. 綜合判斷與信心值

### 4.1 加權總分

```
加權總分 = Σ(訊號i的分數 × 訊號i的權重)
```

### 4.2 方向判斷

| 加權總分 | 判斷 | 顯示 |
|---------|------|------|
| +40 ~ +100 | 強烈看漲 | 📈 看漲 |
| +20 ~ +39 | 看漲 | 📈 看漲 |
| +5 ~ +19 | 微幅看漲 | 📈 看漲 |
| -4 ~ +4 | 中性 | ⚖️ 中性 |
| -19 ~ -5 | 微幅看跌 | 📉 看跌 |
| -39 ~ -20 | 看跌 | 📉 看跌 |
| -100 ~ -40 | 強烈看跌 | 📉 看跌 |

### 4.3 信心值計算

```
方向一致性 = 同方向訊號數 / 9 × 100%
強度因子 = |加權總分| / 100 × 100%
離散度因子 = max(0, 1 - 分數標準差 / 80) × 100%

信心值 = 方向一致性 × 0.45 + 強度因子 × 0.30 + 離散度因子 × 0.25
信心值 = clamp(信心值, 10%, 95%)
```

### 4.4 訊號衝突處理

- **量能 vs 技術指標矛盾**：外盤強烈看漲但 RSI 超買反轉時，短線量能主導，降低 RSI 權重
- **KD vs MACD 交叉矛盾**：兩者分數各衰減 40%，信心值下修 30%
- **位置 vs 動能矛盾**：動能優先於位置，信心值小幅下修 10%

---

## 5. AI 推論整合（Groq API）

### 5.1 架構

- **模型**：Llama 3.3 70B Versatile（via Groq API）
- **開關**：使用者可在前端一鍵開關 AI 推論
- **快取**：同評分區間（四捨五入到 5 分）5 分鐘內不重複呼叫
- **降級**：連續 5 次失敗自動關閉，10 分鐘後自動嘗試恢復

### 5.2 Prompt 設計

**System Prompt**：
```
你是一位專業的台灣股票盤中分析師。你將收到一支股票的即時九大訊號數據，
每個訊號已經計算出 -100 到 +100 的分數及加權總分。
你的工作是：
1. 根據數據判斷未來 62 秒的短線走勢方向
2. 用繁體中文輸出一段精確扼要的推論說明（限80字以內）
3. 重點說明主要支撐/壓力的訊號依據
4. 如有訊號衝突，指出關鍵矛盾
語氣專業、簡潔、不使用emoji。直接切入重點，不要開場白。
```

**送入 AI 的 JSON 結構**：包含 stock_code、current_price、change_pct、9 個訊號的 value/score/description、weighted_total_score、direction、confidence、signal_agreement。

**推論輸出範例**：
> 台積電短線看漲，外盤主力持續攻擊且MACD柱體放大，8項訊號同向偏多。加權總分36.8，信心72%，日內高檔位置為唯一隱憂，留意追高風險。

---

## 6. 62秒自動驗證機制

### 6.1 驗證規則

推論完成後 62 秒自動擷取最新成交價比對：

| 推論方向 | 價格變化 | 判定 |
|---------|---------|------|
| 看漲（總分 ≥ +5） | 變化率 > +0.02% | 成功 |
| 看漲（總分 ≥ +5） | 變化率 < -0.02% | 失敗 |
| 看漲（總分 ≥ +5） | ±0.02% 以內 | 平盤（不計入） |
| 看跌（總分 ≤ -5） | 變化率 < -0.02% | 成功 |
| 看跌（總分 ≤ -5） | 變化率 > +0.02% | 失敗 |
| 中性（-4 ≤ 總分 ≤ +4） | ±0.05% 以內 | 成功 |

### 6.2 成功率統計維度

| 維度 | 說明 |
|------|------|
| 整體成功率 | 成功次數 / 有效推論次數 |
| 依方向 | 看漲/看跌/中性 各自的成功率 |
| 依信心值 | 高(>70%)/中(40-70%)/低(<40%) |
| 依時段 | 開盤(09:00-09:30)/盤中(09:30-12:00)/尾盤(12:00-13:30) |
| 依個股 | 各股票的個別成功率 |
| 滾動統計 | 最近 20/50/100 次 |

### 6.3 權重持續優化

- 累積 50 次有效推論後啟動第一次優化
- 每 100 次更新一次權重
- 使用正確率加權法：`新權重 = 0.7×原權重 + 0.3×(訊號正確率/Σ正確率)`
- 權重範圍限制：3% ~ 25%

---

## 7. 數據來源與收集架構

### 7.1 推薦數據源組合（完全免費方案）

```
第一層（即時核心）：永豐金 Shioaji API（免費，需開戶）
  ├── WebSocket Tick 推送（內外盤、成交明細）
  ├── WebSocket BidAsk 推送（五檔委買委賣）
  └── 即時報價

第二層（即時備用）：Fugle API 基本方案（免費，5檔）
  └── REST API / WebSocket 備用通道

第三層（歷史數據）：yfinance + TWSE/TPEX OpenAPI（免費）
  ├── 歷史日K/分鐘K（技術指標計算）
  └── 每日收盤行情

月成本：NT$0
```

### 7.2 各訊號數據取得方式

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

### 7.3 數據更新頻率

| 層級 | 頻率 | 數據 | 觸發方式 |
|------|------|------|---------|
| 即時層 | ~100ms | tick、五檔 | WebSocket push |
| 秒級層 | 1-3 秒 | 外盤比率、漲跌幅、加速度 | tick 驅動 |
| 分鐘層 | 每分鐘 | RSI、MACD、KD | 分鐘K完成 |
| 盤前載入 | 08:30 | 歷史K線、昨收價 | 排程 |
| 盤後批次 | 14:30 | 收盤數據、驗證結果 | 排程 |

### 7.4 三層快取策略

| 快取層 | 儲存 | 數據 | 存活時間 |
|--------|------|------|---------|
| L1 即時 | Python dict/deque | 最新 tick、五檔、訊號值 | 即時覆蓋 |
| L2 短期 | Python 記憶體 | 分鐘K、近期訊號歷史 | 1 交易日 |
| L3 持久 | SQLite | 日K、歷史訊號、預測記錄 | 永久 |

### 7.5 異常處理與降級

```
Shioaji 斷線 → Fugle WebSocket 備用 → TWSE mis 輪詢 → 暫停訊號計算
WebSocket 斷線 → 指數退避重連（1s → 2s → 4s → ... → 60s max）
心跳超時 30s → 主動重連
數據異常（超出漲跌停）→ 標記並跳過
```

---

## 8. 後端系統架構

### 8.1 技術棧

```
語言：       Python 3.11+
框架：       FastAPI 0.110+
ASGI：       Uvicorn
ORM：        SQLAlchemy 2.0 (async)
資料庫：     SQLite (WAL mode) → 可遷移 PostgreSQL
快取：       cachetools (TTLCache)
排程：       APScheduler
WebSocket：  FastAPI 內建
金融計算：   pandas, numpy, TA-Lib, pandas-ta
AI 整合：    Groq Python SDK
HTTP 客戶端：httpx (async)
驗證：       Pydantic v2
日誌：       loguru
```

### 8.2 系統架構圖

```
┌─────────────────────────────────────────────────────────┐
│                   前端 (Next.js)                          │
│               HTTP REST ◄─────────► WebSocket            │
└────────┬──────────────────────────────┬──────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────────────────────────────────────────────┐
│                    API 閘道層                              │
│     REST Router  │  WS Manager  │  Middleware (CORS等)    │
└────────┬──────────────────────────────┬──────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────────────────────────────────────────────┐
│                   業務邏輯層                               │
│  訊號評分引擎  │  AI分析服務  │  預測驗證  │  模擬倉  │  統計  │
└────────┬──────────────────────────────┬──────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────────────────────────────────────────────┐
│                     數據層                                 │
│     SQLite DB  │  記憶體快取  │  外部API (TWSE/Groq等)    │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│                    排程層                                  │
│   即時行情(5秒)  │  預測驗證(62秒)  │  盤後整理(每日14:00) │
└─────────────────────────────────────────────────────────┘
```

### 8.3 專案目錄結構

```
backend/
├── main.py                     # FastAPI 入口
├── config.py                   # 組態管理
├── database.py                 # 資料庫連線
├── api/v1/                     # API 路由
│   ├── stocks.py               # 股票查詢
│   ├── analysis.py             # 即時分析
│   ├── portfolio.py            # 模擬倉
│   ├── predictions.py          # 預測記錄
│   └── stats.py                # 統計數據
├── services/                   # 業務邏輯
│   ├── signal_engine.py        # 9大訊號評分引擎
│   ├── ai_analysis.py          # Groq AI 服務
│   ├── quote_service.py        # 行情服務
│   ├── portfolio_service.py    # 模擬倉服務
│   ├── prediction_service.py   # 預測驗證服務
│   └── stats_service.py        # 統計服務
├── models/                     # 資料模型
│   ├── database_models.py      # SQLAlchemy ORM
│   └── schemas.py              # Pydantic schemas
├── core/                       # 核心元件
│   ├── cache.py, scheduler.py, ws_manager.py, exceptions.py
├── prompts/                    # AI Prompt 模板
└── data/twstock.db             # SQLite 資料庫
```

### 8.4 訊號評分引擎設計

```python
class BaseSignal(ABC):
    @abstractmethod
    async def calculate(self, stock_id, market_data) -> SignalResult: ...

class SignalEngine:
    signals = [OuterRatioSignal(), BidAskSignal(), TickDirectionSignal(), ...]

    async def evaluate(self, stock_id) -> CompositeScore:
        market_data = await self._get_market_data(stock_id)
        results = await asyncio.gather(*[s.calculate(stock_id, market_data) for s in self.signals])
        total_score = sum(r.weighted_score for r in results)
        direction = self._determine_direction(total_score)
        confidence = self._calculate_confidence(results)
        return CompositeScore(total_score, direction, confidence, results)
```

---

## 9. RESTful API 設計

**Base URL**: `http://localhost:8000/api/v1`

### 9.1 股票查詢

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/stocks/search?q=台積` | 搜尋股票 |
| GET | `/stocks/{stock_id}/quote` | 即時報價 |
| GET | `/stocks/{stock_id}/history` | 歷史K線 |

### 9.2 即時分析

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/analysis/{stock_id}/signals` | 9大訊號評分 |
| GET | `/analysis/{stock_id}/composite` | 綜合分析（訊號+AI） |
| POST | `/analysis/{stock_id}/predict` | 產生漲跌預測 |
| POST | `/analysis/ai/toggle` | 切換 AI 開關 |

### 9.3 模擬倉

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/portfolio/account` | 帳戶總覽 |
| GET | `/portfolio/positions` | 所有持倉 |
| POST | `/portfolio/buy` | 模擬買入 |
| POST | `/portfolio/sell` | 模擬賣出 |
| GET | `/portfolio/trades` | 交易記錄 |
| POST | `/portfolio/reset` | 重置模擬倉 |

### 9.4 預測與統計

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/predictions/stats` | 預測統計 |
| GET | `/predictions/latest` | 最新預測 |
| GET | `/stats/dashboard` | 儀表板總覽 |
| GET | `/stats/signals/accuracy` | 各訊號準確度 |

### 9.5 統一回應格式

```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2026-04-09T10:30:00+08:00"
}
```

---

## 10. WebSocket 即時推送

### 10.1 連線端點

`ws://localhost:8000/ws`

### 10.2 客戶端 → 伺服器

```json
{"action": "subscribe", "stock_id": "2330"}
{"action": "unsubscribe", "stock_id": "2330"}
{"action": "ping"}
```

### 10.3 伺服器 → 客戶端（5 種訊息類型）

| 類型 | 說明 |
|------|------|
| `quote_update` | 即時報價更新 |
| `signal_update` | 訊號評分更新（含 total_score、direction、confidence） |
| `prediction_created` | 新預測產生 |
| `prediction_verified` | 預測驗證結果（含 is_correct） |
| `pong` | 心跳回應 |

### 10.4 心跳機制

- 每 30 秒 ping
- 90 秒無回應視為斷線，主動清理連線

---

## 11. 資料庫 Schema 設計

### 11.1 資料表總覽（7 張表）

```
user_accounts ──1:N──► positions
              ──1:N──► trade_records
              ──1:N──► asset_snapshots

prediction_records（全域，不綁定 user）
stock_daily_data（歷史K線快取）
app_settings（應用設定）
```

### 11.2 核心資料表

**user_accounts**（使用者帳戶）
```sql
CREATE TABLE user_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL DEFAULT 'default' UNIQUE,
    initial_capital REAL NOT NULL DEFAULT 1000000,
    current_cash REAL NOT NULL DEFAULT 1000000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**positions**（持倉部位）
```sql
CREATE TABLE positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user_accounts(id),
    stock_id TEXT NOT NULL,
    stock_name TEXT NOT NULL,
    shares INTEGER NOT NULL DEFAULT 0,
    avg_cost REAL NOT NULL DEFAULT 0,
    total_cost REAL NOT NULL DEFAULT 0,
    UNIQUE(user_id, stock_id)
);
```

**trade_records**（交易記錄）
```sql
CREATE TABLE trade_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user_accounts(id),
    stock_id TEXT NOT NULL,
    stock_name TEXT NOT NULL,
    trade_type TEXT NOT NULL CHECK(trade_type IN ('buy','sell')),
    shares INTEGER NOT NULL,
    price REAL NOT NULL,
    amount REAL NOT NULL,
    fee REAL NOT NULL DEFAULT 0,
    tax REAL NOT NULL DEFAULT 0,
    net_amount REAL NOT NULL,
    realized_pnl REAL,
    traded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**prediction_records**（預測記錄）
```sql
CREATE TABLE prediction_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    stock_name TEXT NOT NULL,
    predicted_at TIMESTAMP NOT NULL,
    predicted_direction TEXT NOT NULL CHECK(predicted_direction IN ('up','down','flat')),
    predicted_confidence REAL NOT NULL,
    price_at_prediction REAL NOT NULL,
    signal_score REAL,
    ai_involved BOOLEAN NOT NULL DEFAULT FALSE,
    verify_at TIMESTAMP,
    price_at_verify REAL,
    actual_direction TEXT,
    price_change_pct REAL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','verified','expired')),
    is_correct BOOLEAN
);
```

**asset_snapshots**（每日資產快照）、**stock_daily_data**（日K快取）、**app_settings**（系統設定）。

---

## 12. 模擬倉功能設計

### 12.1 交易成本常數

| 項目 | 值 |
|------|------|
| 手續費率 | 0.1425% |
| 手續費折扣 | 6 折（0.6） |
| 最低手續費 | 20 元 |
| 交易稅（賣出） | 0.3% |
| 手續費取整 | 無條件捨去 |
| 交易稅取整 | 無條件捨去 |

### 12.2 買入流程

```
成交金額 = 股價 × 股數
手續費 = max(成交金額 × 0.1425% × 0.6, 20)（無條件捨去）
買入總成本 = 成交金額 + 手續費
→ 檢查餘額 → 扣款 → 更新/建立持倉（平均成本法）→ 記錄交易
```

### 12.3 賣出流程

```
成交金額 = 股價 × 股數
手續費 = max(成交金額 × 0.1425% × 0.6, 20)（無條件捨去）
交易稅 = 成交金額 × 0.3%（無條件捨去）
賣出淨收入 = 成交金額 - 手續費 - 交易稅
已實現損益 = 賣出淨收入 - (平均成本 × 股數)
→ 入帳 → 更新/刪除持倉 → 記錄交易
```

### 12.4 範例

```
買入台積電 1 張 @1000 元：
  金額：1,000 × 1000 = 1,000,000
  手續費：1,000,000 × 0.001425 × 0.6 = 855
  總成本：1,000,855

賣出 @1050 元：
  金額：1,050,000
  手續費：897
  交易稅：3,150
  淨收入：1,045,953
  已實現損益：+45,098
```

---

## 13. 前端 UI/UX 設計

### 13.1 技術棧

```
框架：       Next.js 14+ (App Router, TypeScript)
UI 元件：    Shadcn/ui + Radix UI
樣式：       Tailwind CSS 3.4+
K 線圖：     lightweight-charts (TradingView)
統計圖表：   ECharts 5
狀態管理：   Zustand
伺服器快取：  TanStack Query v5
WebSocket：  原生 + 自訂 hook
動畫：       Framer Motion
```

### 13.2 頁面架構

```
/dashboard          儀表板（總覽）
/stock/[code]       個股分析頁
/portfolio          模擬倉管理
/portfolio/history  交易歷史
/statistics         歷史記錄與統計
/settings           設定頁
```

### 13.3 核心視覺 — 即時推論顯示區

```
┌───────────────────────────────────────┐
│         ╭──────────╮                  │
│         │   78%    │  ← 環形進度條    │
│         │  信心值   │                  │
│         ╰──────────╯                  │
│                                       │
│        📈  看    漲                    │
│   (72px 粗體，紅色，帶入場動畫)          │
│                                       │
│   2330 台積電 | NT$890 ▲+1.71%        │
└───────────────────────────────────────┘
```

**配色（台股慣例：紅漲綠跌）**：

| 狀態 | 文字色 | 背景色 |
|------|--------|--------|
| 📈 看漲 | `text-red-600` | `bg-red-50` |
| 📉 看跌 | `text-green-600` | `bg-green-50` |
| ⚖️ 中性 | `text-yellow-600` | `bg-yellow-50` |

### 13.4 9大訊號儀表板

- 3×3 網格卡片，每個訊號顯示：名稱、數值、方向、權重、一句話解讀
- ECharts 雷達圖呈現整體訊號強度
- 即時更新動畫（countUp 數字滾動、脈衝動畫）

### 13.5 AI 推論區塊

- 打字機效果逐字出現（30ms/字）
- ON/OFF 開關按鈕（藍紫漸層）
- 載入中：三圓點脈動 + 骨架屏

### 13.6 K 線走勢圖

- lightweight-charts 蠟燭圖（紅漲綠跌）
- 可切換 RSI / MACD / KD 子圖
- 模擬倉買賣點標記（紅色向上箭頭=買、綠色向下箭頭=賣）

### 13.7 模擬倉介面

- 持倉列表（股票、數量、成本、現價、損益、損益%、操作）
- 買入/賣出面板（含手續費、交易稅即時計算）
- 4 張統計卡片（總資產、持倉市值、可用現金、總損益）

### 13.8 響應式設計

| 裝置 | 寬度 | 佈局策略 |
|------|------|---------|
| 桌面 | ≥1024px | 側邊欄固定 + 2-3 欄 Grid |
| 平板 | 768-1023px | 抽屜式側邊欄 + 底部 Tab |
| 手機 | <768px | 推論結果置頂 + Tab 切換內容 + 底部 Sheet 交易 |

### 13.9 深色/淺色主題

- CSS Variables 切換
- 台股專用色彩變數：`--stock-up`(紅)、`--stock-down`(綠)、`--stock-flat`(黃)
- 圖表自動適配主題色

### 13.10 前端目錄結構

```
src/
├── app/              # Next.js 頁面
├── components/       # 元件（ui/ prediction/ signals/ chart/ ai/ portfolio/ statistics/ search/）
├── hooks/            # 自訂 Hooks (useStockWebSocket, useStockData, usePrediction...)
├── stores/           # Zustand (useStockStore, usePortfolioStore, useUIStore)
├── services/         # API 服務層 (stockService, predictionService, portfolioService)
├── lib/              # 工具函數 (formatters, validators, constants)
├── types/            # TypeScript 型別定義
└── styles/           # 全域 CSS + 圖表主題
```

---

## 14. 技術棧總覽

| 層級 | 技術 |
|------|------|
| **前端框架** | Next.js 14+ (TypeScript) |
| **UI 元件** | Shadcn/ui + Tailwind CSS 3.4 |
| **圖表** | lightweight-charts (K線) + ECharts 5 (統計) |
| **狀態管理** | Zustand + TanStack Query v5 |
| **後端框架** | Python FastAPI |
| **資料庫** | SQLite (WAL) → PostgreSQL |
| **ORM** | SQLAlchemy 2.0 (async) |
| **快取** | cachetools TTLCache |
| **排程** | APScheduler |
| **AI** | Groq API (Llama 3.3 70B) |
| **即時通訊** | WebSocket (FastAPI 內建) |
| **金融計算** | pandas, numpy, TA-Lib |
| **即時數據** | 永豐金 Shioaji API (WebSocket) |
| **歷史數據** | yfinance + TWSE OpenAPI |
| **測試** | pytest + Vitest + Playwright |
| **CI/CD** | GitHub Actions |

---

## 15. 測試策略與品質保證

### 15.1 測試金字塔

```
     /   E2E    \        10% (~20 案例)     Playwright
    /  整合測試   \       25% (~60 案例)     pytest + MSW
   / 單元測試      \     65% (~200 案例)    pytest + Vitest
  ──────────────────
```

### 15.2 覆蓋率目標

| 模組 | 行覆蓋率 | 分支覆蓋率 | 優先級 |
|------|---------|-----------|--------|
| 訊號計算模組 | ≥ 95% | ≥ 90% | P0 |
| 加權評分系統 | ≥ 95% | ≥ 90% | P0 |
| 模擬倉功能 | ≥ 90% | ≥ 85% | P0 |
| API 路由層 | ≥ 80% | ≥ 75% | P1 |
| 前端元件 | ≥ 75% | ≥ 70% | P2 |
| **全專案整體** | **≥ 85%** | **≥ 80%** | — |

### 15.3 單元測試重點

- **9大訊號**：每個訊號的正常值、邊界值（0%/100%、漲停/跌停）、異常數據（None、負值、零分母）
- **加權評分**：權重加總=100%、全看漲/全看跌/矛盾/缺失訊號處理、Property-based 分數範圍檢查
- **模擬倉**：買入餘額不足、賣出持倉不足、手續費最低 20 元、交易稅僅賣出、平均成本計算

### 15.4 效能目標

| 指標 | 目標 |
|------|------|
| 單一訊號計算 | < 10ms |
| 9大訊號完整計算 | < 100ms |
| WebSocket 推送延遲 | < 50ms |
| API P95 回應 | < 200ms |
| 首屏載入 (LCP) | < 2.5s |

### 15.5 數據驗證

- **歷史回測**：用歷史數據跑預測，比對實際走勢，準確率需顯著 > 50%
- **統計檢驗**：二項檢定（p < 0.05）、Pearson 相關、混淆矩陣分析

### 15.6 CI/CD

```
push/PR → 單元測試 → 整合測試 → E2E 測試 → 覆蓋率檢查 → 部署
每週排程 → 效能回歸測試 + 回測驗證
```

---

## 16. 開發階段與里程碑

### Phase 1：基礎架構（第 1-2 週）

- [ ] 後端 FastAPI 專案初始化
- [ ] SQLite 資料庫 Schema 建立
- [ ] 前端 Next.js 專案初始化
- [ ] 基本頁面路由與佈局

### Phase 2：數據層（第 2-3 週）

- [ ] Shioaji API 連接與 Tick/BidAsk 訂閱
- [ ] 歷史數據載入（yfinance + TWSE）
- [ ] 數據快取層實作
- [ ] 分鐘K聚合模組

### Phase 3：訊號引擎（第 3-5 週）

- [ ] 9大訊號計算模組實作
- [ ] 加權評分引擎
- [ ] 信心值計算
- [ ] 訊號衝突處理邏輯
- [ ] 單元測試（P0 模組 ≥ 95%）

### Phase 4：即時推送（第 5-6 週）

- [ ] WebSocket 連線管理
- [ ] 即時報價推送
- [ ] 訊號評分推送
- [ ] 前端 WebSocket 連接

### Phase 5：前端核心 UI（第 6-8 週）

- [ ] 即時推論大字顯示（環形進度條+動畫）
- [ ] 9大訊號儀表板（卡片+雷達圖）
- [ ] K線走勢圖整合
- [ ] 股票搜尋功能

### Phase 6：AI 推論（第 8-9 週）

- [ ] Groq API 整合
- [ ] Prompt 管理與快取
- [ ] AI 開關機制
- [ ] 降級策略
- [ ] AI 推論 UI 元件

### Phase 7：自動驗證（第 9-10 週）

- [ ] 62 秒排程驗證
- [ ] 預測記錄與比對
- [ ] 成功率統計模組
- [ ] 驗證結果推送
- [ ] 統計圖表前端

### Phase 8：模擬倉（第 10-12 週）

- [ ] 買入/賣出邏輯
- [ ] 損益計算（含手續費/稅）
- [ ] 持倉管理 UI
- [ ] 交易面板
- [ ] 資產快照與歷史

### Phase 9：完善與測試（第 12-14 週）

- [ ] 整合測試
- [ ] E2E 測試
- [ ] 效能優化
- [ ] 響應式適配
- [ ] 深色主題
- [ ] 權重自動優化機制

---

## 17. 風險評估與對策

### 17.1 數據來源風險

| 風險 | 影響 | 對策 |
|------|------|------|
| Shioaji API 斷線 | 無法取得即時數據 | 備用 Fugle + 自動重連 |
| yfinance 被封鎖 | 無法載入歷史數據 | 備用 TWSE OpenAPI + twstock |
| 數據延遲 > 5 秒 | 訊號失真 | 放棄本次推論，標記數據過期 |

### 17.2 訊號系統風險

| 風險 | 影響 | 對策 |
|------|------|------|
| 極端行情（漲跌停） | 訊號失效 | 偵測漲跌停→停止推論+警告 |
| 低流動性標的 | 樣本不足 | 日成交量 < 500 張→標記低可信度 |
| 開盤前 5 分鐘 | 指標不穩定 | 09:00-09:05 訊號權重降低 |
| 訊號長期失準 | 成功率下降 | 權重自動優化機制（每 100 次） |

### 17.3 技術風險

| 風險 | 影響 | 對策 |
|------|------|------|
| Groq API 不可用 | AI 推論中斷 | 自動降級→僅顯示訊號評分 |
| SQLite 效能瓶頸 | 查詢變慢 | 遷移至 PostgreSQL（SQLAlchemy ORM 無痛切換） |
| WebSocket 連線數過多 | 記憶體壓力 | Semaphore 控制 + 連線上限 |

### 17.4 合規風險

- 本系統**僅供學術研究與技術實驗**
- 所有分析結果**不構成投資建議**
- 需在 UI 顯著位置標示免責聲明

---

## 附錄 A：數據結構定義

```typescript
interface SignalScore {
  name: string;
  value: number;          // 原始指標值
  score: number;          // -100 ~ +100
  weight: number;         // 0.0 ~ 1.0
  description: string;    // 繁體中文簡述
  reliability: number;    // 0.0 ~ 1.0（可信度）
}

interface AnalysisResult {
  stockCode: string;
  stockName: string;
  timestamp: string;
  currentPrice: number;
  changePct: number;
  signals: SignalScore[];
  weightedTotalScore: number;  // -100 ~ +100
  direction: '強烈看漲' | '看漲' | '微幅看漲' | '中性' | '微幅看跌' | '看跌' | '強烈看跌';
  confidence: number;     // 10 ~ 95 (%)
  signalAgreement: string;
  aiReasoning: string;    // 80字推論
}

interface VerificationResult {
  analysisTimestamp: string;
  verifyTimestamp: string;
  predictedDirection: string;
  priceAtPrediction: number;
  priceAtVerify: number;
  changePct: number;
  result: '成功' | '失敗' | '平盤';
}

interface StatisticsRecord {
  totalPredictions: number;
  successCount: number;
  failCount: number;
  flatCount: number;
  successRate: number;
  byDirection: { bullish, bearish, neutral };
  byConfidence: { high, medium, low };
  byPeriod: { opening, midday, closing };
  rolling20: number;
  rolling50: number;
  rolling100: number;
}
```

## 附錄 B：環境變數

```env
# 應用程式
APP_HOST=0.0.0.0
APP_PORT=8000

# 資料庫
DATABASE_URL=sqlite+aiosqlite:///./data/twstock.db

# Groq AI
GROQ_API_KEY=gsk_your_key
AI_ENABLED=true
AI_MODEL=llama-3.3-70b-versatile

# 排程
PREDICTION_INTERVAL=62
QUOTE_INTERVAL=5

# 模擬倉
INITIAL_CAPITAL=1000000
FEE_DISCOUNT=0.6
```

## 附錄 C：參考資源

| 資源 | 網址 |
|------|------|
| Shioaji 官方文件 | https://sinotrade.github.io |
| Fugle Developer | https://developer.fugle.tw |
| TWSE OpenAPI | https://openapi.twse.com.tw |
| Groq API | https://console.groq.com |
| lightweight-charts | https://tradingview.github.io/lightweight-charts |
| Shadcn/ui | https://ui.shadcn.com |

---

> **免責聲明**：本系統僅供學術研究與技術實驗使用，所有分析結果不構成投資建議。股市有風險，投資需謹慎。使用者應自行承擔所有投資決策的風險與責任。
