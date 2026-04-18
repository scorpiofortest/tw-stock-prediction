"""Prediction stats, latest, and history endpoints."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.schemas import APIResponse
from services.quote_service import QuoteService
from services.prediction_service import PredictionService

router = APIRouter(prefix="/predictions", tags=["predictions"])

quote_service = QuoteService()
prediction_service = PredictionService(quote_service)


@router.get("/stats")
async def get_prediction_stats(
    stock_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive prediction statistics."""
    stats = await prediction_service.get_stats(db, stock_id=stock_id)
    return APIResponse(data=stats)


@router.get("/latest")
async def get_latest_predictions(
    stock_id: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest prediction records."""
    records = await prediction_service.get_latest(db, stock_id=stock_id, limit=limit)
    return APIResponse(data=records)


@router.get("/history")
async def get_prediction_history(
    stock_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated prediction history."""
    result = await prediction_service.get_history(db, stock_id=stock_id, page=page, page_size=page_size)
    return {
        "success": True,
        "data": result["data"],
        "pagination": result["pagination"],
        "timestamp": datetime.now().isoformat(),
    }
