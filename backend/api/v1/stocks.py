"""Stock search, quote, and history endpoints."""

from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.schemas import APIResponse
from services.quote_service import QuoteService
from services.news_service import NewsService

router = APIRouter(prefix="/stocks", tags=["stocks"])
quote_service = QuoteService()
news_service = NewsService()


@router.get("/search")
async def search_stocks(q: str = Query(..., min_length=1)):
    """Search stocks by code or name."""
    results = quote_service.search_stocks(q)
    return APIResponse(data=results)


@router.get("/{stock_id}/quote")
async def get_quote(stock_id: str):
    """Get real-time quote for a stock."""
    quote = await quote_service.get_quote(stock_id)
    return APIResponse(data=quote)


@router.get("/{stock_id}/history")
async def get_history(
    stock_id: str,
    period: str = Query("3mo", pattern="^(1d|5d|1mo|3mo|6mo|1y)$"),
):
    """Get historical OHLCV data via yfinance."""
    records = await quote_service.get_history(stock_id, period)
    return APIResponse(data=records)


@router.get("/{stock_id}/news")
async def get_news(stock_id: str, limit: int = Query(5, ge=1, le=20)):
    """Get stock-specific news via Google News RSS."""
    stock_name = quote_service.get_stock_name(stock_id)
    news = await news_service.get_stock_news(stock_id, stock_name, limit=limit)
    return APIResponse(data=news)


@router.get("/{stock_id}/fundamentals")
async def get_fundamentals(stock_id: str):
    """Get basic fundamentals (PE, EPS, dividend yield, etc.) via yfinance."""
    fundamentals = await quote_service.get_fundamentals(stock_id)
    return APIResponse(data=fundamentals)
