"""Pydantic v2 request/response schemas."""

from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, Any


# ─── Unified Response ──────────────────────────────────────────────

class APIResponse(BaseModel):
    success: bool = True
    data: Any = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class APIErrorResponse(BaseModel):
    success: bool = False
    error: dict
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class PaginatedResponse(BaseModel):
    success: bool = True
    data: list[Any]
    pagination: PaginationMeta
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# ─── Signal Schemas ────────────────────────────────────────────────

class SignalScoreOut(BaseModel):
    name: str
    value: float
    score: float = Field(ge=-100, le=100)
    weight: float = Field(ge=0, le=1)
    weighted_score: float
    description: str
    reliability: float = Field(ge=0, le=1, default=1.0)


class CompositeScoreOut(BaseModel):
    stock_id: str
    stock_name: str
    total_score: float = Field(ge=-100, le=100)
    direction: str
    confidence: float = Field(ge=10, le=95)
    signal_agreement: str
    signals: list[SignalScoreOut]
    calculated_at: str


class AnalysisResultOut(BaseModel):
    stock_id: str
    stock_name: str
    current_price: float
    change_pct: float
    composite_score: CompositeScoreOut
    ai_analysis: Optional[dict] = None


# ─── Stock Quote ───────────────────────────────────────────────────

class StockQuoteOut(BaseModel):
    stock_id: str
    stock_name: str
    current_price: float
    open: float
    high: float
    low: float
    close: float
    volume: int
    change: float
    change_percent: float
    updated_at: str


class StockSearchResult(BaseModel):
    stock_id: str
    stock_name: str
    market: str  # 'TWSE' | 'TPEX'


class StockHistoryItem(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


# ─── Portfolio ─────────────────────────────────────────────────────

class TradeRequest(BaseModel):
    stock_id: str
    shares: int = Field(gt=0)
    price: Optional[float] = Field(default=None, gt=0)


class ResetRequest(BaseModel):
    initial_capital: Optional[float] = Field(default=None, gt=0)


class PositionOut(BaseModel):
    stock_id: str
    stock_name: str
    shares: int
    avg_cost: float
    total_cost: float
    current_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None


class TradeRecordOut(BaseModel):
    id: int
    stock_id: str
    stock_name: str
    trade_type: str
    shares: int
    price: float
    amount: float
    fee: float
    tax: float
    net_amount: float
    realized_pnl: Optional[float] = None
    traded_at: str


class AccountOut(BaseModel):
    username: str
    initial_capital: float
    current_cash: float
    total_stock_value: float
    total_assets: float
    total_pnl: float
    total_pnl_pct: float
    positions_count: int


class TradeResultOut(BaseModel):
    trade: TradeRecordOut
    position: Optional[PositionOut] = None
    account_balance: float


# ─── Prediction ────────────────────────────────────────────────────

class PredictionOut(BaseModel):
    id: int
    stock_id: str
    stock_name: str
    predicted_at: str
    predicted_direction: str
    predicted_confidence: float
    price_at_prediction: float
    signal_score: Optional[float] = None
    ai_involved: bool
    verify_at: Optional[str] = None
    price_at_verify: Optional[float] = None
    actual_direction: Optional[str] = None
    price_change_pct: Optional[float] = None
    status: str
    is_correct: Optional[bool] = None


class DirectionStats(BaseModel):
    total: int
    success: int
    fail: int
    rate: float


class ConfidenceStats(BaseModel):
    high: DirectionStats
    medium: DirectionStats
    low: DirectionStats


class PeriodStats(BaseModel):
    opening: DirectionStats
    midday: DirectionStats
    closing: DirectionStats


class PredictionStatsOut(BaseModel):
    total_predictions: int
    success_count: int
    fail_count: int
    flat_count: int
    success_rate: float
    by_direction: dict[str, DirectionStats]
    by_confidence: ConfidenceStats
    by_period: PeriodStats
    rolling_20: Optional[float] = None
    rolling_50: Optional[float] = None
    rolling_100: Optional[float] = None


# ─── Stats / Dashboard ────────────────────────────────────────────

class DashboardOut(BaseModel):
    portfolio: dict
    predictions: dict
    ai_status: dict


class SignalAccuracyOut(BaseModel):
    signal_name: str
    total: int
    correct: int
    accuracy: float


# ─── AI Toggle ─────────────────────────────────────────────────────

class AIToggleRequest(BaseModel):
    enabled: bool


class AIStatusOut(BaseModel):
    enabled: bool
    reason: str
    consecutive_failures: int


# ─── AI Settings ──────────────────────────────────────────────────

class AISettingsOut(BaseModel):
    api_key: str  # masked
    model: str
    provider: str


class AISettingsUpdateRequest(BaseModel):
    api_key: Optional[str] = None
    model: Optional[str] = None
