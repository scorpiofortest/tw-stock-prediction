# 前端設計文件 — 台股實驗預測及模擬倉

> 版本：v1.0
> 角色：前端工程師
> 日期：2026-04-09

---

## 目錄

1. [技術棧選型](#1-技術棧選型)
2. [頁面架構設計](#2-頁面架構設計)
3. [核心元件設計](#3-核心元件設計)
4. [股票搜尋與輸入](#4-股票搜尋與輸入)
5. [響應式設計](#5-響應式設計)
6. [主題與設計規範](#6-主題與設計規範)
7. [前端架構](#7-前端架構)

---

## 1. 技術棧選型

### 1.1 前端框架：Next.js 14+ (App Router)

**選擇理由：**

| 比較項目 | Next.js | Vue.js (Nuxt) | 純 React (Vite) |
|---------|---------|---------------|-----------------|
| SSR/SSG 支援 | ✅ 內建 | ✅ 內建 | ❌ 需額外配置 |
| 路由系統 | ✅ 檔案式路由 | ✅ 檔案式路由 | ❌ 需 react-router |
| 生態系規模 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| TypeScript 整合 | ✅ 原生 | ✅ 原生 | ✅ 原生 |
| 即時數據場景 | ✅ Server Actions + Client | ✅ Composables | ✅ Hooks |
| 部署便利性 | ✅ Vercel 一鍵 | ✅ 多平台 | ✅ 多平台 |

**決策：** 選用 **Next.js 14+ (App Router + TypeScript)**，原因：
- 檔案式路由簡化頁面管理
- App Router 支援 Server Components，首屏載入更快
- 股票數據頁面可用 SSR 提升 SEO（若未來公開）
- React 生態系的圖表庫、UI 庫最為豐富
- Vercel 部署零配置，適合快速迭代

### 1.2 UI 元件庫：Shadcn/ui + Tailwind CSS

**選擇理由：**

| 比較項目 | Shadcn/ui + Tailwind | Ant Design | Material UI |
|---------|---------------------|------------|-------------|
| 自訂彈性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Bundle 大小 | 極小（按需引入原始碼） | 較大 | 較大 |
| 深色主題支援 | ✅ CSS 變數原生 | ✅ ConfigProvider | ✅ ThemeProvider |
| 金融風格適配 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 元件所有權 | 完整原始碼 copy | npm 依賴 | npm 依賴 |

**決策：** 選用 **Shadcn/ui**，原因：
- 元件原始碼直接 copy 到專案中，100% 可控可改
- 基於 Radix UI primitives，無障礙性佳
- Tailwind CSS 讓台股特有的紅漲綠跌配色能快速自訂
- 深色主題透過 CSS 變數切換，效能好

### 1.3 圖表庫：Lightweight Charts (TradingView) + ECharts

**選擇理由：**

| 用途 | 選用庫 | 理由 |
|------|--------|------|
| K 線走勢圖 | **lightweight-charts** (TradingView) | 專為金融圖表設計、高效能、即時更新、專業外觀 |
| 統計圖表（圓餅圖、雷達圖、折線圖） | **ECharts** | 圖表類型豐富、動畫效果佳、支援響應式 |
| 簡易小型圖表（迷你趨勢線等） | **Recharts** | 輕量、React 原生語法、適合小型嵌入圖 |

**K 線圖 (lightweight-charts) 特性：**
- 原生支援蠟燭圖（Candlestick）
- 內建十字游標 (crosshair)
- 支援多個技術指標疊加
- WebSocket 即時更新效能優異
- 體積僅 ~45KB gzipped

### 1.4 狀態管理：Zustand + React Query (TanStack Query)

| 用途 | 方案 | 理由 |
|------|------|------|
| 客戶端全域狀態 | **Zustand** | 極輕量（~1KB）、無 boilerplate、支援 middleware |
| 伺服器狀態快取 | **TanStack Query** | 自動快取/重新驗證、支援 WebSocket 整合 |
| 表單狀態 | **React Hook Form + Zod** | 高效能、Schema 驗證 |

**Zustand Store 規劃：**

```typescript
// stores/useStockStore.ts
interface StockStore {
  currentStock: string | null          // 當前選擇的股票代碼
  prediction: PredictionResult | null  // 即時推論結果
  signals: Signal[]                    // 9大訊號數據
  aiReasoning: string | null           // AI推論說明
  isAiEnabled: boolean                 // AI開關狀態
  setCurrentStock: (code: string) => void
  setPrediction: (result: PredictionResult) => void
}

// stores/usePortfolioStore.ts
interface PortfolioStore {
  holdings: Holding[]                  // 持倉列表
  cash: number                        // 現金餘額
  transactions: Transaction[]          // 交易記錄
  buy: (stock: string, qty: number, price: number) => void
  sell: (stock: string, qty: number, price: number) => void
}

// stores/useUIStore.ts
interface UIStore {
  theme: 'light' | 'dark'
  sidebarOpen: boolean
  activeTab: string
}
```

### 1.5 WebSocket 客戶端

選用原生 WebSocket + 自訂 hook 封裝，搭配 TanStack Query 整合：

```typescript
// hooks/useStockWebSocket.ts
function useStockWebSocket(stockCode: string) {
  const [status, setStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected')
  const queryClient = useQueryClient()

  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE_URL}/ws/stock/${stockCode}`)

    ws.onopen = () => setStatus('connected')

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      // 根據訊息類型更新對應的 query cache
      switch (data.type) {
        case 'prediction':
          queryClient.setQueryData(['prediction', stockCode], data.payload)
          break
        case 'signals':
          queryClient.setQueryData(['signals', stockCode], data.payload)
          break
        case 'price':
          queryClient.setQueryData(['price', stockCode], data.payload)
          break
      }
    }

    ws.onclose = () => {
      setStatus('disconnected')
      // 自動重連邏輯（指數退避）
    }

    return () => ws.close()
  }, [stockCode])

  return { status }
}
```

**重連策略：**
- 指數退避：1s → 2s → 4s → 8s → 最大 30s
- 頁面 visibility 切換時自動重連
- 心跳檢測（每 30 秒 ping）

### 1.6 完整技術棧總覽

```
框架：       Next.js 14+ (App Router, TypeScript)
UI 元件：    Shadcn/ui + Radix UI
樣式：       Tailwind CSS 3.4+
K 線圖表：   lightweight-charts (TradingView)
統計圖表：   ECharts 5 (apache-echarts)
小型圖表：   Recharts
狀態管理：   Zustand
伺服器快取：  TanStack Query v5
表單：       React Hook Form + Zod
WebSocket：  原生 + 自訂 hook
動畫：       Framer Motion
圖示：       Lucide React
日期處理：   date-fns
HTTP 客戶端：ky (或 fetch 原生)
```

---

## 2. 頁面架構設計

### 2.1 路由結構

```
app/
├── layout.tsx                    # 全域佈局（側邊欄 + 頂部欄）
├── page.tsx                      # 首頁 → 重導至 /dashboard
├── dashboard/
│   └── page.tsx                  # 儀表板（總覽）
├── stock/
│   └── [code]/
│       └── page.tsx              # 個股分析頁（動態路由）
├── portfolio/
│   ├── page.tsx                  # 模擬倉總覽
│   └── history/
│       └── page.tsx              # 交易歷史
├── statistics/
│   └── page.tsx                  # 歷史記錄與統計
├── settings/
│   └── page.tsx                  # 設定頁
└── api/                          # API Route (BFF 層，如需要)
```

### 2.2 各頁面功能說明

#### 📊 首頁 / 儀表板 (`/dashboard`)

主要功能：一目了然看到所有核心資訊

```
┌─────────────────────────────────────────────────────────┐
│ [🔍 股票搜尋欄]                    [主題切換] [設定⚙️]  │
├──────────┬──────────────────────────────────────────────┤
│          │  ┌─────────────────────────────────────────┐ │
│  側      │  │         即時推論顯示區（大字）            │ │
│  邊      │  │     📈 看漲  信心值: 78%                │ │
│  欄      │  └─────────────────────────────────────────┘ │
│          │  ┌──────────────┐ ┌────────────────────────┐ │
│  常      │  │  9大訊號儀表板 │ │    AI 推論說明區塊     │ │
│  用      │  │  (雷達圖+卡片) │ │  「根據RSI超賣、MACD  │ │
│  股      │  │              │ │   金叉及外資買超...」   │ │
│  票      │  └──────────────┘ └────────────────────────┘ │
│  列      │  ┌─────────────────────────────────────────┐ │
│  表      │  │         即時走勢圖 (K線+指標)            │ │
│          │  │                                         │ │
│          │  └─────────────────────────────────────────┘ │
│          │  ┌──────────────┐ ┌────────────────────────┐ │
│          │  │  模擬倉摘要   │ │    驗證統計摘要        │ │
│          │  └──────────────┘ └────────────────────────┘ │
├──────────┴──────────────────────────────────────────────┤
│ 底部狀態列：WebSocket 連線狀態 | 最後更新時間 | 版本     │
└─────────────────────────────────────────────────────────┘
```

**區塊說明：**
- 上方為股票搜尋欄，始終可見
- 核心區域以「即時推論結果」為視覺重心
- 下方分為左右兩欄：訊號儀表板 + AI 推論
- 走勢圖佔據全寬
- 底部為模擬倉摘要與驗證統計摘要

#### 📈 個股分析頁 (`/stock/[code]`)

專注於單一股票的深度分析：

```
┌─────────────────────────────────────────────────────────┐
│ ← 返回  |  2330 台積電  |  NT$890 ▲+15 (+1.71%)       │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────────────────┐ ┌──────────────────────┐  │
│  │    推論結果 + 信心值       │ │   AI 推論卡片        │  │
│  │    📈 看漲 82%           │ │                      │  │
│  └──────────────────────────┘ └──────────────────────┘  │
│  ┌─────────────────────────────────────────────────────┐│
│  │              完整 K 線走勢圖                         ││
│  │    (含 RSI / MACD / KD 子圖可切換)                  ││
│  │    (含買賣點標記 ● 買 ○ 賣)                         ││
│  └─────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────┐│
│  │     9大訊號詳細卡片（3×3 Grid）                      ││
│  │  [RSI] [MACD] [KD] [布林] [成交量] [外資] ...      ││
│  └─────────────────────────────────────────────────────┘│
│  ┌──────────────────────────┐ ┌──────────────────────┐  │
│  │    歷史預測準確率          │ │   快速交易面板        │  │
│  │    (折線圖)              │ │   [買入] [賣出]       │  │
│  └──────────────────────────┘ └──────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

#### 💼 模擬倉管理頁 (`/portfolio`)

```
┌─────────────────────────────────────────────────────────┐
│  總資產摘要                                              │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐           │
│  │總資產   │ │持倉市值 │ │可用現金 │ │總損益   │           │
│  │$1,234k │ │$890k  │ │$344k  │ │+$56k  │           │
│  └────────┘ └────────┘ └────────┘ └────────┘           │
├─────────────────────────────────────────────────────────┤
│  持倉列表 (Table)                                       │
│  ┌──────┬──────┬──────┬──────┬──────┬──────┬────────┐  │
│  │ 股票 │ 數量 │ 成本  │ 現價  │ 損益  │ 損益% │  操作  │  │
│  ├──────┼──────┼──────┼──────┼──────┼──────┼────────┤  │
│  │ 2330 │ 1000 │ 875  │ 890  │+15k │+1.7%│ [賣出] │  │
│  │ 2317 │ 2000 │ 112  │ 118  │+12k │+5.4%│ [賣出] │  │
│  └──────┴──────┴──────┴──────┴──────┴──────┴────────┘  │
├─────────────────────────────────────────────────────────┤
│  資產配置圓餅圖  |  損益走勢折線圖                        │
├─────────────────────────────────────────────────────────┤
│  近期交易記錄 (Table)                                    │
│  ┌────────┬──────┬──────┬──────┬──────┬────────────┐   │
│  │ 時間   │ 股票 │ 方向  │ 數量 │ 價格  │   金額     │   │
│  ├────────┼──────┼──────┼──────┼──────┼────────────┤   │
│  │ 04/09  │ 2330 │ 買入  │ 500 │ 890  │  $445,000 │   │
│  └────────┴──────┴──────┴──────┴──────┴────────────┘   │
└─────────────────────────────────────────────────────────┘
```

#### 📉 歷史記錄與統計頁 (`/statistics`)

```
┌─────────────────────────────────────────────────────────┐
│  篩選列：[日期範圍] [股票] [預測方向]                      │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────────────────┐ ┌──────────────────────┐  │
│  │   整體成功率              │ │   各訊號準確率        │  │
│  │   🎯 73.2%              │ │   (橫向長條圖)        │  │
│  │   (大字+環形進度條)       │ │                      │  │
│  └──────────────────────────┘ └──────────────────────┘  │
│  ┌─────────────────────────────────────────────────────┐│
│  │  成功率趨勢折線圖（按日/週/月）                       ││
│  └─────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────┐│
│  │  預測記錄列表                                        ││
│  │  ┌────────┬──────┬──────┬──────┬──────┬──────────┐ ││
│  │  │ 日期   │ 股票 │ 預測  │ 實際 │ 信心值│  結果    │ ││
│  │  ├────────┼──────┼──────┼──────┼──────┼──────────┤ ││
│  │  │ 04/08  │ 2330 │ 📈漲 │ ↑漲  │ 78%  │  ✅ 正確 │ ││
│  │  │ 04/08  │ 2317 │ 📉跌 │ ↑漲  │ 55%  │  ❌ 錯誤 │ ││
│  │  └────────┴──────┴──────┴──────┴──────┴──────────┘ ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

#### ⚙️ 設定頁 (`/settings`)

```
┌─────────────────────────────────────────────────────────┐
│  一般設定                                                │
│  ├── 主題切換（深色/淺色/跟隨系統）                       │
│  ├── 語言（繁體中文）                                    │
│  └── 通知設定                                           │
│                                                         │
│  AI 設定                                                │
│  ├── AI 推論開關                                        │
│  ├── AI 模型選擇                                        │
│  └── 推論自動更新頻率                                    │
│                                                         │
│  模擬倉設定                                              │
│  ├── 初始資金設定                                        │
│  ├── 手續費率設定（預設 0.1425%）                         │
│  ├── 證交稅設定（預設 0.3%）                              │
│  └── 重置模擬倉                                         │
│                                                         │
│  數據設定                                                │
│  ├── 資料更新頻率                                        │
│  ├── WebSocket 連線設定                                  │
│  └── 快取清除                                           │
│                                                         │
│  關於                                                    │
│  ├── 版本資訊                                           │
│  └── 技術說明                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 核心元件設計

### 3.1 即時推論顯示區（核心視覺）

此元件為整個應用的視覺重心，必須在第一眼就傳達清楚的漲跌訊息。

#### 元件結構

```typescript
// components/prediction/PredictionDisplay.tsx
interface PredictionDisplayProps {
  direction: 'bullish' | 'bearish' | 'neutral'
  confidence: number        // 0-100
  stockCode: string
  stockName: string
  isLoading: boolean
  lastUpdated: Date
}
```

#### 視覺設計

```
┌───────────────────────────────────────────────┐
│                                               │
│            ┌─────────────────┐                │
│            │   ╭──────────╮  │                │
│            │   │  78%     │  │  ← 環形進度條   │
│            │   │ 信心值    │  │    動態填充     │
│            │   ╰──────────╯  │                │
│            └─────────────────┘                │
│                                               │
│          📈  看    漲                          │
│     (72px 粗體，帶入場動畫)                     │
│                                               │
│    ────────────────────────────                │
│    2330 台積電  |  NT$890  ▲+1.71%            │
│    最後更新：2026/04/09 13:30:25              │
└───────────────────────────────────────────────┘
```

#### 顏色方案（台股慣例：紅漲綠跌）

| 狀態 | 背景色 | 文字色 | 圖示 | 動畫 |
|------|--------|--------|------|------|
| 📈 看漲 (Bullish) | `bg-red-50/dark:bg-red-950` | `text-red-600/dark:text-red-400` | 向上箭頭 | 向上彈跳 (bounceUp) |
| 📉 看跌 (Bearish) | `bg-green-50/dark:bg-green-950` | `text-green-600/dark:text-green-400` | 向下箭頭 | 向下滑入 (slideDown) |
| ⚖️ 中性 (Neutral) | `bg-yellow-50/dark:bg-yellow-950` | `text-yellow-600/dark:text-yellow-400` | 橫向箭頭 | 左右擺動 (swing) |

#### 環形進度條設計

```typescript
// components/prediction/ConfidenceRing.tsx
// 使用 SVG 繪製環形進度條
// - 外圈：灰色底色
// - 內圈：根據方向填充對應顏色
// - 中心：數字百分比
// - 動畫：從 0% 漸增到目標值（spring 物理動畫）

const ConfidenceRing = ({ value, direction }: Props) => {
  const color = {
    bullish: 'stroke-red-500',
    bearish: 'stroke-green-500',
    neutral: 'stroke-yellow-500',
  }[direction]

  // SVG 環形 + Framer Motion 動畫
  return (
    <motion.svg viewBox="0 0 120 120">
      {/* 背景圈 */}
      <circle cx="60" cy="60" r="50" strokeWidth="10"
        className="stroke-gray-200 dark:stroke-gray-700" fill="none" />
      {/* 進度圈 */}
      <motion.circle cx="60" cy="60" r="50" strokeWidth="10"
        className={color} fill="none"
        strokeLinecap="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: value / 100 }}
        transition={{ type: 'spring', duration: 1.5 }} />
      {/* 中心文字 */}
      <text x="60" y="55" textAnchor="middle" className="text-2xl font-bold">
        {value}%
      </text>
      <text x="60" y="75" textAnchor="middle" className="text-sm text-muted">
        信心值
      </text>
    </motion.svg>
  )
}
```

#### 動畫效果設計

| 事件 | 動畫 | 持續時間 | 緩動函數 |
|------|------|---------|---------|
| 結果首次載入 | 淡入 + 縮放 (fadeIn + scale) | 600ms | easeOutBack |
| 方向切換（漲→跌） | 舊結果淡出 → 新結果滑入 | 800ms | easeInOutCubic |
| 信心值變化 | 數字滾動 (countUp) | 1000ms | spring |
| 環形進度更新 | 弧度平滑過渡 | 1500ms | spring (stiffness: 100) |
| 脈衝提示（新推論到達） | 邊框脈衝光暈 | 2000ms | 循環 2 次 |

### 3.2 9 大訊號儀表板

#### 訊號卡片設計

每個訊號以獨立卡片呈現，3×3 網格排列：

```
┌──────────────────┐
│  RSI 指標    📊   │  ← 訊號名稱 + 圖示
│                  │
│  ████████░░  72  │  ← 進度條 + 數值
│                  │
│  偏多 ▲           │  ← 訊號方向 + 箭頭
│  權重: 15%       │  ← 該訊號在總評分中的權重
│  ──────────────  │
│  📈 看漲信號      │  ← 一句話解讀
└──────────────────┘
```

```typescript
// components/signals/SignalCard.tsx
interface SignalCardProps {
  name: string             // 訊號名稱
  icon: string             // 圖示
  value: number            // 當前值
  direction: 'bullish' | 'bearish' | 'neutral'
  weight: number           // 權重百分比
  description: string      // 簡短解讀
  history: number[]        // 迷你歷史趨勢（用於 sparkline）
}
```

**9 大訊號卡片列表：**

| 訊號 | 圖示 | 顏色標識 |
|------|------|---------|
| RSI (相對強弱指標) | 📊 | 根據超買/超賣區間變色 |
| MACD (異同移動平均) | 📉 | 金叉紅/死叉綠 |
| KD (隨機指標) | 📈 | 根據交叉狀態變色 |
| 布林通道 | 〰️ | 觸及上/下軌變色 |
| 成交量分析 | 📦 | 放量紅/縮量灰 |
| 外資買賣超 | 🏦 | 買超紅/賣超綠 |
| 投信買賣超 | 🏛️ | 買超紅/賣超綠 |
| 融資融券比 | ⚖️ | 根據比值區間變色 |
| 均線排列 | 📐 | 多頭排列紅/空頭排列綠 |

#### 雷達圖設計

使用 ECharts 雷達圖呈現 9 大訊號的整體強度：

```typescript
// components/signals/SignalRadarChart.tsx
const radarOption = {
  radar: {
    indicator: [
      { name: 'RSI', max: 100 },
      { name: 'MACD', max: 100 },
      { name: 'KD', max: 100 },
      { name: '布林通道', max: 100 },
      { name: '成交量', max: 100 },
      { name: '外資', max: 100 },
      { name: '投信', max: 100 },
      { name: '融資融券', max: 100 },
      { name: '均線', max: 100 },
    ],
    shape: 'polygon',         // 多邊形形狀
    splitNumber: 4,           // 4 層同心圓
    axisName: {
      color: 'var(--text-secondary)',
    },
  },
  series: [{
    type: 'radar',
    data: [{
      value: [72, 65, 80, 55, 90, 78, 45, 60, 85],
      name: '訊號強度',
      areaStyle: {
        color: 'rgba(239, 68, 68, 0.2)',   // 半透明紅色填充
      },
      lineStyle: {
        color: '#ef4444',
      },
    }],
    animationDuration: 1500,
  }],
}
```

#### 即時更新動畫

- 數值變化時：數字帶 countUp 動畫（平滑滾動到新值）
- 方向改變時：卡片邊框閃爍對應顏色 (pulse animation)
- 新數據到達：卡片右上角出現小圓點 (notification dot) 閃爍 2 秒後消失
- 雷達圖更新：資料點平滑過渡到新位置 (300ms ease)

### 3.3 AI 推論區塊

#### 推論卡片設計

```
┌──────────────────────────────────────────────┐
│  🤖 AI 智慧推論              [AI ON 🔘]      │
│  ─────────────────────────────────────────── │
│                                              │
│  「根據目前技術指標分析，RSI 位於 72 接近超     │
│   買區，但 MACD 出現金叉搭配外資連續 3 日買     │
│   超共計 15,000 張，短線偏多看待。」            │
│                                              │
│  ─────────────────────────────────────────── │
│  ⏱️ 生成時間：1.2 秒  |  模型：Claude        │
│  📅 2026/04/09 13:30                         │
└──────────────────────────────────────────────┘
```

#### AI 開關按鈕設計

```typescript
// components/ai/AIToggle.tsx
// 使用 Shadcn Switch 元件
// OFF 狀態：灰色，顯示「AI 已關閉」
// ON 狀態：藍色漸變，顯示「AI 已啟用」
// 切換動畫：滑動 + 顏色漸變 (300ms)

const AIToggle = () => {
  const { isAiEnabled, toggleAi } = useStockStore()

  return (
    <div className="flex items-center gap-2">
      <Switch
        checked={isAiEnabled}
        onCheckedChange={toggleAi}
        className="data-[state=checked]:bg-gradient-to-r
                   data-[state=checked]:from-blue-500
                   data-[state=checked]:to-purple-500"
      />
      <span className="text-sm">
        {isAiEnabled ? 'AI 已啟用' : 'AI 已關閉'}
      </span>
    </div>
  )
}
```

#### 載入中狀態

```typescript
// 打字機效果的骨架屏
// 三個脈動圓點 + 「AI 正在分析...」文字
// 模擬文字逐字出現的效果（typewriter animation）

const AILoadingState = () => (
  <div className="space-y-3 animate-pulse">
    <div className="flex items-center gap-2">
      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" />
      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce [animation-delay:0.2s]" />
      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce [animation-delay:0.4s]" />
      <span className="text-sm text-muted-foreground">AI 正在分析中...</span>
    </div>
    <div className="h-4 bg-muted rounded w-full" />
    <div className="h-4 bg-muted rounded w-4/5" />
    <div className="h-4 bg-muted rounded w-3/5" />
  </div>
)
```

**AI 推論文字呈現動畫：** 文字以打字機效果逐字出現（每字間隔 30ms），模擬 AI 即時生成的感覺。

### 3.4 即時走勢圖

#### K 線圖整合 (lightweight-charts)

```typescript
// components/chart/StockChart.tsx
interface StockChartProps {
  stockCode: string
  timeframe: '1m' | '5m' | '15m' | '30m' | '1h' | '1d' | '1w' | '1M'
  showIndicators: ('RSI' | 'MACD' | 'KD')[]
  tradeMarkers?: TradeMarker[]
}

// 圖表配置
const chartOptions = {
  layout: {
    background: { type: ColorType.Solid, color: 'transparent' },
    textColor: 'var(--chart-text)',
  },
  grid: {
    vertLines: { color: 'var(--chart-grid)' },
    horzLines: { color: 'var(--chart-grid)' },
  },
  crosshair: {
    mode: CrosshairMode.Normal,
  },
  timeScale: {
    timeVisible: true,
    secondsVisible: false,
    borderColor: 'var(--chart-border)',
  },
  // 台股慣例：紅漲綠跌
  upColor: '#ef4444',        // 紅色上漲
  downColor: '#22c55e',      // 綠色下跌
  wickUpColor: '#ef4444',
  wickDownColor: '#22c55e',
  borderUpColor: '#ef4444',
  borderDownColor: '#22c55e',
}
```

#### 技術指標子圖

```
┌─────────────────────────────────────────────────┐
│  2330 台積電  [1分][5分][15分][日][週][月]         │
│  ┌─────────────────────────────────────────────┐│
│  │                                             ││
│  │           K 線主圖                           ││
│  │     (含均線 MA5/MA10/MA20/MA60)              ││
│  │     (含買賣點標記)                            ││
│  │                                             ││
│  ├─────────────────────────────────────────────┤│
│  │  成交量柱狀圖                                ││
│  ├────────────────────── [RSI ✓][MACD ✓][KD ✓]─┤│
│  │  RSI 指標子圖                                ││
│  │  ---- 超買線 (70) ---- 超賣線 (30) ----      ││
│  ├─────────────────────────────────────────────┤│
│  │  MACD 指標子圖                               ││
│  │  DIF 線 / DEA 線 / MACD 柱狀                 ││
│  ├─────────────────────────────────────────────┤│
│  │  KD 指標子圖                                 ││
│  │  K 線 / D 線                                 ││
│  └─────────────────────────────────────────────┘│
└─────────────────────────────────────────────────┘
```

**指標子圖切換：** 使用 Checkbox 勾選要顯示的指標，動態新增/移除子圖面板。

#### 買賣點標記

```typescript
// 在 K 線上標記模擬倉的買賣操作
interface TradeMarker {
  time: number
  position: 'aboveBar' | 'belowBar'
  color: string
  shape: 'arrowUp' | 'arrowDown' | 'circle'
  text: string
}

// 買入標記：紅色向上箭頭，位於 K 線下方
// 賣出標記：綠色向下箭頭，位於 K 線上方
const markers: TradeMarker[] = trades.map(trade => ({
  time: trade.timestamp,
  position: trade.type === 'buy' ? 'belowBar' : 'aboveBar',
  color: trade.type === 'buy' ? '#ef4444' : '#22c55e',
  shape: trade.type === 'buy' ? 'arrowUp' : 'arrowDown',
  text: trade.type === 'buy' ? `買 ${trade.qty}` : `賣 ${trade.qty}`,
}))
```

### 3.5 模擬倉介面

#### 持倉列表

```typescript
// components/portfolio/HoldingsTable.tsx
interface Holding {
  stockCode: string
  stockName: string
  quantity: number
  avgCost: number          // 平均成本
  currentPrice: number     // 現價
  pnl: number             // 損益金額
  pnlPercent: number      // 損益百分比
  marketValue: number     // 市值
}

// 表格欄位設計
const columns = [
  { key: 'stock', label: '股票', render: (h) => `${h.stockCode} ${h.stockName}` },
  { key: 'quantity', label: '持有張數', align: 'right' },
  { key: 'avgCost', label: '平均成本', align: 'right', format: 'currency' },
  { key: 'currentPrice', label: '現價', align: 'right', format: 'currency' },
  { key: 'pnl', label: '損益', align: 'right', format: 'pnl' },           // 紅正綠負
  { key: 'pnlPercent', label: '損益%', align: 'right', format: 'pnlPct' }, // 紅正綠負
  { key: 'action', label: '操作', render: (h) => <SellButton holding={h} /> },
]
```

**損益顏色規則：**
- 正數（獲利）：紅色文字 `text-red-600`
- 負數（虧損）：綠色文字 `text-green-600`
- 零：灰色文字 `text-gray-500`

#### 買入/賣出操作面板

```
┌──────────────────────────────────────┐
│  交易面板                    [買入|賣出] ← Tab 切換
│  ─────────────────────────────────── │
│                                      │
│  股票代碼：[2330 台積電      🔍]      │
│  現價：    NT$ 890.00                │
│                                      │
│  數量(張)：[    1    ] [-] [+]       │
│  預估金額：NT$ 890,000               │
│                                      │
│  手續費：  NT$ 1,268 (0.1425%)       │
│  證交稅：  NT$ 0 (買入免稅)           │
│  ─────────────────────────────────── │
│  總計：    NT$ 891,268               │
│                                      │
│  可用餘額：NT$ 1,500,000             │
│                                      │
│  [      確認買入      ]  ← 紅色按鈕   │
└──────────────────────────────────────┘
```

**賣出面板差異：**
- 確認按鈕變為綠色「確認賣出」
- 顯示預估損益
- 顯示證交稅（0.3%）
- 顯示可賣數量上限

#### 交易記錄表格

```typescript
// components/portfolio/TransactionTable.tsx
interface Transaction {
  id: string
  timestamp: Date
  stockCode: string
  stockName: string
  type: 'buy' | 'sell'
  quantity: number
  price: number
  fee: number              // 手續費
  tax: number              // 證交稅
  totalAmount: number      // 實際金額
}

// 篩選功能
// - 日期範圍
// - 股票代碼
// - 買入/賣出
// - 分頁（每頁 20 筆）
```

#### 總資產/總損益摘要

```typescript
// components/portfolio/PortfolioSummary.tsx
// 4 個統計卡片橫排顯示

interface PortfolioSummaryData {
  totalAssets: number      // 總資產 = 持倉市值 + 現金
  marketValue: number      // 持倉市值
  cash: number            // 可用現金
  totalPnL: number        // 總損益（已實現 + 未實現）
  totalPnLPercent: number // 總報酬率
  realizedPnL: number     // 已實現損益
  unrealizedPnL: number   // 未實現損益
}

// 每張卡片設計：
// ┌────────────┐
// │ 📊 總資產   │
// │ $1,234,000 │  ← 大字數字
// │ ▲ +5.2%    │  ← 變化百分比（帶顏色）
// └────────────┘
```

### 3.6 自動驗證統計

#### 成功率視覺化

```typescript
// components/statistics/AccuracyChart.tsx

// 1. 環形進度條 - 整體成功率
// 大字顯示，搭配環形進度條
// 例：🎯 73.2% (182/249 筆正確)

// 2. 折線圖 - 成功率趨勢
// X軸：日期
// Y軸：成功率百分比
// 可切換：日/週/月 粒度
// 參考線：50% 基準線（紅色虛線）

// 3. 圓餅圖 - 預測分佈
// 看漲正確 / 看漲錯誤 / 看跌正確 / 看跌錯誤 / 中性
```

#### 預測記錄列表

```typescript
// components/statistics/PredictionHistory.tsx
interface PredictionRecord {
  id: string
  date: Date
  stockCode: string
  stockName: string
  predictedDirection: 'bullish' | 'bearish' | 'neutral'
  confidence: number
  actualDirection: 'up' | 'down' | 'flat'
  actualChange: number        // 實際漲跌幅 %
  isCorrect: boolean
  signals: SignalSnapshot[]   // 當時的訊號快照
}

// 列表顯示：
// | 日期 | 股票 | 預測方向 | 信心值 | 實際漲跌 | 結果 |
// 結果欄：✅ 綠底 / ❌ 紅底
// 支援展開查看當時的詳細訊號資料
```

#### 各訊號單獨準確率

```typescript
// components/statistics/SignalAccuracy.tsx
// 橫向長條圖，每個訊號一條

// RSI     ████████████████░░░░  78.3%
// MACD    ██████████████░░░░░░  71.2%
// KD      █████████████░░░░░░░  68.9%
// 布林通道  ████████████░░░░░░░░  65.4%
// 成交量   ███████████████░░░░░  74.1%
// 外資     ██████████████████░░  82.5%
// 投信     ██████████████░░░░░░  70.3%
// 融資融券  ███████████░░░░░░░░░  62.8%
// 均線     ████████████████░░░░  76.7%

// 顏色規則：
// ≥ 75%：綠色（優秀）
// 60-75%：黃色（普通）
// < 60%：紅色（需改進）
```

---

## 4. 股票搜尋與輸入

### 4.1 搜尋輸入框設計

```typescript
// components/search/StockSearch.tsx
// 使用 Shadcn Command (cmdk) 元件

interface StockSearchProps {
  onSelect: (stock: StockInfo) => void
  placeholder?: string
}
```

**視覺設計：**

```
┌──────────────────────────────────────────────┐
│ 🔍  輸入股票代碼或名稱...           ⌘K       │
└──────────────────────────────────────────────┘
            ↓ 輸入 "233" 或 "台積" 時展開
┌──────────────────────────────────────────────┐
│  最近搜尋                                     │
│  ├── 2330 台積電                              │
│  └── 2317 鴻海                               │
│  ─────────────────────────────────────────── │
│  搜尋結果                                     │
│  ├── 2330 台積電     NT$890  ▲+1.71%        │
│  ├── 2331 精英       NT$25   ▼-0.40%        │
│  └── 2337 旺宏       NT$31   ▲+2.31%        │
│  ─────────────────────────────────────────── │
│  熱門股票                                     │
│  ├── 2330 台積電                              │
│  ├── 2454 聯發科                              │
│  └── 0050 元大台灣50                          │
└──────────────────────────────────────────────┘
```

**功能規格：**
- 支援股票代碼搜尋（例：2330）
- 支援中文名稱搜尋（例：台積電）
- 支援模糊搜尋（例：台積 → 台積電）
- 鍵盤快捷鍵 `⌘K` / `Ctrl+K` 全域喚出
- 方向鍵上下選擇 + Enter 確認
- 防抖搜尋（debounce 300ms）
- 顯示即時價格與漲跌

### 4.2 常用股票快捷列表

```typescript
// components/search/FavoriteStocks.tsx
// 側邊欄顯示，支援拖拽排序

// ⭐ 常用股票
// ┌──────────────────────┐
// │ 2330 台積電   $890 ▲ │  ← 點擊直接切換
// │ 2317 鴻海     $118 ▲ │
// │ 2454 聯發科   $1250▼ │
// │ 0050 台灣50   $165 ▲ │
// │ [+ 新增股票]          │
// └──────────────────────┘

// 功能：
// - 點擊星號收藏/取消
// - 拖拽排序
// - 即時價格與漲跌色彩
// - 存儲於 localStorage
```

### 4.3 搜尋建議下拉選單

使用 `cmdk` (Command Menu) 實現：

```typescript
// 基於 Shadcn 的 CommandDialog
import { CommandDialog, CommandInput, CommandList,
         CommandGroup, CommandItem } from '@/components/ui/command'

const StockCommandMenu = () => {
  const [open, setOpen] = useState(false)

  // ⌘K 快捷鍵
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen(prev => !prev)
      }
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [])

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="搜尋股票代碼或名稱..." />
      <CommandList>
        <CommandGroup heading="最近搜尋">
          {recentStocks.map(stock => (
            <CommandItem key={stock.code}>
              {stock.code} {stock.name}
            </CommandItem>
          ))}
        </CommandGroup>
        <CommandGroup heading="搜尋結果">
          {searchResults.map(stock => (
            <CommandItem key={stock.code}>
              <span>{stock.code} {stock.name}</span>
              <span className={stock.change > 0 ? 'text-red-500' : 'text-green-500'}>
                ${stock.price} {stock.change > 0 ? '▲' : '▼'}{stock.changePercent}%
              </span>
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  )
}
```

---

## 5. 響應式設計

### 5.1 斷點定義

| 斷點 | 寬度範圍 | 裝置類型 | Tailwind Class |
|------|---------|---------|----------------|
| xs | < 640px | 手機直向 | 預設 |
| sm | 640px - 767px | 手機橫向 | `sm:` |
| md | 768px - 1023px | 平板 | `md:` |
| lg | 1024px - 1279px | 小螢幕桌面 | `lg:` |
| xl | 1280px - 1535px | 桌面 | `xl:` |
| 2xl | ≥ 1536px | 大螢幕桌面 | `2xl:` |

### 5.2 桌面版佈局 (≥ 1024px)

```
┌──────────────────────────────────────────────────────┐
│  頂部導覽列 (64px)                                    │
│  Logo | 搜尋 | 通知 | 主題切換 | 設定                  │
├────────────┬─────────────────────────────────────────┤
│            │                                         │
│  側邊欄     │              主內容區                    │
│  (240px)   │              (fluid)                    │
│            │                                         │
│  導覽選單   │   2-3 欄 Grid 佈局                      │
│  常用股票   │   圖表全寬                               │
│            │                                         │
│  可收合 ←→ │                                         │
│            │                                         │
├────────────┴─────────────────────────────────────────┤
│  底部狀態列 (32px)                                    │
└──────────────────────────────────────────────────────┘
```

**特點：**
- 側邊欄固定左側，可收合為 icon-only 模式 (64px)
- 主內容區使用 CSS Grid 佈局，最多 3 欄
- K 線圖佔據全寬
- 訊號卡片 3×3 網格
- 模擬倉表格完整顯示

### 5.3 平板版佈局 (768px - 1023px)

```
┌──────────────────────────────────────┐
│  頂部導覽列 (56px)                    │
│  ☰ | Logo | 搜尋 | 設定              │
├──────────────────────────────────────┤
│                                      │
│           主內容區 (全寬)              │
│                                      │
│   2 欄 Grid 佈局                     │
│   圖表全寬                            │
│   訊號卡片 3×2 或 2×3                 │
│                                      │
├──────────────────────────────────────┤
│  底部 Tab 導覽                        │
│  [儀表板] [分析] [模擬倉] [統計] [設定] │
└──────────────────────────────────────┘
```

**調整策略：**
- 側邊欄改為抽屜式 (drawer)，漢堡選單觸發
- 底部增加 Tab 導覽列
- 訊號卡片從 3×3 改為 3×3 但尺寸縮小
- 交易面板改為 Modal 彈出

### 5.4 手機版佈局 (< 768px)

```
┌────────────────────────┐
│  頂部列 (48px)          │
│  ☰ | 搜尋 | ⋮           │
├────────────────────────┤
│                        │
│   推論結果（堆疊排列）   │
│   大字 + 信心值          │
│                        │
│   ─ Tab 切換 ─         │
│   [訊號][圖表][AI][倉位] │
│                        │
│   依選中 Tab 顯示        │
│   單一內容區             │
│                        │
│                        │
│                        │
├────────────────────────┤
│  底部 Tab 導覽          │
│  [首頁][分析][倉位][我的] │
└────────────────────────┘
```

**調整策略：**
- 推論結果永遠在最上方（核心資訊）
- 下方使用 Tab 切換不同內容區（而非同時顯示）
- 訊號卡片改為橫向滑動卡片 (horizontal scroll snap)
- K 線圖全寬，支援手勢縮放
- 交易操作改為底部抽屜 (bottom sheet)
- 表格改為卡片式列表

### 5.5 各裝置元件調整策略總覽

| 元件 | 桌面 | 平板 | 手機 |
|------|------|------|------|
| 側邊欄 | 固定顯示 (240px) | 抽屜式 | 隱藏 |
| 導覽 | 側邊欄選單 | 底部 Tab + 抽屜 | 底部 Tab |
| 推論結果 | 卡片 (1/2 寬) | 卡片 (全寬) | 頂部固定 |
| 信心環形 | 120×120px | 100×100px | 80×80px |
| 訊號卡片 | 3×3 網格 | 3×3 小卡 | 橫向滑動 |
| 雷達圖 | 400×400px | 300×300px | 280×280px |
| K 線圖 | 全寬，高 400px | 全寬，高 350px | 全寬，高 280px |
| 指標子圖 | 全部顯示 | 可折疊 | 預設收合 |
| 持倉列表 | 完整表格 | 精簡表格 | 卡片列表 |
| 交易面板 | 側邊面板 | Modal | 底部 Sheet |
| 統計圖表 | 並排 2 欄 | 堆疊 | 堆疊 + 簡化 |

---

## 6. 主題與設計規範

### 6.1 色彩系統

#### 基礎色彩 (CSS Variables)

```css
/* globals.css */
:root {
  /* 淺色主題 */
  --background: 0 0% 100%;           /* #ffffff */
  --foreground: 222 47% 11%;         /* #0f172a */
  --card: 0 0% 100%;
  --card-foreground: 222 47% 11%;
  --popover: 0 0% 100%;
  --popover-foreground: 222 47% 11%;
  --primary: 222 47% 11%;
  --primary-foreground: 210 40% 98%;
  --secondary: 210 40% 96%;
  --secondary-foreground: 222 47% 11%;
  --muted: 210 40% 96%;
  --muted-foreground: 215 16% 47%;
  --accent: 210 40% 96%;
  --accent-foreground: 222 47% 11%;
  --border: 214 32% 91%;
  --ring: 222 47% 11%;

  /* 台股專用色彩 */
  --stock-up: 0 84% 60%;             /* #ef4444 紅色-上漲 */
  --stock-down: 142 71% 45%;         /* #22c55e 綠色-下跌 */
  --stock-flat: 48 96% 53%;          /* #eab308 黃色-平盤 */
  --stock-up-bg: 0 86% 97%;          /* #fef2f2 漲的背景 */
  --stock-down-bg: 138 76% 97%;      /* #f0fdf4 跌的背景 */
  --stock-flat-bg: 48 100% 96%;      /* #fefce8 平盤背景 */

  /* 圖表色彩 */
  --chart-grid: 214 32% 91%;
  --chart-text: 215 16% 47%;
  --chart-border: 214 32% 91%;

  /* 訊號色彩 */
  --signal-bullish: 0 84% 60%;       /* 看漲訊號 */
  --signal-bearish: 142 71% 45%;     /* 看跌訊號 */
  --signal-neutral: 48 96% 53%;      /* 中性訊號 */
}

.dark {
  /* 深色主題 */
  --background: 222 47% 5%;           /* #020817 */
  --foreground: 210 40% 98%;          /* #f8fafc */
  --card: 222 47% 8%;
  --card-foreground: 210 40% 98%;
  --popover: 222 47% 8%;
  --popover-foreground: 210 40% 98%;
  --primary: 210 40% 98%;
  --primary-foreground: 222 47% 11%;
  --secondary: 217 33% 17%;
  --secondary-foreground: 210 40% 98%;
  --muted: 217 33% 17%;
  --muted-foreground: 215 20% 65%;
  --accent: 217 33% 17%;
  --accent-foreground: 210 40% 98%;
  --border: 217 33% 17%;
  --ring: 210 40% 80%;

  /* 台股專用色彩 (深色模式適配) */
  --stock-up: 0 72% 51%;              /* 紅色-略暗 */
  --stock-down: 142 64% 40%;          /* 綠色-略暗 */
  --stock-flat: 48 89% 50%;           /* 黃色-略暗 */
  --stock-up-bg: 0 60% 12%;           /* 漲的深色背景 */
  --stock-down-bg: 142 50% 10%;       /* 跌的深色背景 */
  --stock-flat-bg: 48 50% 10%;        /* 平盤深色背景 */

  /* 圖表色彩 (深色) */
  --chart-grid: 217 33% 20%;
  --chart-text: 215 20% 65%;
  --chart-border: 217 33% 20%;
}
```

#### 語意色彩

| 用途 | 淺色模式 | 深色模式 | CSS 變數 |
|------|---------|---------|---------|
| 上漲/看漲 | `#ef4444` (紅) | `#f87171` (淺紅) | `--stock-up` |
| 下跌/看跌 | `#22c55e` (綠) | `#4ade80` (淺綠) | `--stock-down` |
| 平盤/中性 | `#eab308` (黃) | `#facc15` (淺黃) | `--stock-flat` |
| 成功/正確 | `#22c55e` (綠) | `#4ade80` | -- |
| 錯誤/失敗 | `#ef4444` (紅) | `#f87171` | -- |
| AI 功能 | `#3b82f6→#8b5cf6` (藍紫漸層) | 同左但亮度提高 | -- |
| 連線中 | `#22c55e` (綠點) | 同左 | -- |
| 離線 | `#ef4444` (紅點) | 同左 | -- |

> **重要提醒：** 台股慣例為「紅漲綠跌」，與美股相反。此配色貫穿整個應用。

### 6.2 字體規範

```css
/* 字體堆疊 */
--font-sans: "Inter", "Noto Sans TC", -apple-system, BlinkMacSystemFont,
             "Segoe UI", Roboto, sans-serif;
--font-mono: "JetBrains Mono", "Fira Code", "SF Mono", Consolas, monospace;
```

| 用途 | 字體 | 大小 | 粗細 | 行高 |
|------|------|------|------|------|
| 推論結果大字 | Inter | 72px / 4.5rem | Bold (700) | 1.1 |
| 信心值百分比 | Inter | 36px / 2.25rem | Semibold (600) | 1.2 |
| 頁面標題 (H1) | Inter | 30px / 1.875rem | Bold (700) | 1.3 |
| 區塊標題 (H2) | Inter | 24px / 1.5rem | Semibold (600) | 1.35 |
| 卡片標題 (H3) | Inter | 18px / 1.125rem | Semibold (600) | 1.4 |
| 正文 | Noto Sans TC | 14px / 0.875rem | Normal (400) | 1.6 |
| 小字/標籤 | Noto Sans TC | 12px / 0.75rem | Normal (400) | 1.5 |
| 數字/價格 | JetBrains Mono | 16px / 1rem | Medium (500) | 1.4 |
| 程式碼/數據 | JetBrains Mono | 13px / 0.8125rem | Normal (400) | 1.5 |

**中文字體說明：** 使用 Google Fonts 的 Noto Sans TC（思源黑體繁體中文），確保繁體中文顯示品質。數字與英文使用 Inter 以獲得更好的等寬對齊。

### 6.3 間距與排版規則

**間距系統 (基於 4px 網格)：**

```
spacing-0.5: 2px    spacing-1:  4px     spacing-1.5: 6px
spacing-2:   8px    spacing-2.5: 10px   spacing-3:   12px
spacing-4:   16px   spacing-5:  20px    spacing-6:   24px
spacing-8:   32px   spacing-10: 40px    spacing-12:  48px
spacing-16:  64px   spacing-20: 80px    spacing-24:  96px
```

| 元素 | 間距規則 |
|------|---------|
| 頁面邊距 (padding) | 桌面 24px / 平板 16px / 手機 12px |
| 卡片間距 (gap) | 桌面 16px / 平板 12px / 手機 8px |
| 卡片內邊距 (padding) | 桌面 20px / 平板 16px / 手機 12px |
| 區塊間距 (section gap) | 桌面 32px / 平板 24px / 手機 16px |
| 表格行高 | 48px |
| 按鈕高度 | 大 40px / 中 32px / 小 28px |

**圓角規則：**

| 元素 | 圓角 |
|------|------|
| 卡片 | 12px (rounded-xl) |
| 按鈕 | 8px (rounded-lg) |
| 輸入框 | 8px (rounded-lg) |
| 標籤/Badge | 9999px (rounded-full) |
| 頭像/圖示 | 50% (rounded-full) |
| Modal/Dialog | 16px (rounded-2xl) |

**陰影層級：**

```css
--shadow-sm:  0 1px 2px rgba(0,0,0,0.05);
--shadow-md:  0 4px 6px -1px rgba(0,0,0,0.1);
--shadow-lg:  0 10px 15px -3px rgba(0,0,0,0.1);
--shadow-xl:  0 20px 25px -5px rgba(0,0,0,0.1);
/* 深色模式下陰影減弱，改用 border 區分層級 */
```

### 6.4 台股特有設計注意事項

1. **紅漲綠跌**：貫穿所有漲跌相關顯示，與美股相反
2. **漲停/跌停標記**：漲停 10% 以紅色三角 ▲▲ 標記，跌停 10% 以綠色倒三角 ▼▼ 標記
3. **價格顯示**：新台幣 NT$，小數點兩位
4. **交易單位**：以「張」為單位（1 張 = 1,000 股），零股交易另行標示
5. **手續費計算**：牌告費率 0.1425%，實際折扣可在設定中調整
6. **證交稅**：賣出時 0.3%（ETF 0.1%）
7. **交易時間**：09:00-13:30，盤後 14:00-14:30

---

## 7. 前端架構

### 7.1 目錄結構

```
src/
├── app/                          # Next.js App Router 頁面
│   ├── layout.tsx                # 根佈局
│   ├── page.tsx                  # 首頁
│   ├── dashboard/
│   │   └── page.tsx
│   ├── stock/
│   │   └── [code]/
│   │       └── page.tsx
│   ├── portfolio/
│   │   ├── page.tsx
│   │   └── history/
│   │       └── page.tsx
│   ├── statistics/
│   │   └── page.tsx
│   └── settings/
│       └── page.tsx
│
├── components/                   # 元件目錄
│   ├── ui/                       # Shadcn/ui 基礎元件
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── input.tsx
│   │   ├── switch.tsx
│   │   ├── table.tsx
│   │   ├── tabs.tsx
│   │   └── ...
│   │
│   ├── layout/                   # 佈局元件
│   │   ├── Header.tsx            # 頂部導覽列
│   │   ├── Sidebar.tsx           # 側邊欄
│   │   ├── MobileNav.tsx         # 手機版底部導覽
│   │   └── StatusBar.tsx         # 底部狀態列
│   │
│   ├── prediction/               # 推論相關元件
│   │   ├── PredictionDisplay.tsx # 大字推論結果
│   │   ├── ConfidenceRing.tsx    # 信心值環形圖
│   │   └── PredictionBadge.tsx   # 小型推論標籤
│   │
│   ├── signals/                  # 訊號相關元件
│   │   ├── SignalCard.tsx        # 單一訊號卡片
│   │   ├── SignalGrid.tsx        # 9宮格訊號面板
│   │   ├── SignalRadarChart.tsx  # 雷達圖
│   │   └── SignalMiniBar.tsx     # 迷你進度條
│   │
│   ├── chart/                    # 圖表元件
│   │   ├── StockChart.tsx        # K線主圖
│   │   ├── VolumeChart.tsx       # 成交量圖
│   │   ├── RSIChart.tsx          # RSI指標
│   │   ├── MACDChart.tsx         # MACD指標
│   │   ├── KDChart.tsx           # KD指標
│   │   └── ChartToolbar.tsx      # 圖表工具列
│   │
│   ├── ai/                       # AI推論元件
│   │   ├── AIReasoningCard.tsx   # AI推論卡片
│   │   ├── AIToggle.tsx          # AI開關
│   │   ├── AILoadingState.tsx    # 載入狀態
│   │   └── TypewriterText.tsx    # 打字機效果
│   │
│   ├── portfolio/                # 模擬倉元件
│   │   ├── PortfolioSummary.tsx  # 資產摘要
│   │   ├── HoldingsTable.tsx     # 持倉列表
│   │   ├── TradePanel.tsx        # 交易面板
│   │   ├── TransactionTable.tsx  # 交易記錄
│   │   └── AssetPieChart.tsx     # 資產配置圖
│   │
│   ├── statistics/               # 統計元件
│   │   ├── AccuracyChart.tsx     # 準確率圖表
│   │   ├── PredictionHistory.tsx # 預測記錄
│   │   ├── SignalAccuracy.tsx    # 訊號準確率
│   │   └── TrendLineChart.tsx    # 趨勢折線圖
│   │
│   └── search/                   # 搜尋元件
│       ├── StockSearch.tsx       # 搜尋輸入
│       ├── SearchResults.tsx     # 搜尋結果
│       └── FavoriteStocks.tsx    # 常用股票
│
├── hooks/                        # 自訂 Hooks
│   ├── useStockWebSocket.ts      # WebSocket 連線
│   ├── useStockData.ts           # 股票數據查詢
│   ├── usePrediction.ts          # 推論數據
│   ├── useSignals.ts             # 訊號數據
│   ├── usePortfolio.ts           # 模擬倉操作
│   ├── useTheme.ts               # 主題切換
│   ├── useMediaQuery.ts          # 響應式偵測
│   └── useDebounce.ts            # 防抖
│
├── stores/                       # Zustand 狀態管理
│   ├── useStockStore.ts          # 股票/推論狀態
│   ├── usePortfolioStore.ts      # 模擬倉狀態
│   └── useUIStore.ts             # UI狀態
│
├── services/                     # API 服務層
│   ├── api.ts                    # API 客戶端基礎配置
│   ├── stockService.ts           # 股票相關 API
│   ├── predictionService.ts      # 推論相關 API
│   ├── portfolioService.ts       # 模擬倉相關 API
│   └── statisticsService.ts      # 統計相關 API
│
├── lib/                          # 工具函數
│   ├── utils.ts                  # 通用工具
│   ├── formatters.ts             # 格式化（貨幣、百分比、日期）
│   ├── validators.ts             # 驗證函數
│   ├── constants.ts              # 常數定義
│   └── cn.ts                     # className 合併工具
│
├── types/                        # TypeScript 型別
│   ├── stock.ts                  # 股票相關型別
│   ├── prediction.ts             # 推論相關型別
│   ├── signal.ts                 # 訊號相關型別
│   ├── portfolio.ts              # 模擬倉相關型別
│   └── api.ts                    # API 回應型別
│
└── styles/                       # 全域樣式
    ├── globals.css               # 全域 CSS + CSS 變數
    └── chart-theme.css           # 圖表主題色
```

### 7.2 元件分層策略

採用四層架構：

```
┌──────────────────────────────────────────┐
│  Page Layer（頁面層）                      │
│  app/dashboard/page.tsx                  │
│  - 負責頁面佈局組合                        │
│  - 處理路由參數                            │
│  - 頁面級數據載入                          │
├──────────────────────────────────────────┤
│  Feature Layer（功能層）                   │
│  components/prediction/PredictionDisplay │
│  components/signals/SignalGrid           │
│  - 組合基礎元件形成完整功能區塊             │
│  - 包含業務邏輯                            │
│  - 連接 Store 和 API                      │
├──────────────────────────────────────────┤
│  Base Component Layer（基礎元件層）        │
│  components/ui/button, card, table       │
│  - Shadcn/ui 元件                        │
│  - 無業務邏輯                             │
│  - 高度可重用                             │
├──────────────────────────────────────────┤
│  Foundation Layer（基礎設施層）            │
│  hooks/, stores/, services/, lib/        │
│  - 狀態管理                              │
│  - API 通訊                              │
│  - 工具函數                              │
│  - 型別定義                              │
└──────────────────────────────────────────┘
```

**依賴規則：**
- 上層可依賴下層，但下層不可依賴上層
- Page → Feature → Base → Foundation
- Feature 層之間盡量不互相依賴

### 7.3 API 服務層設計

```typescript
// services/api.ts
// 基礎 API 客戶端配置

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  async get<T>(path: string, params?: Record<string, string>): Promise<T> {
    const url = new URL(`${this.baseUrl}${path}`)
    if (params) {
      Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v))
    }
    const res = await fetch(url.toString(), {
      headers: { 'Content-Type': 'application/json' },
    })
    if (!res.ok) throw new ApiError(res.status, await res.text())
    return res.json()
  }

  async post<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) throw new ApiError(res.status, await res.text())
    return res.json()
  }
}

export const api = new ApiClient(API_BASE_URL)
```

```typescript
// services/stockService.ts
import { api } from './api'

export const stockService = {
  // 搜尋股票
  search: (query: string) =>
    api.get<StockSearchResult[]>('/stocks/search', { q: query }),

  // 取得股票即時報價
  getQuote: (code: string) =>
    api.get<StockQuote>(`/stocks/${code}/quote`),

  // 取得K線數據
  getKlines: (code: string, timeframe: string, limit: number) =>
    api.get<Kline[]>(`/stocks/${code}/klines`, {
      timeframe,
      limit: limit.toString(),
    }),
}

// services/predictionService.ts
export const predictionService = {
  // 取得即時推論
  getPrediction: (code: string) =>
    api.get<PredictionResult>(`/predictions/${code}`),

  // 取得9大訊號
  getSignals: (code: string) =>
    api.get<Signal[]>(`/predictions/${code}/signals`),

  // 觸發AI推論
  getAIReasoning: (code: string) =>
    api.post<AIReasoning>(`/predictions/${code}/ai-reasoning`, {}),

  // 取得歷史預測記錄
  getHistory: (params: PredictionHistoryParams) =>
    api.get<PaginatedResult<PredictionRecord>>('/predictions/history', params),
}

// services/portfolioService.ts
export const portfolioService = {
  // 取得持倉列表
  getHoldings: () =>
    api.get<Holding[]>('/portfolio/holdings'),

  // 買入
  buy: (data: TradeRequest) =>
    api.post<TradeResult>('/portfolio/buy', data),

  // 賣出
  sell: (data: TradeRequest) =>
    api.post<TradeResult>('/portfolio/sell', data),

  // 取得交易記錄
  getTransactions: (params: TransactionParams) =>
    api.get<PaginatedResult<Transaction>>('/portfolio/transactions', params),

  // 取得資產摘要
  getSummary: () =>
    api.get<PortfolioSummary>('/portfolio/summary'),
}
```

**TanStack Query 整合範例：**

```typescript
// hooks/useStockData.ts
import { useQuery } from '@tanstack/react-query'
import { stockService } from '@/services/stockService'

export function useStockQuote(code: string) {
  return useQuery({
    queryKey: ['stockQuote', code],
    queryFn: () => stockService.getQuote(code),
    enabled: !!code,
    refetchInterval: 5000,         // 每 5 秒重新取得（盤中）
    staleTime: 3000,               // 3 秒內視為新鮮
  })
}

export function useStockKlines(code: string, timeframe: string) {
  return useQuery({
    queryKey: ['klines', code, timeframe],
    queryFn: () => stockService.getKlines(code, timeframe, 200),
    enabled: !!code,
    staleTime: 60000,              // K線數據 1 分鐘快取
  })
}

export function usePrediction(code: string) {
  return useQuery({
    queryKey: ['prediction', code],
    queryFn: () => predictionService.getPrediction(code),
    enabled: !!code,
    staleTime: 10000,
  })
}
```

### 7.4 WebSocket 連線管理

```typescript
// lib/websocket.ts

type MessageHandler = (data: any) => void

class WebSocketManager {
  private ws: WebSocket | null = null
  private url: string
  private handlers: Map<string, Set<MessageHandler>> = new Map()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 10
  private reconnectTimer: NodeJS.Timeout | null = null
  private heartbeatTimer: NodeJS.Timeout | null = null

  constructor(url: string) {
    this.url = url
  }

  connect() {
    this.ws = new WebSocket(this.url)

    this.ws.onopen = () => {
      this.reconnectAttempts = 0
      this.startHeartbeat()
    }

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      const handlers = this.handlers.get(message.type)
      if (handlers) {
        handlers.forEach(handler => handler(message.payload))
      }
    }

    this.ws.onclose = (event) => {
      this.stopHeartbeat()
      if (!event.wasClean) {
        this.scheduleReconnect()
      }
    }

    this.ws.onerror = () => {
      this.ws?.close()
    }
  }

  // 訂閱特定類型的訊息
  subscribe(type: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set())
    }
    this.handlers.get(type)!.add(handler)

    // 返回取消訂閱函數
    return () => {
      this.handlers.get(type)?.delete(handler)
    }
  }

  // 發送訊息（例如訂閱特定股票）
  send(type: string, payload: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, payload }))
    }
  }

  // 指數退避重連
  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return

    const delay = Math.min(
      1000 * Math.pow(2, this.reconnectAttempts),
      30000  // 最大 30 秒
    )
    this.reconnectAttempts++

    this.reconnectTimer = setTimeout(() => {
      this.connect()
    }, delay)
  }

  // 心跳保活
  private startHeartbeat() {
    this.heartbeatTimer = setInterval(() => {
      this.send('ping', {})
    }, 30000)  // 每 30 秒
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
    }
  }

  // 切換股票訂閱
  switchStock(oldCode: string | null, newCode: string) {
    if (oldCode) {
      this.send('unsubscribe', { stockCode: oldCode })
    }
    this.send('subscribe', { stockCode: newCode })
  }

  disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
    this.stopHeartbeat()
    this.ws?.close()
    this.handlers.clear()
  }
}

// 單例模式
let wsManager: WebSocketManager | null = null

export function getWSManager(): WebSocketManager {
  if (!wsManager) {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws'
    wsManager = new WebSocketManager(wsUrl)
  }
  return wsManager
}
```

**React Hook 封裝：**

```typescript
// hooks/useStockWebSocket.ts
import { useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { getWSManager } from '@/lib/websocket'
import { useStockStore } from '@/stores/useStockStore'

export function useStockWebSocket(stockCode: string | null) {
  const queryClient = useQueryClient()
  const { setPrediction } = useStockStore()
  const prevCode = useRef<string | null>(null)

  useEffect(() => {
    if (!stockCode) return

    const ws = getWSManager()

    // 如果是首次連線，建立連線
    ws.connect()

    // 切換股票訂閱
    ws.switchStock(prevCode.current, stockCode)
    prevCode.current = stockCode

    // 訂閱即時價格更新
    const unsubPrice = ws.subscribe('price_update', (data) => {
      queryClient.setQueryData(['stockQuote', stockCode], data)
    })

    // 訂閱推論結果更新
    const unsubPrediction = ws.subscribe('prediction_update', (data) => {
      queryClient.setQueryData(['prediction', stockCode], data)
      setPrediction(data)
    })

    // 訂閱訊號更新
    const unsubSignals = ws.subscribe('signals_update', (data) => {
      queryClient.setQueryData(['signals', stockCode], data)
    })

    return () => {
      unsubPrice()
      unsubPrediction()
      unsubSignals()
    }
  }, [stockCode, queryClient, setPrediction])
}
```

---

## 附錄：技術依賴清單

```json
{
  "dependencies": {
    "next": "^14.2",
    "react": "^18.3",
    "react-dom": "^18.3",
    "typescript": "^5.4",
    "@tanstack/react-query": "^5.50",
    "zustand": "^4.5",
    "lightweight-charts": "^4.1",
    "echarts": "^5.5",
    "echarts-for-react": "^3.0",
    "recharts": "^2.12",
    "framer-motion": "^11.2",
    "react-hook-form": "^7.52",
    "zod": "^3.23",
    "@hookform/resolvers": "^3.6",
    "date-fns": "^3.6",
    "lucide-react": "^0.400",
    "cmdk": "^1.0",
    "class-variance-authority": "^0.7",
    "clsx": "^2.1",
    "tailwind-merge": "^2.3",
    "tailwindcss-animate": "^1.0"
  },
  "devDependencies": {
    "tailwindcss": "^3.4",
    "postcss": "^8.4",
    "autoprefixer": "^10.4",
    "@types/react": "^18.3",
    "@types/node": "^20",
    "eslint": "^8",
    "eslint-config-next": "^14.2",
    "prettier": "^3.3",
    "prettier-plugin-tailwindcss": "^0.6"
  }
}
```

---

> 本文件由前端工程師撰寫，涵蓋技術選型、頁面架構、核心元件、響應式設計、設計規範與前端架構等完整面向。所有設計均以台股使用者習慣為核心（紅漲綠跌），並兼顧桌面與行動裝置的使用體驗。
