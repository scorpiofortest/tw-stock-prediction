"""Dashboard and signal accuracy endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.schemas import APIResponse
from services.quote_service import QuoteService
from services.ai_analysis import AIAnalysisService
from services.prediction_service import PredictionService
from services.stats_service import StatsService

router = APIRouter(prefix="/stats", tags=["stats"])

quote_service = QuoteService()
ai_service = AIAnalysisService()
prediction_service = PredictionService(quote_service)
stats_service = StatsService(quote_service, ai_service, prediction_service)


@router.get("/dashboard")
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Get dashboard overview."""
    data = await stats_service.get_dashboard(db)
    return APIResponse(data=data)


@router.get("/signals/accuracy")
async def get_signal_accuracy(db: AsyncSession = Depends(get_db)):
    """Get per-signal accuracy statistics."""
    data = await stats_service.get_signal_accuracy(db)
    return APIResponse(data=data)
