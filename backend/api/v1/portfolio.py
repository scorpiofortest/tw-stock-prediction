"""Portfolio (paper trading) API endpoints."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.schemas import APIResponse, TradeRequest, ResetRequest
from services.quote_service import QuoteService
from services.portfolio_service import PortfolioService
from core.exceptions import InsufficientFunds, InsufficientShares

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

quote_service = QuoteService()
portfolio_service = PortfolioService(quote_service)


@router.get("/account")
async def get_account(db: AsyncSession = Depends(get_db)):
    """Get account overview."""
    account = await portfolio_service.get_account(db)
    return APIResponse(data=account)


@router.get("/positions")
async def get_positions(db: AsyncSession = Depends(get_db)):
    """Get all positions with unrealized PnL."""
    positions = await portfolio_service.get_positions(db)
    return APIResponse(data=positions)


@router.post("/buy")
async def buy(request: TradeRequest, db: AsyncSession = Depends(get_db)):
    """Execute a simulated buy order."""
    result = await portfolio_service.buy(
        db=db,
        stock_id=request.stock_id,
        shares=request.shares,
        price=request.price,
    )
    return APIResponse(data=result)


@router.post("/sell")
async def sell(request: TradeRequest, db: AsyncSession = Depends(get_db)):
    """Execute a simulated sell order."""
    result = await portfolio_service.sell(
        db=db,
        stock_id=request.stock_id,
        shares=request.shares,
        price=request.price,
    )
    return APIResponse(data=result)


@router.get("/trades")
async def get_trades(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    stock_id: Optional[str] = None,
    trade_type: Optional[str] = Query(None, pattern="^(buy|sell)$"),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated trade records."""
    result = await portfolio_service.get_trades(
        db, page=page, page_size=page_size, stock_id=stock_id, trade_type=trade_type,
    )
    return {
        "success": True,
        "data": result["data"],
        "pagination": result["pagination"],
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/reset")
async def reset_portfolio(request: ResetRequest, db: AsyncSession = Depends(get_db)):
    """Reset portfolio to initial state."""
    result = await portfolio_service.reset(db, initial_capital=request.initial_capital)
    return APIResponse(data=result)
