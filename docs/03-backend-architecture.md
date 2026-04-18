# 03 - 後端架構設計文件

> 台股實驗預測及模擬倉 - Backend Architecture Design
> 版本：v1.0 | 最後更新：2026-04-09

---

## 目錄

1. [技術棧選型](#1-技術棧選型)
2. [系統架構圖](#2-系統架構圖)
3. [9大訊號評分引擎設計](#3-9大訊號評分引擎設計)
4. [Groq API（Llama 3.3）整合設計](#4-groq-apillama-33整合設計)
5. [62秒自動驗證機制](#5-62秒自動驗證機制)
6. [模擬倉功能設計](#6-模擬倉功能設計)
7. [RESTful API 端點設計](#7-restful-api-端點設計)
8. [WebSocket 推送設計](#8-websocket-推送設計)
9. [資料庫 Schema 設計](#9-資料庫-schema-設計)

---

## 1. 技術棧選型

### 1.1 後端框架：Python FastAPI

**選擇：FastAPI (Python 3.11+)**

| 評估維度 | FastAPI (Python) | Express/Fastify (Node.js) |
|---------|-----------------|--------------------------|
| 金融數據處理 | pandas/numpy 生態完整 | 需依賴第三方計算庫 |
| AI/ML 整合 | 原生支援，庫豐富 | 需透過子程序呼叫 |
| 非同步支援 | async/await 原生支援 | 原生事件驅動 |
| 型別安全 | Pydantic 強型別驗證 | 需額外 TypeScript |
| API 文件 | 自動生成 OpenAPI/Swagger | 需手動維護 |
| 技術指標計算 | TA-Lib、pandas-ta 成熟 | technicalindicators 較弱 |
| WebSocket | 內建支援 | socket.io 成熟 |
| 部署複雜度 | uvicorn 單指令 | pm2 單指令 |

**選擇 FastAPI 的核心理由：**
1. **金融計算生態**：pandas、numpy、TA-Lib 是金融數據分析的事實標準
2. **AI 整合**：與 Groq SDK（Python）無縫整合，Prompt 工程更靈活
3. **高效能非同步**：基於 Starlette，效能接近 Node.js
4. **自動 API 文件**：Pydantic model 自動產生完整 Swagger 文件
5. **型別安全**：Pydantic v2 在執行期嚴格驗證資料結構

### 1.2 資料庫選擇

**主資料庫：SQLite（開發/單機部署）+ 可遷移至 PostgreSQL**

| 資料庫 | 適用場景 | 本專案評估 |
|-------|---------|-----------|
| **SQLite** | 單機部署、個人專案、嵌入式 | **首選** - 零配置、單檔案、效能足夠 |
| PostgreSQL | 多用戶、高併發、複雜查詢 | 備選 - 未來規模化時遷移 |
| MongoDB | 非結構化數據、快速迭代 | 不適合 - 金融數據高度結構化 |

**設計策略：**
- 使用 SQLAlchemy ORM 作為資料庫抽象層，確保未來可無痛遷移
- SQLite WAL 模式啟用，支援讀寫並行
- 開發環境與生產環境共用同一套 ORM 模型

```python
# 資料庫引擎配置範例
from sqlalchemy import create_engine

# 開發/單機 - SQLite
DATABASE_URL = "sqlite+aiosqlite:///./data/twstock.db"

# 未來擴展 - PostgreSQL
# DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/twstock"
```

### 1.3 快取方案：記憶體快取為主

**選擇：本地記憶體快取（cachetools / lru_cache）**

| 方案 | 優點 | 缺點 | 適用性 |
|-----|------|------|-------|
| **記憶體快取** | 零依賴、極低延遲 | 重啟後消失 | **首選** |
| Redis | 持久化、分散式 | 需額外服務 | 未來擴展 |

**快取策略：**
- **股票行情快取**：TTL = 5 秒（盤中即時價），盤後 TTL = 1 小時
- **技術指標快取**：TTL = 60 秒（計算結果短暫快取）
- **AI 分析快取**：TTL = 300 秒（同一股票短期內不重複呼叫）
- **基本面數據快取**：TTL = 24 小時（每日更新一次）

```python
from cachetools import TTLCache
from functools import lru_cache

# 即時行情快取（最多500檔，5秒過期）
quote_cache = TTLCache(maxsize=500, ttl=5)

# AI 分析快取（最多100筆，5分鐘過期）
ai_analysis_cache = TTLCache(maxsize=100, ttl=300)
```

### 1.4 即時通訊：WebSocket

**選擇：FastAPI 內建 WebSocket**

| 方案 | 優點 | 缺點 |
|-----|------|------|
| **WebSocket** | 全雙工、低延遲、瀏覽器原生 | 連線管理較複雜 |
| SSE | 簡單、自動重連 | 單向、無法從客戶端推送 |

**選擇 WebSocket 的理由：**
- 股票數據需要伺服器主動推送（即時報價、訊號更新）
- 未來可能需要客戶端發送訂閱/取消訂閱指令
- FastAPI 原生支援 WebSocket 端點

### 1.5 任務排程：APScheduler

**選擇：APScheduler（Advanced Python Scheduler）**

| 方案 | 優點 | 缺點 | 適用性 |
|-----|------|------|-------|
| **APScheduler** | 輕量、嵌入式、支援多種觸發器 | 單程序 | **首選** |
| Celery | 分散式、高可靠 | 需 Redis/RabbitMQ | 過度設計 |
| node-cron | 簡單 | Node.js 專用 | 不適用 |

**排程任務規劃：**

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# 盤中每5秒更新即時報價（09:00-13:30）
scheduler.add_job(fetch_realtime_quotes, 'interval', seconds=5,
                  id='realtime_quotes')

# 每62秒執行預測驗證
scheduler.add_job(verify_predictions, 'interval', seconds=62,
                  id='prediction_verify')

# 盤後每日 14:00 計算日報
scheduler.add_job(generate_daily_report, 'cron', hour=14, minute=0,
                  id='daily_report')

# 每日 08:50 預載資料
scheduler.add_job(preload_market_data, 'cron', hour=8, minute=50,
                  id='preload_data')
```

### 1.6 完整技術棧總覽

```
┌─────────────────────────────────────────────────┐
│ 技術棧                                          │
├─────────────────────────────────────────────────┤
│ 語言        │ Python 3.11+                      │
│ 框架        │ FastAPI 0.110+                    │
│ ASGI 伺服器 │ Uvicorn                            │
│ ORM         │ SQLAlchemy 2.0 (async)            │
│ 資料庫      │ SQLite (WAL mode) / PostgreSQL    │
│ 快取        │ cachetools (TTLCache)             │
│ 排程        │ APScheduler                       │
│ WebSocket   │ FastAPI 內建                      │
│ 金融計算    │ pandas, numpy, TA-Lib, pandas-ta  │
│ AI 整合     │ Groq Python SDK                   │
│ HTTP 客戶端 │ httpx (async)                     │
│ 資料驗證    │ Pydantic v2                       │
│ 環境管理    │ python-dotenv                     │
│ 日誌        │ loguru                            │
│ 測試        │ pytest + pytest-asyncio           │
└─────────────────────────────────────────────────┘
```

---

## 2. 系統架構圖

### 2.1 整體分層架構

```
┌──────────────────────────────────────────────────────────────────┐
│                        前端展示層 (Frontend)                      │
│                    React + TailwindCSS + Chart.js                │
│         HTTP REST API ◄──────────────► WebSocket 即時推送         │
└──────────┬──────────────────────────────────┬────────────────────┘
           │                                  │
           ▼                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                         API 閘道層 (Gateway)                      │
│                                                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │ REST Router  │  │ WS Manager   │  │ Middleware             │  │
│  │ /api/v1/*   │  │ 連線管理      │  │ - CORS                │  │
│  │             │  │ 頻道訂閱      │  │ - Rate Limiting       │  │
│  │             │  │ 訊息廣播      │  │ - Error Handler       │  │
│  └─────┬───────┘  └──────┬───────┘  │ - Request Logging     │  │
│        │                 │          └────────────────────────┘  │
└────────┼─────────────────┼──────────────────────────────────────┘
         │                 │
         ▼                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                      業務邏輯層 (Service)                         │
│                                                                  │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │ 訊號評分引擎     │  │  AI 分析服務      │  │ 預測驗證服務   │  │
│  │ SignalEngine     │  │  AIAnalysisService│  │ VerifyService  │  │
│  │                 │  │                  │  │                │  │
│  │ - 9大訊號計算   │  │ - Groq API 呼叫  │  │ - 62s 排程驗證 │  │
│  │ - 加權評分合成  │  │ - Prompt 管理    │  │ - 記錄比對     │  │
│  │ - 即時更新推送  │  │ - 開關控制       │  │ - 成功率統計   │  │
│  └────────┬────────┘  └────────┬─────────┘  └───────┬────────┘  │
│           │                    │                     │           │
│  ┌────────┴────────┐  ┌───────┴──────────┐  ┌──────┴────────┐  │
│  │ 模擬倉服務      │  │  行情服務         │  │ 統計報表服務   │  │
│  │ PortfolioService│  │  QuoteService    │  │ StatsService  │  │
│  │                 │  │                  │  │               │  │
│  │ - 買賣下單      │  │ - 即時行情       │  │ - 勝率分析    │  │
│  │ - 損益計算      │  │ - 歷史K線        │  │ - 績效報表    │  │
│  │ - 資產快照      │  │ - 個股資訊       │  │ - 趨勢圖表    │  │
│  └────────┬────────┘  └───────┬──────────┘  └──────┬────────┘  │
└───────────┼───────────────────┼─────────────────────┼───────────┘
            │                   │                     │
            ▼                   ▼                     ▼
┌──────────────────────────────────────────────────────────────────┐
│                        數據層 (Data)                              │
│                                                                  │
│  ┌──────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │
│  │   SQLite DB   │  │  記憶體快取      │  │  外部數據源          │ │
│  │              │  │  (TTLCache)      │  │                     │ │
│  │ - 交易記錄   │  │                 │  │ - TWSE/TPEX API    │ │
│  │ - 預測紀錄   │  │ - 即時報價      │  │ - Yahoo Finance    │ │
│  │ - 持倉狀態   │  │ - 指標快取      │  │ - FinMind          │ │
│  │ - 歷史K線    │  │ - AI分析快取    │  │ - Groq API         │ │
│  │ - 使用者設定  │  │                 │  │                     │ │
│  └──────────────┘  └─────────────────┘  └─────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────────────┐
│                       排程層 (Scheduler)                         │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────────┐  │
│  │ 即時行情排程    │  │ 預測驗證排程    │  │ 盤後整理排程      │  │
│  │ 每5秒 (盤中)   │  │ 每62秒          │  │ 每日14:00         │  │
│  └────────────────┘  └────────────────┘  └───────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 數據流向圖

```
即時數據流（盤中）：

  外部API ──(5s輪詢)──► QuoteService ──► 快取更新
                                         │
                                         ├──► SignalEngine（重算訊號）
                                         │         │
                                         │         ├──► 加權評分計算
                                         │         │
                                         │         └──► WebSocket 推送訊號更新
                                         │
                                         └──► WebSocket 推送即時報價

AI分析流程：

  使用者請求分析 ──► API Router
                      │
                      ├──► 檢查快取 ──(命中)──► 回傳快取結果
                      │
                      └──(未命中)──► 檢查AI開關
                                      │
                                      ├──(關閉)──► 回傳「僅訊號評分」
                                      │
                                      └──(開啟)──► Groq API 呼叫
                                                    │
                                                    ├──► 解析回應
                                                    ├──► 寫入快取
                                                    └──► 回傳結果

預測驗證流程：

  排程觸發(62s) ──► 查詢待驗證預測
                      │
                      ├──► 取得當前即時價格
                      │
                      ├──► 比對預測方向 vs 實際漲跌
                      │
                      ├──► 更新預測記錄（成功/失敗）
                      │
                      ├──► 重算統計數據
                      │
                      └──► WebSocket 推送驗證結果
```

### 2.3 專案目錄結構

```
backend/
├── main.py                     # FastAPI 應用程式入口
├── config.py                   # 組態管理
├── database.py                 # 資料庫連線管理
│
├── api/                        # API 路由層
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── router.py           # 路由彙總
│   │   ├── stocks.py           # 股票查詢端點
│   │   ├── analysis.py         # 即時分析端點
│   │   ├── portfolio.py        # 模擬倉端點
│   │   ├── predictions.py      # 預測記錄端點
│   │   └── stats.py            # 統計數據端點
│   └── websocket.py            # WebSocket 端點
│
├── services/                   # 業務邏輯層
│   ├── __init__.py
│   ├── signal_engine.py        # 9大訊號評分引擎
│   ├── ai_analysis.py          # Groq AI 分析服務
│   ├── quote_service.py        # 行情數據服務
│   ├── portfolio_service.py    # 模擬倉服務
│   ├── prediction_service.py   # 預測與驗證服務
│   └── stats_service.py        # 統計報表服務
│
├── models/                     # 資料模型層
│   ├── __init__.py
│   ├── database_models.py      # SQLAlchemy ORM 模型
│   └── schemas.py              # Pydantic 請求/回應模型
│
├── core/                       # 核心元件
│   ├── __init__.py
│   ├── cache.py                # 快取管理
│   ├── scheduler.py            # 排程管理
│   ├── ws_manager.py           # WebSocket 連線管理
│   └── exceptions.py           # 自訂例外
│
├── data/                       # 數據目錄
│   └── twstock.db              # SQLite 資料庫檔案
│
├── prompts/                    # AI Prompt 模板
│   ├── analysis.py             # 綜合分析 prompt
│   └── prediction.py           # 漲跌預測 prompt
│
├── tests/                      # 測試目錄
│   ├── test_signal_engine.py
│   ├── test_portfolio.py
│   └── test_predictions.py
│
├── requirements.txt            # Python 依賴
└── .env.example                # 環境變數範例
```

---

## 3. 9大訊號評分引擎設計

### 3.1 訊號定義與權重

| # | 訊號名稱 | 類別 | 權重 | 數據來源 | 更新頻率 |
|---|---------|------|------|---------|---------|
| 1 | 技術面趨勢 (MA/EMA) | 技術分析 | 15% | K線數據 | 即時 |
| 2 | RSI 強弱指標 | 技術分析 | 10% | K線數據 | 即時 |
| 3 | MACD 動能 | 技術分析 | 12% | K線數據 | 即時 |
| 4 | KD 隨機指標 | 技術分析 | 8% | K線數據 | 即時 |
| 5 | 布林通道位置 | 技術分析 | 8% | K線數據 | 即時 |
| 6 | 成交量異常 | 量能分析 | 12% | 成交量數據 | 即時 |
| 7 | 法人買賣超 | 籌碼分析 | 15% | 法人進出 | 盤後 |
| 8 | 融資融券變化 | 籌碼分析 | 10% | 信用交易 | 盤後 |
| 9 | 本益比/基本面 | 基本面 | 10% | 財報數據 | 季/月 |
|   | **合計** | | **100%** | | |

### 3.2 訊號計算模組架構

```python
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass

class SignalDirection(Enum):
    STRONG_BULLISH = 2      # 強烈看漲
    BULLISH = 1             # 看漲
    NEUTRAL = 0             # 中性
    BEARISH = -1            # 看跌
    STRONG_BEARISH = -2     # 強烈看跌

@dataclass
class SignalResult:
    """單一訊號計算結果"""
    name: str                    # 訊號名稱
    direction: SignalDirection   # 方向
    score: float                 # 原始分數 (-100 ~ +100)
    weight: float                # 權重 (0~1)
    weighted_score: float        # 加權分數
    reason: str                  # 判斷理由
    raw_data: dict               # 原始計算數據

class BaseSignal(ABC):
    """訊號計算基底類別"""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def weight(self) -> float:
        pass

    @abstractmethod
    async def calculate(self, stock_id: str, market_data: dict) -> SignalResult:
        """計算訊號分數"""
        pass

class MASignal(BaseSignal):
    """訊號1：均線趨勢訊號"""
    name = "技術面趨勢 (MA/EMA)"
    weight = 0.15

    async def calculate(self, stock_id: str, market_data: dict) -> SignalResult:
        # 計算 MA5, MA10, MA20, MA60
        # 判斷多頭排列/空頭排列/糾結
        # 計算價格與均線的相對位置
        ...

class RSISignal(BaseSignal):
    """訊號2：RSI 強弱指標"""
    name = "RSI 強弱指標"
    weight = 0.10

    async def calculate(self, stock_id: str, market_data: dict) -> SignalResult:
        # 計算 RSI(6), RSI(12), RSI(24)
        # 超買(>80)/超賣(<20)/中性 判斷
        # RSI 背離檢測
        ...

# ... 其餘7個訊號類別類似設計
```

### 3.3 評分引擎核心

```python
class SignalEngine:
    """9大訊號加權評分引擎"""

    def __init__(self):
        self.signals: list[BaseSignal] = [
            MASignal(),
            RSISignal(),
            MACDSignal(),
            KDSignal(),
            BollingerSignal(),
            VolumeSignal(),
            InstitutionalSignal(),
            MarginSignal(),
            FundamentalSignal(),
        ]

    async def evaluate(self, stock_id: str) -> CompositeScore:
        """
        對指定股票執行完整評分流程
        Returns: CompositeScore 包含綜合分數與各訊號明細
        """
        # 1. 取得市場數據（快取優先）
        market_data = await self._get_market_data(stock_id)

        # 2. 平行計算所有訊號
        results = await asyncio.gather(*[
            signal.calculate(stock_id, market_data)
            for signal in self.signals
        ])

        # 3. 計算加權總分
        total_score = sum(r.weighted_score for r in results)

        # 4. 判定綜合方向
        direction = self._determine_direction(total_score)

        # 5. 計算信心度（各訊號一致性）
        confidence = self._calculate_confidence(results)

        return CompositeScore(
            stock_id=stock_id,
            total_score=total_score,         # -100 ~ +100
            direction=direction,              # 漲/跌/中性
            confidence=confidence,            # 0~100%
            signal_details=results,           # 各訊號明細
            calculated_at=datetime.now(),
        )

    def _determine_direction(self, score: float) -> str:
        if score >= 30:
            return "強烈看漲"
        elif score >= 10:
            return "看漲"
        elif score > -10:
            return "中性"
        elif score > -30:
            return "看跌"
        else:
            return "強烈看跌"

    def _calculate_confidence(self, results: list[SignalResult]) -> float:
        """
        信心度計算：當多數訊號方向一致時，信心度高
        """
        directions = [r.direction.value for r in results]
        positive = sum(1 for d in directions if d > 0)
        negative = sum(1 for d in directions if d < 0)
        total = len(directions)
        max_agreement = max(positive, negative)
        return round((max_agreement / total) * 100, 1)
```

### 3.4 即時更新機制

```
數據更新觸發流程：

  行情更新 (每5秒)
      │
      ▼
  QuoteService.on_price_update(stock_id, new_price)
      │
      ├──► 更新快取中的報價
      │
      ├──► 檢查是否有訂閱此股票的 WebSocket 連線
      │       │
      │       └──(有訂閱)──► SignalEngine.evaluate(stock_id)
      │                          │
      │                          ├──► 計算9大訊號（使用快取避免重複IO）
      │                          │
      │                          └──► WebSocket 推送更新結果
      │
      └──► 推送即時報價到所有訂閱的連線
```

**按需計算策略（節省資源）：**
- 只有「被前端訂閱的股票」才即時重算訊號
- 未被訂閱的股票不主動計算，僅在 API 請求時計算
- 訊號計算結果快取 60 秒，避免短時間重複計算

### 3.5 平行計算策略

```python
async def batch_evaluate(self, stock_ids: list[str]) -> list[CompositeScore]:
    """批量評估多檔股票（平行）"""
    # 使用 semaphore 控制並行數，避免資源耗盡
    semaphore = asyncio.Semaphore(10)  # 最多同時計算10檔

    async def _eval_with_limit(stock_id):
        async with semaphore:
            return await self.evaluate(stock_id)

    results = await asyncio.gather(*[
        _eval_with_limit(sid) for sid in stock_ids
    ])
    return results
```

---

## 4. Groq API（Llama 3.3）整合設計

### 4.1 API 呼叫架構

```python
from groq import AsyncGroq

class AIAnalysisService:
    """Groq AI 分析服務"""

    def __init__(self, config: AppConfig):
        self.client = AsyncGroq(api_key=config.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"
        self.enabled = config.AI_ENABLED  # 開關控制
        self.cache = TTLCache(maxsize=100, ttl=300)

    async def analyze(
        self, stock_id: str, signal_score: CompositeScore, market_context: dict
    ) -> AIAnalysisResult:
        """
        執行 AI 分析（非同步）
        """
        # 1. 檢查開關
        if not self.enabled:
            return AIAnalysisResult(
                available=False,
                message="AI 分析功能已關閉，僅顯示訊號評分結果"
            )

        # 2. 檢查快取
        cache_key = f"{stock_id}:{signal_score.total_score:.0f}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # 3. 組裝 Prompt
        prompt = self._build_prompt(stock_id, signal_score, market_context)

        # 4. 呼叫 Groq API（含重試）
        result = await self._call_groq(prompt)

        # 5. 解析回應
        analysis = self._parse_response(result)

        # 6. 寫入快取
        self.cache[cache_key] = analysis

        return analysis

    async def _call_groq(self, prompt: str, max_retries: int = 3) -> str:
        """帶重試邏輯的 Groq API 呼叫"""
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,       # 低溫度，結果更穩定
                    max_tokens=1024,
                    response_format={"type": "json_object"},
                )
                return response.choices[0].message.content

            except RateLimitError:
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)

            except APIError as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1)

        raise AIServiceUnavailable("Groq API 重試次數已耗盡")
```

### 4.2 Prompt 模板管理

```python
# prompts/analysis.py

SYSTEM_PROMPT = """你是一位專業的台股分析師。
根據提供的技術指標和訊號評分，給出簡潔的分析意見。
你必須以 JSON 格式回應。"""

ANALYSIS_TEMPLATE = """
## 股票分析請求

**股票代號**：{stock_id}
**股票名稱**：{stock_name}
**當前價格**：{current_price} 元
**今日漲跌**：{price_change} ({change_percent}%)

### 9大訊號評分結果
綜合評分：{total_score}/100
方向判定：{direction}
信心度：{confidence}%

### 各訊號明細
{signal_details}

### 近期技術面數據
- 5日均線：{ma5}
- 20日均線：{ma20}
- RSI(14)：{rsi14}
- 成交量(今/昨)：{volume_today}/{volume_yesterday}

請分析以上數據，回應 JSON 格式如下：
{{
  "summary": "一句話總結（20字內）",
  "outlook": "short_term_bullish | short_term_bearish | neutral",
  "key_factors": ["因素1", "因素2", "因素3"],
  "risk_level": "low | medium | high",
  "suggestion": "觀望 | 可考慮布局 | 建議減碼"
}}
"""

PREDICTION_TEMPLATE = """
## 漲跌預測請求

**股票代號**：{stock_id}
**當前價格**：{current_price}
**綜合訊號評分**：{total_score}

根據以上數據，預測未來62秒的短線走勢：
{{
  "predicted_direction": "up | down | flat",
  "confidence": 0.0-1.0,
  "reasoning": "理由"
}}
"""
```

### 4.3 AI 開關機制設計

```python
class AIToggle:
    """AI 功能開關管理"""

    def __init__(self):
        self._enabled: bool = True
        self._reason: str = ""
        self._disabled_at: datetime | None = None

    @property
    def enabled(self) -> bool:
        return self._enabled

    def enable(self):
        self._enabled = True
        self._reason = ""
        self._disabled_at = None

    def disable(self, reason: str = "使用者手動關閉"):
        self._enabled = False
        self._reason = reason
        self._disabled_at = datetime.now()

    def auto_disable(self, reason: str):
        """錯誤過多時自動關閉"""
        self.disable(reason=f"自動關閉：{reason}")

    def status(self) -> dict:
        return {
            "enabled": self._enabled,
            "reason": self._reason,
            "disabled_at": self._disabled_at,
        }
```

**自動降級觸發條件：**
- 連續 5 次 API 呼叫失敗 → 自動關閉 AI，10 分鐘後自動嘗試重新開啟
- API 回應延遲 > 10 秒 → 標記為降級模式，僅回傳訊號評分
- 達到每日 API 額度限制 → 自動關閉直到隔日重置

### 4.4 錯誤處理與降級策略

```
AI 服務降級流程：

  正常模式 (AI + 訊號)
       │
       ├──(API錯誤)──► 重試(最多3次)
       │                    │
       │                    ├──(成功)──► 回傳正常結果
       │                    │
       │                    └──(全部失敗)──► 降級模式
       │
       ▼
  降級模式 (僅訊號評分)
       │
       ├── 回傳訊號評分結果
       ├── 附加提示「AI 分析暫時無法使用」
       └── 記錄錯誤日誌

  自動恢復：
       │
       └── 10分鐘後自動嘗試一次 API 呼叫
             │
             ├──(成功)──► 恢復正常模式
             └──(失敗)──► 繼續降級，再等10分鐘
```

### 4.5 回應快取策略

| 快取鍵 | TTL | 說明 |
|--------|-----|------|
| `ai:{stock_id}:{score_bucket}` | 5 分鐘 | 同評分區間不重複查詢 |
| `prediction:{stock_id}:{timestamp_bucket}` | 62 秒 | 預測結果快取 |

**score_bucket 分桶規則：**
- 將 total_score 四捨五入到最近的 5 分（如 73 → 75, 68 → 70）
- 同一桶內視為相同分析請求，避免分數微小變動觸發重複 API 呼叫

---

## 5. 62秒自動驗證機制

### 5.1 排程系統設計

```python
class PredictionVerifier:
    """62秒預測驗證排程"""

    def __init__(self, scheduler: AsyncIOScheduler, db: AsyncSession):
        self.scheduler = scheduler
        self.db = db

    def start(self):
        """啟動驗證排程（僅在盤中執行）"""
        self.scheduler.add_job(
            self._verify_cycle,
            trigger='interval',
            seconds=62,
            id='prediction_verify',
            # 僅在盤中執行 (09:00 - 13:30)
            # APScheduler 不直接支援，在 _verify_cycle 內判斷
        )

    async def _verify_cycle(self):
        """單次驗證週期"""
        # 1. 檢查是否在盤中
        if not self._is_market_open():
            return

        # 2. 查詢所有待驗證的預測
        pending = await self._get_pending_predictions()

        # 3. 逐筆驗證
        for prediction in pending:
            await self._verify_single(prediction)

        # 4. 更新統計
        await self._update_stats()
```

### 5.2 預測記錄資料結構

```python
@dataclass
class PredictionRecord:
    """預測記錄"""
    id: int                          # 主鍵
    stock_id: str                    # 股票代號 e.g. "2330"
    stock_name: str                  # 股票名稱 e.g. "台積電"

    # 預測時的資訊
    predicted_at: datetime           # 預測時間
    predicted_direction: str         # 預測方向: "up" | "down" | "flat"
    predicted_confidence: float      # 預測信心度 0~1
    price_at_prediction: float       # 預測時的價格
    signal_score: float              # 預測時的訊號評分
    ai_involved: bool                # 是否使用了 AI 分析

    # 驗證時的資訊
    verify_at: datetime | None       # 驗證時間（預測時間 + 62秒）
    price_at_verify: float | None    # 驗證時的價格
    actual_direction: str | None     # 實際方向: "up" | "down" | "flat"
    price_change: float | None       # 價格變動
    price_change_pct: float | None   # 價格變動百分比

    # 驗證結果
    status: str                      # "pending" | "verified" | "expired"
    is_correct: bool | None          # 預測是否正確
    result_note: str | None          # 備註
```

### 5.3 驗證流程詳細設計

```python
async def _verify_single(self, prediction: PredictionRecord):
    """驗證單筆預測"""

    # 1. 取得當前價格
    current_price = await self.quote_service.get_price(prediction.stock_id)
    if current_price is None:
        prediction.status = "expired"
        prediction.result_note = "無法取得驗證時價格"
        await self._save(prediction)
        return

    # 2. 計算實際漲跌
    price_change = current_price - prediction.price_at_prediction
    price_change_pct = (price_change / prediction.price_at_prediction) * 100

    # 3. 判定實際方向
    THRESHOLD = 0.05  # 漲跌幅 < 0.05% 視為平盤
    if price_change_pct > THRESHOLD:
        actual_direction = "up"
    elif price_change_pct < -THRESHOLD:
        actual_direction = "down"
    else:
        actual_direction = "flat"

    # 4. 比對結果
    is_correct = self._compare_direction(
        predicted=prediction.predicted_direction,
        actual=actual_direction
    )

    # 5. 更新記錄
    prediction.verify_at = datetime.now()
    prediction.price_at_verify = current_price
    prediction.actual_direction = actual_direction
    prediction.price_change = price_change
    prediction.price_change_pct = round(price_change_pct, 4)
    prediction.is_correct = is_correct
    prediction.status = "verified"

    await self._save(prediction)

    # 6. 推送驗證結果到前端
    await self.ws_manager.broadcast_to_stock(
        prediction.stock_id,
        {
            "type": "prediction_verified",
            "data": prediction.to_dict()
        }
    )

def _compare_direction(self, predicted: str, actual: str) -> bool:
    """
    方向比對邏輯：
    - 預測 up/down，實際也是 up/down → 正確
    - 預測 flat，實際也是 flat → 正確
    - 預測 up，實際 flat → 半對（記為正確，因未虧損方向）
    - 預測 up，實際 down → 錯誤
    """
    if predicted == actual:
        return True
    if predicted in ("up", "down") and actual == "flat":
        return True  # 方向未反轉，視為半正確
    return False
```

### 5.4 成功率統計模組

```python
class PredictionStats:
    """預測成功率統計"""

    async def get_stats(
        self,
        stock_id: str | None = None,
        period: str = "today"   # today | week | month | all
    ) -> StatsResult:
        """取得預測統計"""

        records = await self._query_records(stock_id, period)

        total = len(records)
        correct = sum(1 for r in records if r.is_correct)
        incorrect = total - correct

        # 分方向統計
        up_predictions = [r for r in records if r.predicted_direction == "up"]
        down_predictions = [r for r in records if r.predicted_direction == "down"]

        return StatsResult(
            total_predictions=total,
            correct_predictions=correct,
            incorrect_predictions=incorrect,
            accuracy_rate=round(correct / total * 100, 1) if total > 0 else 0,

            # 分方向
            up_accuracy=self._calc_accuracy(up_predictions),
            down_accuracy=self._calc_accuracy(down_predictions),

            # AI vs 非AI 比較
            ai_accuracy=self._calc_accuracy(
                [r for r in records if r.ai_involved]
            ),
            signal_only_accuracy=self._calc_accuracy(
                [r for r in records if not r.ai_involved]
            ),

            # 分信心度統計
            high_confidence_accuracy=self._calc_accuracy(
                [r for r in records if r.predicted_confidence >= 0.7]
            ),
            low_confidence_accuracy=self._calc_accuracy(
                [r for r in records if r.predicted_confidence < 0.7]
            ),

            period=period,
            stock_id=stock_id,
        )
```

---

## 6. 模擬倉功能設計

### 6.1 資料模型設計

```python
# ========== 使用者帳戶 ==========
class UserAccount:
    id: int                          # 主鍵
    username: str                    # 使用者名稱（預設 "default"）
    initial_capital: float           # 初始資金（預設 1,000,000）
    current_cash: float              # 目前現金餘額
    created_at: datetime             # 建立時間
    updated_at: datetime             # 更新時間

# ========== 持倉部位 ==========
class Position:
    id: int                          # 主鍵
    user_id: int                     # 使用者ID
    stock_id: str                    # 股票代號
    stock_name: str                  # 股票名稱
    shares: int                      # 持有股數（整股，1000股為1張）
    avg_cost: float                  # 平均成本（含手續費）
    total_cost: float                # 總成本
    current_price: float             # 目前價格（即時更新）
    unrealized_pnl: float            # 未實現損益
    unrealized_pnl_pct: float        # 未實現損益%
    created_at: datetime             # 首次買入時間
    updated_at: datetime             # 最後更新時間

# ========== 交易記錄 ==========
class TradeRecord:
    id: int                          # 主鍵
    user_id: int                     # 使用者ID
    stock_id: str                    # 股票代號
    stock_name: str                  # 股票名稱
    trade_type: str                  # "buy" | "sell"
    shares: int                      # 交易股數
    price: float                     # 成交價格
    amount: float                    # 成交金額 (price * shares)
    fee: float                       # 手續費
    tax: float                       # 交易稅（賣出時）
    net_amount: float                # 淨金額（扣除費用）
    realized_pnl: float | None       # 已實現損益（賣出時計算）
    signal_score: float | None       # 下單時的訊號評分
    trade_reason: str | None         # 交易理由
    traded_at: datetime              # 交易時間

# ========== 資產快照 ==========
class AssetSnapshot:
    id: int                          # 主鍵
    user_id: int                     # 使用者ID
    snapshot_date: date              # 快照日期
    cash: float                      # 現金
    stock_value: float               # 持股市值
    total_assets: float              # 總資產
    daily_pnl: float                 # 當日損益
    daily_pnl_pct: float             # 當日損益%
    total_pnl: float                 # 累計損益
    total_pnl_pct: float             # 累計報酬率%
    positions_detail: str            # 持倉明細（JSON）
    created_at: datetime             # 建立時間
```

### 6.2 買入邏輯

```python
class PortfolioService:

    # 台股交易常數
    FEE_RATE = 0.001425        # 手續費率 0.1425%
    FEE_DISCOUNT = 0.6         # 手續費折扣（大多數券商6折）
    TAX_RATE = 0.003           # 交易稅 0.3%（賣出時收取）
    MIN_FEE = 20               # 最低手續費 20 元

    async def buy(
        self, user_id: int, stock_id: str, shares: int, price: float | None = None
    ) -> TradeResult:
        """
        模擬買入
        - shares: 股數（1張 = 1000股）
        - price: 買入價（None 則使用即時價）
        """
        # 1. 取得買入價格
        if price is None:
            price = await self.quote_service.get_price(stock_id)

        # 2. 計算金額與手續費
        amount = price * shares
        fee = max(
            amount * self.FEE_RATE * self.FEE_DISCOUNT,
            self.MIN_FEE
        )
        fee = math.floor(fee)  # 手續費無條件捨去
        total_cost = amount + fee

        # 3. 檢查餘額
        account = await self._get_account(user_id)
        if account.current_cash < total_cost:
            raise InsufficientFunds(
                f"現金不足：需要 {total_cost:,.0f}，"
                f"餘額 {account.current_cash:,.0f}"
            )

        # 4. 扣款
        account.current_cash -= total_cost

        # 5. 更新或建立持倉
        position = await self._get_position(user_id, stock_id)
        if position:
            # 加碼：重新計算平均成本
            old_total = position.avg_cost * position.shares
            new_total = old_total + total_cost
            position.shares += shares
            position.avg_cost = new_total / position.shares
            position.total_cost = new_total
        else:
            # 新建持倉
            position = Position(
                user_id=user_id,
                stock_id=stock_id,
                stock_name=await self._get_stock_name(stock_id),
                shares=shares,
                avg_cost=total_cost / shares,
                total_cost=total_cost,
            )

        # 6. 建立交易記錄
        trade = TradeRecord(
            user_id=user_id,
            stock_id=stock_id,
            trade_type="buy",
            shares=shares,
            price=price,
            amount=amount,
            fee=fee,
            tax=0,
            net_amount=total_cost,
            traded_at=datetime.now(),
        )

        await self._save_all(account, position, trade)

        return TradeResult(success=True, trade=trade, position=position)
```

### 6.3 賣出邏輯

```python
    async def sell(
        self, user_id: int, stock_id: str, shares: int, price: float | None = None
    ) -> TradeResult:
        """
        模擬賣出
        """
        # 1. 取得賣出價格
        if price is None:
            price = await self.quote_service.get_price(stock_id)

        # 2. 檢查持倉
        position = await self._get_position(user_id, stock_id)
        if not position or position.shares < shares:
            raise InsufficientShares("持有股數不足")

        # 3. 計算金額與稅費
        amount = price * shares
        fee = max(
            amount * self.FEE_RATE * self.FEE_DISCOUNT,
            self.MIN_FEE
        )
        fee = math.floor(fee)
        tax = math.floor(amount * self.TAX_RATE)  # 交易稅無條件捨去
        net_proceeds = amount - fee - tax

        # 4. 計算已實現損益
        cost_basis = position.avg_cost * shares  # 賣出部位的成本
        realized_pnl = net_proceeds - cost_basis

        # 5. 入帳
        account = await self._get_account(user_id)
        account.current_cash += net_proceeds

        # 6. 更新持倉
        position.shares -= shares
        if position.shares == 0:
            await self._delete_position(position)
        else:
            position.total_cost = position.avg_cost * position.shares

        # 7. 建立交易記錄
        trade = TradeRecord(
            user_id=user_id,
            stock_id=stock_id,
            trade_type="sell",
            shares=shares,
            price=price,
            amount=amount,
            fee=fee,
            tax=tax,
            net_amount=net_proceeds,
            realized_pnl=realized_pnl,
            traded_at=datetime.now(),
        )

        await self._save_all(account, position, trade)

        return TradeResult(success=True, trade=trade, realized_pnl=realized_pnl)
```

### 6.4 損益計算說明

```
買入成本計算：
  成交金額 = 股價 × 股數
  手續費   = 成交金額 × 0.1425% × 折扣(0.6) （最低20元，無條件捨去）
  買入總成本 = 成交金額 + 手續費

賣出淨收入計算：
  成交金額 = 股價 × 股數
  手續費   = 成交金額 × 0.1425% × 折扣(0.6) （最低20元，無條件捨去）
  交易稅   = 成交金額 × 0.3%               （無條件捨去）
  賣出淨收入 = 成交金額 - 手續費 - 交易稅

已實現損益 = 賣出淨收入 - 買入成本（依平均成本法）
未實現損益 = (目前價格 × 持有股數) - 持有成本

範例（買入台積電 1張 @1000元）：
  買入：1000 × 1000 = 1,000,000
  手續費：1,000,000 × 0.001425 × 0.6 = 855 → 855
  買入總成本：1,000,855

  賣出 @1050元：
  賣出金額：1050 × 1000 = 1,050,000
  手續費：1,050,000 × 0.001425 × 0.6 = 897 → 897
  交易稅：1,050,000 × 0.003 = 3,150
  淨收入：1,050,000 - 897 - 3,150 = 1,045,953
  已實現損益：1,045,953 - 1,000,855 = +45,098
```

### 6.5 資產快照與歷史記錄

```python
async def take_daily_snapshot(self, user_id: int):
    """每日盤後建立資產快照"""
    account = await self._get_account(user_id)
    positions = await self._get_all_positions(user_id)

    # 計算持股市值
    stock_value = 0
    positions_detail = []
    for pos in positions:
        current_price = await self.quote_service.get_closing_price(pos.stock_id)
        market_value = current_price * pos.shares
        stock_value += market_value
        positions_detail.append({
            "stock_id": pos.stock_id,
            "stock_name": pos.stock_name,
            "shares": pos.shares,
            "avg_cost": pos.avg_cost,
            "current_price": current_price,
            "market_value": market_value,
            "pnl": market_value - pos.total_cost,
        })

    total_assets = account.current_cash + stock_value

    # 取得前日快照以計算日損益
    prev_snapshot = await self._get_latest_snapshot(user_id)
    prev_total = prev_snapshot.total_assets if prev_snapshot else account.initial_capital

    snapshot = AssetSnapshot(
        user_id=user_id,
        snapshot_date=date.today(),
        cash=account.current_cash,
        stock_value=stock_value,
        total_assets=total_assets,
        daily_pnl=total_assets - prev_total,
        daily_pnl_pct=round((total_assets - prev_total) / prev_total * 100, 2),
        total_pnl=total_assets - account.initial_capital,
        total_pnl_pct=round(
            (total_assets - account.initial_capital) / account.initial_capital * 100, 2
        ),
        positions_detail=json.dumps(positions_detail, ensure_ascii=False),
    )

    await self._save(snapshot)
```

---

## 7. RESTful API 端點設計

### 7.1 API 基礎資訊

- **Base URL**: `http://localhost:8000/api/v1`
- **格式**: JSON
- **認證**: 無（個人單機使用）
- **版本策略**: URL 路徑版本 `/api/v1/`

### 7.2 統一回應格式

```json
// 成功回應
{
  "success": true,
  "data": { ... },
  "timestamp": "2026-04-09T10:30:00+08:00"
}

// 錯誤回應
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_FUNDS",
    "message": "現金餘額不足"
  },
  "timestamp": "2026-04-09T10:30:00+08:00"
}

// 分頁回應
{
  "success": true,
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 156,
    "total_pages": 8
  },
  "timestamp": "2026-04-09T10:30:00+08:00"
}
```

### 7.3 股票查詢 API

| 方法 | 端點 | 說明 | 參數 |
|------|------|------|------|
| GET | `/stocks/search` | 搜尋股票 | `q` (關鍵字), `market` (上市/上櫃) |
| GET | `/stocks/{stock_id}` | 取得個股資訊 | - |
| GET | `/stocks/{stock_id}/quote` | 取得即時報價 | - |
| GET | `/stocks/{stock_id}/history` | 取得歷史K線 | `period` (1d/5d/1m/3m/6m/1y), `interval` (1m/5m/1d) |
| GET | `/stocks/{stock_id}/institutional` | 取得法人買賣超 | `days` (天數，預設 10) |
| GET | `/stocks/{stock_id}/margin` | 取得融資融券 | `days` (天數，預設 10) |

**範例回應 - 即時報價：**

```json
GET /api/v1/stocks/2330/quote

{
  "success": true,
  "data": {
    "stock_id": "2330",
    "stock_name": "台積電",
    "current_price": 1025.0,
    "open": 1020.0,
    "high": 1030.0,
    "low": 1018.0,
    "close": 1025.0,
    "volume": 25630,
    "change": 15.0,
    "change_percent": 1.49,
    "bid_price": 1024.0,
    "ask_price": 1025.0,
    "updated_at": "2026-04-09T10:30:05+08:00"
  }
}
```

### 7.4 即時分析 API

| 方法 | 端點 | 說明 | 參數 |
|------|------|------|------|
| GET | `/analysis/{stock_id}/signals` | 取得9大訊號評分 | - |
| GET | `/analysis/{stock_id}/composite` | 取得綜合分析（訊號+AI） | `include_ai` (bool, 預設 true) |
| POST | `/analysis/{stock_id}/predict` | 產生漲跌預測 | `use_ai` (bool) |
| GET | `/analysis/ai/status` | AI 服務狀態 | - |
| POST | `/analysis/ai/toggle` | 切換 AI 開關 | `enabled` (bool) |

**範例回應 - 綜合分析：**

```json
GET /api/v1/analysis/2330/composite

{
  "success": true,
  "data": {
    "stock_id": "2330",
    "stock_name": "台積電",
    "composite_score": {
      "total_score": 42.5,
      "direction": "看漲",
      "confidence": 66.7,
      "calculated_at": "2026-04-09T10:30:10+08:00"
    },
    "signals": [
      {
        "name": "技術面趨勢 (MA/EMA)",
        "direction": "BULLISH",
        "score": 65.0,
        "weight": 0.15,
        "weighted_score": 9.75,
        "reason": "多頭排列：MA5 > MA10 > MA20，價格在所有均線之上"
      },
      // ... 其餘8個訊號
    ],
    "ai_analysis": {
      "available": true,
      "summary": "短線偏多，均線多頭排列支撐走勢",
      "outlook": "short_term_bullish",
      "key_factors": [
        "均線多頭排列",
        "成交量溫和放大",
        "法人連續買超"
      ],
      "risk_level": "medium",
      "suggestion": "可考慮布局"
    }
  }
}
```

### 7.5 模擬倉操作 API

| 方法 | 端點 | 說明 | 參數 |
|------|------|------|------|
| GET | `/portfolio/account` | 取得帳戶總覽 | - |
| GET | `/portfolio/positions` | 取得所有持倉 | - |
| GET | `/portfolio/positions/{stock_id}` | 取得指定持倉 | - |
| POST | `/portfolio/buy` | 模擬買入 | Body: `{stock_id, shares, price?}` |
| POST | `/portfolio/sell` | 模擬賣出 | Body: `{stock_id, shares, price?}` |
| GET | `/portfolio/trades` | 取得交易記錄 | `page`, `page_size`, `stock_id?`, `type?` |
| GET | `/portfolio/snapshots` | 取得資產快照 | `start_date`, `end_date` |
| POST | `/portfolio/reset` | 重置模擬倉 | Body: `{initial_capital?}` |

**範例請求 - 買入：**

```json
POST /api/v1/portfolio/buy

{
  "stock_id": "2330",
  "shares": 1000,
  "price": 1025.0    // 可省略，使用即時價
}

// 回應
{
  "success": true,
  "data": {
    "trade": {
      "id": 42,
      "stock_id": "2330",
      "stock_name": "台積電",
      "trade_type": "buy",
      "shares": 1000,
      "price": 1025.0,
      "amount": 1025000,
      "fee": 876,
      "tax": 0,
      "net_amount": 1025876,
      "traded_at": "2026-04-09T10:35:00+08:00"
    },
    "position": {
      "stock_id": "2330",
      "shares": 1000,
      "avg_cost": 1025.876,
      "total_cost": 1025876
    },
    "account_balance": 974124
  }
}
```

### 7.6 預測記錄 API

| 方法 | 端點 | 說明 | 參數 |
|------|------|------|------|
| GET | `/predictions` | 取得預測記錄列表 | `page`, `page_size`, `stock_id?`, `status?`, `date?` |
| GET | `/predictions/{id}` | 取得單筆預測詳情 | - |
| GET | `/predictions/stats` | 取得預測統計 | `stock_id?`, `period` (today/week/month/all) |
| GET | `/predictions/latest` | 取得最新預測 | `stock_id?`, `limit` (預設 10) |

**範例回應 - 預測統計：**

```json
GET /api/v1/predictions/stats?period=today

{
  "success": true,
  "data": {
    "period": "today",
    "total_predictions": 156,
    "correct_predictions": 98,
    "incorrect_predictions": 58,
    "accuracy_rate": 62.8,
    "up_accuracy": 65.2,
    "down_accuracy": 59.3,
    "ai_accuracy": 68.4,
    "signal_only_accuracy": 57.1,
    "high_confidence_accuracy": 72.3,
    "low_confidence_accuracy": 51.6
  }
}
```

### 7.7 統計數據 API

| 方法 | 端點 | 說明 | 參數 |
|------|------|------|------|
| GET | `/stats/dashboard` | 儀表板總覽 | - |
| GET | `/stats/performance` | 績效報表 | `period` (week/month/quarter/year) |
| GET | `/stats/signals/accuracy` | 各訊號歷史準確度 | `period` |
| GET | `/stats/portfolio/history` | 資產歷史曲線 | `start_date`, `end_date` |

**範例回應 - 儀表板：**

```json
GET /api/v1/stats/dashboard

{
  "success": true,
  "data": {
    "portfolio": {
      "total_assets": 1_250_000,
      "total_pnl": 250_000,
      "total_pnl_pct": 25.0,
      "daily_pnl": 8500,
      "positions_count": 5
    },
    "predictions": {
      "today_total": 45,
      "today_accuracy": 64.4,
      "overall_accuracy": 61.2,
      "best_signal": "法人買賣超",
      "best_signal_accuracy": 71.5
    },
    "ai_status": {
      "enabled": true,
      "calls_today": 120,
      "avg_response_ms": 850
    },
    "market_status": {
      "is_open": true,
      "taiex": 22350.6,
      "taiex_change": 125.3,
      "taiex_change_pct": 0.56
    }
  }
}
```

---

## 8. WebSocket 推送設計

### 8.1 連線管理

```python
class WebSocketManager:
    """WebSocket 連線管理器"""

    def __init__(self):
        # 所有活躍連線
        self.active_connections: dict[str, WebSocket] = {}
        # 股票訂閱映射：stock_id -> set of connection_ids
        self.stock_subscriptions: dict[str, set[str]] = defaultdict(set)
        # 連線訂閱映射：connection_id -> set of stock_ids
        self.connection_subscriptions: dict[str, set[str]] = defaultdict(set)

    async def connect(self, websocket: WebSocket) -> str:
        """接受連線，回傳 connection_id"""
        await websocket.accept()
        conn_id = str(uuid4())
        self.active_connections[conn_id] = websocket
        return conn_id

    async def disconnect(self, conn_id: str):
        """斷開連線，清理訂閱"""
        # 移除所有訂閱
        for stock_id in self.connection_subscriptions.get(conn_id, set()):
            self.stock_subscriptions[stock_id].discard(conn_id)
        self.connection_subscriptions.pop(conn_id, None)
        self.active_connections.pop(conn_id, None)

    async def subscribe(self, conn_id: str, stock_id: str):
        """訂閱個股頻道"""
        self.stock_subscriptions[stock_id].add(conn_id)
        self.connection_subscriptions[conn_id].add(stock_id)

    async def unsubscribe(self, conn_id: str, stock_id: str):
        """取消訂閱"""
        self.stock_subscriptions[stock_id].discard(conn_id)
        self.connection_subscriptions[conn_id].discard(stock_id)

    async def broadcast_to_stock(self, stock_id: str, message: dict):
        """推送訊息給訂閱該股票的所有連線"""
        conn_ids = self.stock_subscriptions.get(stock_id, set())
        dead_connections = []

        for conn_id in conn_ids:
            ws = self.active_connections.get(conn_id)
            if ws:
                try:
                    await ws.send_json(message)
                except WebSocketDisconnect:
                    dead_connections.append(conn_id)

        # 清理斷線的連線
        for conn_id in dead_connections:
            await self.disconnect(conn_id)

    async def broadcast_all(self, message: dict):
        """推送訊息給所有連線"""
        dead_connections = []
        for conn_id, ws in self.active_connections.items():
            try:
                await ws.send_json(message)
            except WebSocketDisconnect:
                dead_connections.append(conn_id)

        for conn_id in dead_connections:
            await self.disconnect(conn_id)
```

### 8.2 WebSocket 端點

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    conn_id = await ws_manager.connect(websocket)

    try:
        # 發送歡迎訊息
        await websocket.send_json({
            "type": "connected",
            "connection_id": conn_id,
            "server_time": datetime.now().isoformat(),
        })

        while True:
            # 接收客戶端訊息
            data = await websocket.receive_json()
            await handle_ws_message(conn_id, data)

    except WebSocketDisconnect:
        await ws_manager.disconnect(conn_id)
```

### 8.3 訊息格式定義

**客戶端 → 伺服器：**

```json
// 訂閱個股
{
  "action": "subscribe",
  "stock_id": "2330"
}

// 取消訂閱
{
  "action": "unsubscribe",
  "stock_id": "2330"
}

// 心跳
{
  "action": "ping"
}
```

**伺服器 → 客戶端：**

```json
// 連線成功
{
  "type": "connected",
  "connection_id": "uuid-xxx",
  "server_time": "2026-04-09T09:00:00+08:00"
}

// 即時報價更新
{
  "type": "quote_update",
  "data": {
    "stock_id": "2330",
    "price": 1025.0,
    "change": 15.0,
    "change_percent": 1.49,
    "volume": 25630,
    "updated_at": "2026-04-09T10:30:05+08:00"
  }
}

// 訊號評分更新
{
  "type": "signal_update",
  "data": {
    "stock_id": "2330",
    "total_score": 42.5,
    "direction": "看漲",
    "confidence": 66.7,
    "top_signal": "法人連續買超3日",
    "calculated_at": "2026-04-09T10:30:10+08:00"
  }
}

// 預測結果
{
  "type": "prediction_created",
  "data": {
    "prediction_id": 1234,
    "stock_id": "2330",
    "predicted_direction": "up",
    "confidence": 0.72,
    "verify_at": "2026-04-09T10:31:12+08:00"
  }
}

// 預測驗證結果
{
  "type": "prediction_verified",
  "data": {
    "prediction_id": 1234,
    "stock_id": "2330",
    "predicted_direction": "up",
    "actual_direction": "up",
    "is_correct": true,
    "price_change": 2.5,
    "price_change_pct": 0.24
  }
}

// 心跳回應
{
  "type": "pong",
  "server_time": "2026-04-09T10:30:00+08:00"
}

// 錯誤
{
  "type": "error",
  "message": "無效的股票代號"
}
```

### 8.4 頻道設計

```
頻道架構：

  全域頻道 (所有連線自動接收)
  ├── market_status    大盤狀態更新（開盤/收盤、大盤指數）
  └── system_notice    系統公告（AI 狀態變更等）

  個股頻道 (需訂閱)
  └── stock:{stock_id}
      ├── quote_update         即時報價
      ├── signal_update        訊號評分更新
      ├── prediction_created   新預測產生
      └── prediction_verified  預測驗證結果
```

### 8.5 心跳機制

```python
HEARTBEAT_INTERVAL = 30  # 秒
HEARTBEAT_TIMEOUT = 90   # 秒（3次未回應視為斷線）

class HeartbeatManager:
    def __init__(self, ws_manager: WebSocketManager):
        self.ws_manager = ws_manager
        self.last_pong: dict[str, datetime] = {}

    async def start_heartbeat_loop(self):
        """定時發送心跳"""
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            now = datetime.now()
            dead_connections = []

            for conn_id, ws in self.ws_manager.active_connections.items():
                # 檢查是否超時
                last = self.last_pong.get(conn_id, now)
                if (now - last).seconds > HEARTBEAT_TIMEOUT:
                    dead_connections.append(conn_id)
                    continue

                try:
                    await ws.send_json({"type": "ping"})
                except Exception:
                    dead_connections.append(conn_id)

            for conn_id in dead_connections:
                await self.ws_manager.disconnect(conn_id)
                self.last_pong.pop(conn_id, None)

    def record_pong(self, conn_id: str):
        self.last_pong[conn_id] = datetime.now()
```

---

## 9. 資料庫 Schema 設計

### 9.1 ER 關聯圖

```
┌──────────────┐     1:N     ┌──────────────┐
│ user_accounts│────────────►│  positions   │
│              │             │              │
│ PK: id      │             │ PK: id       │
│              │             │ FK: user_id  │
└──────┬───────┘             └──────────────┘
       │
       │ 1:N
       ├──────────────────►┌──────────────┐
       │                   │ trade_records│
       │                   │              │
       │                   │ PK: id       │
       │                   │ FK: user_id  │
       │                   └──────────────┘
       │
       │ 1:N
       ├──────────────────►┌──────────────────┐
       │                   │ asset_snapshots  │
       │                   │                  │
       │                   │ PK: id           │
       │                   │ FK: user_id      │
       │                   └──────────────────┘
       │
       │ (global)
       ▼
┌──────────────────┐
│ prediction_records│  (不綁定user，系統全域)
│                  │
│ PK: id           │
└──────────────────┘

┌──────────────────┐
│ stock_daily_data │  (歷史K線快取)
│                  │
│ PK: id           │
│ UK: stock_id+date│
└──────────────────┘

┌──────────────────┐
│ app_settings     │  (應用程式設定)
│                  │
│ PK: key          │
└──────────────────┘
```

### 9.2 資料表定義

#### user_accounts（使用者帳戶）

```sql
CREATE TABLE user_accounts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL DEFAULT 'default' UNIQUE,
    initial_capital REAL NOT NULL DEFAULT 1000000,
    current_cash    REAL NOT NULL DEFAULT 1000000,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### positions（持倉部位）

```sql
CREATE TABLE positions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES user_accounts(id),
    stock_id        TEXT NOT NULL,
    stock_name      TEXT NOT NULL,
    shares          INTEGER NOT NULL DEFAULT 0,
    avg_cost        REAL NOT NULL DEFAULT 0,
    total_cost      REAL NOT NULL DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, stock_id)
);

CREATE INDEX idx_positions_user ON positions(user_id);
CREATE INDEX idx_positions_stock ON positions(stock_id);
```

#### trade_records（交易記錄）

```sql
CREATE TABLE trade_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES user_accounts(id),
    stock_id        TEXT NOT NULL,
    stock_name      TEXT NOT NULL,
    trade_type      TEXT NOT NULL CHECK(trade_type IN ('buy', 'sell')),
    shares          INTEGER NOT NULL,
    price           REAL NOT NULL,
    amount          REAL NOT NULL,
    fee             REAL NOT NULL DEFAULT 0,
    tax             REAL NOT NULL DEFAULT 0,
    net_amount      REAL NOT NULL,
    realized_pnl    REAL,
    signal_score    REAL,
    trade_reason    TEXT,
    traded_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trades_user ON trade_records(user_id);
CREATE INDEX idx_trades_stock ON trade_records(stock_id);
CREATE INDEX idx_trades_date ON trade_records(traded_at);
CREATE INDEX idx_trades_type ON trade_records(trade_type);
```

#### prediction_records（預測記錄）

```sql
CREATE TABLE prediction_records (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id              TEXT NOT NULL,
    stock_name            TEXT NOT NULL,

    -- 預測資訊
    predicted_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    predicted_direction   TEXT NOT NULL CHECK(predicted_direction IN ('up', 'down', 'flat')),
    predicted_confidence  REAL NOT NULL DEFAULT 0,
    price_at_prediction   REAL NOT NULL,
    signal_score          REAL,
    ai_involved           BOOLEAN NOT NULL DEFAULT FALSE,

    -- 驗證資訊
    verify_at             TIMESTAMP,
    price_at_verify       REAL,
    actual_direction      TEXT CHECK(actual_direction IN ('up', 'down', 'flat')),
    price_change          REAL,
    price_change_pct      REAL,

    -- 結果
    status                TEXT NOT NULL DEFAULT 'pending'
                          CHECK(status IN ('pending', 'verified', 'expired')),
    is_correct            BOOLEAN,
    result_note           TEXT
);

CREATE INDEX idx_predictions_stock ON prediction_records(stock_id);
CREATE INDEX idx_predictions_status ON prediction_records(status);
CREATE INDEX idx_predictions_date ON prediction_records(predicted_at);
CREATE INDEX idx_predictions_correct ON prediction_records(is_correct);
CREATE INDEX idx_predictions_ai ON prediction_records(ai_involved);
```

#### asset_snapshots（資產快照）

```sql
CREATE TABLE asset_snapshots (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           INTEGER NOT NULL REFERENCES user_accounts(id),
    snapshot_date     DATE NOT NULL,
    cash              REAL NOT NULL,
    stock_value       REAL NOT NULL,
    total_assets      REAL NOT NULL,
    daily_pnl         REAL NOT NULL DEFAULT 0,
    daily_pnl_pct     REAL NOT NULL DEFAULT 0,
    total_pnl         REAL NOT NULL DEFAULT 0,
    total_pnl_pct     REAL NOT NULL DEFAULT 0,
    positions_detail  TEXT,          -- JSON 格式的持倉快照
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, snapshot_date)
);

CREATE INDEX idx_snapshots_user_date ON asset_snapshots(user_id, snapshot_date);
```

#### stock_daily_data（股票日線數據快取）

```sql
CREATE TABLE stock_daily_data (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id        TEXT NOT NULL,
    trade_date      DATE NOT NULL,
    open_price      REAL,
    high_price      REAL,
    low_price       REAL,
    close_price     REAL,
    volume          INTEGER,
    turnover        REAL,           -- 成交金額
    change_price    REAL,           -- 漲跌價
    change_pct      REAL,           -- 漲跌幅%
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(stock_id, trade_date)
);

CREATE INDEX idx_daily_stock ON stock_daily_data(stock_id);
CREATE INDEX idx_daily_date ON stock_daily_data(trade_date);
CREATE INDEX idx_daily_stock_date ON stock_daily_data(stock_id, trade_date);
```

#### app_settings（應用程式設定）

```sql
CREATE TABLE app_settings (
    key             TEXT PRIMARY KEY,
    value           TEXT NOT NULL,
    description     TEXT,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 預設設定
INSERT INTO app_settings (key, value, description) VALUES
    ('ai_enabled', 'true', 'AI 分析功能開關'),
    ('ai_model', 'llama-3.3-70b-versatile', 'Groq 使用的模型'),
    ('prediction_interval', '62', '預測驗證間隔（秒）'),
    ('quote_interval', '5', '行情更新間隔（秒）'),
    ('fee_discount', '0.6', '手續費折扣'),
    ('initial_capital', '1000000', '預設初始資金');
```

### 9.3 索引策略總結

| 資料表 | 索引 | 用途 |
|-------|------|------|
| positions | (user_id) | 查詢使用者持倉 |
| positions | (stock_id) | 查詢個股持倉 |
| positions | (user_id, stock_id) UNIQUE | 確保唯一持倉 |
| trade_records | (user_id) | 查詢使用者交易 |
| trade_records | (stock_id) | 查詢個股交易 |
| trade_records | (traded_at) | 依時間排序 |
| prediction_records | (stock_id) | 查詢個股預測 |
| prediction_records | (status) | 查詢待驗證預測 |
| prediction_records | (predicted_at) | 時間範圍查詢 |
| prediction_records | (is_correct) | 統計正確率 |
| prediction_records | (ai_involved) | AI vs 非AI 比較 |
| asset_snapshots | (user_id, snapshot_date) UNIQUE | 每日唯一快照 |
| stock_daily_data | (stock_id, trade_date) UNIQUE | 唯一日線數據 |

### 9.4 SQLAlchemy ORM 模型對應

```python
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    Date, Text, ForeignKey, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

class UserAccount(Base):
    __tablename__ = "user_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True, default="default")
    initial_capital = Column(Float, nullable=False, default=1_000_000)
    current_cash = Column(Float, nullable=False, default=1_000_000)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    positions = relationship("Position", back_populates="user")
    trades = relationship("TradeRecord", back_populates="user")
    snapshots = relationship("AssetSnapshot", back_populates="user")

class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (
        UniqueConstraint("user_id", "stock_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_accounts.id"), nullable=False)
    stock_id = Column(String, nullable=False)
    stock_name = Column(String, nullable=False)
    shares = Column(Integer, nullable=False, default=0)
    avg_cost = Column(Float, nullable=False, default=0)
    total_cost = Column(Float, nullable=False, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("UserAccount", back_populates="positions")

class PredictionRecord(Base):
    __tablename__ = "prediction_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(String, nullable=False, index=True)
    stock_name = Column(String, nullable=False)
    predicted_at = Column(DateTime, nullable=False, server_default=func.now())
    predicted_direction = Column(String, nullable=False)
    predicted_confidence = Column(Float, nullable=False, default=0)
    price_at_prediction = Column(Float, nullable=False)
    signal_score = Column(Float)
    ai_involved = Column(Boolean, nullable=False, default=False)
    verify_at = Column(DateTime)
    price_at_verify = Column(Float)
    actual_direction = Column(String)
    price_change = Column(Float)
    price_change_pct = Column(Float)
    status = Column(String, nullable=False, default="pending", index=True)
    is_correct = Column(Boolean)
    result_note = Column(Text)

# ... TradeRecord, AssetSnapshot, StockDailyData 類似定義
```

---

## 附錄 A：環境變數設定

```env
# .env.example

# === 應用程式 ===
APP_NAME=台股實驗預測及模擬倉
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true

# === 資料庫 ===
DATABASE_URL=sqlite+aiosqlite:///./data/twstock.db

# === Groq AI ===
GROQ_API_KEY=gsk_your_api_key_here
AI_ENABLED=true
AI_MODEL=llama-3.3-70b-versatile

# === 排程 ===
PREDICTION_INTERVAL=62
QUOTE_INTERVAL=5

# === 模擬倉 ===
INITIAL_CAPITAL=1000000
FEE_DISCOUNT=0.6
```

## 附錄 B：啟動流程

```python
# main.py 啟動順序
async def lifespan(app: FastAPI):
    # === 啟動階段 ===
    # 1. 初始化資料庫連線
    await init_database()

    # 2. 建立預設使用者帳戶
    await ensure_default_account()

    # 3. 初始化服務
    signal_engine = SignalEngine()
    ai_service = AIAnalysisService(config)
    portfolio_service = PortfolioService()
    prediction_service = PredictionService()
    ws_manager = WebSocketManager()

    # 4. 啟動排程
    scheduler = AsyncIOScheduler()
    setup_scheduled_jobs(scheduler)
    scheduler.start()

    # 5. 啟動心跳
    asyncio.create_task(heartbeat_manager.start_heartbeat_loop())

    yield  # 應用程式運行中

    # === 關閉階段 ===
    scheduler.shutdown()
    await close_database()
```

---

> 文件結束 | 後端工程師 | 2026-04-09
