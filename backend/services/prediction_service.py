"""Prediction creation and 62-second verification service."""

import math
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.database_models import PredictionRecord
from core.ws_manager import ws_manager


class PredictionService:
    """Creates predictions and verifies them after 62 seconds."""

    def __init__(self, quote_service):
        self.quote_service = quote_service

    async def create_prediction(
        self,
        db: AsyncSession,
        stock_id: str,
        stock_name: str,
        direction: str,
        confidence: float,
        price: float,
        signal_score: float,
        ai_involved: bool = False,
    ) -> dict:
        """Create a new prediction record."""
        # Map direction string to DB enum
        if signal_score >= 5:
            pred_dir = "up"
        elif signal_score <= -5:
            pred_dir = "down"
        else:
            pred_dir = "flat"

        record = PredictionRecord(
            stock_id=stock_id,
            stock_name=stock_name,
            predicted_at=datetime.now(),
            predicted_direction=pred_dir,
            predicted_confidence=confidence,
            price_at_prediction=price,
            signal_score=signal_score,
            ai_involved=ai_involved,
            status="pending",
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)

        result = self._to_dict(record)

        # Broadcast via WebSocket
        await ws_manager.broadcast_to_stock(stock_id, {
            "type": "prediction_created",
            "data": result,
        })

        return result

    async def verify_pending(self, db: AsyncSession):
        """Verify all predictions that are past their 62-second window."""
        cutoff = datetime.now() - timedelta(seconds=62)
        result = await db.execute(
            select(PredictionRecord).where(
                PredictionRecord.status == "pending",
                PredictionRecord.predicted_at <= cutoff,
            )
        )
        pending = result.scalars().all()

        for record in pending:
            await self._verify_single(db, record)

        if pending:
            await db.commit()

    async def _verify_single(self, db: AsyncSession, record: PredictionRecord):
        """Verify a single prediction against current price."""
        try:
            current_price = await self.quote_service.get_price(record.stock_id)
        except Exception:
            record.status = "expired"
            logger.warning(f"Cannot verify prediction {record.id}: price unavailable")
            return

        price_change_pct = (
            (current_price - record.price_at_prediction) / record.price_at_prediction * 100
            if record.price_at_prediction else 0
        )

        # Determine actual direction
        if price_change_pct > 0.02:
            actual = "up"
        elif price_change_pct < -0.02:
            actual = "down"
        else:
            actual = "flat"

        # Determine correctness per PRD Section 6.1
        predicted = record.predicted_direction
        is_correct = None

        if predicted == "up":
            if price_change_pct > 0.02:
                is_correct = True
            elif price_change_pct < -0.02:
                is_correct = False
            else:
                is_correct = None  # flat -> not counted
        elif predicted == "down":
            if price_change_pct < -0.02:
                is_correct = True
            elif price_change_pct > 0.02:
                is_correct = False
            else:
                is_correct = None  # flat -> not counted
        elif predicted == "flat":
            if abs(price_change_pct) <= 0.05:
                is_correct = True
            else:
                is_correct = False

        record.verify_at = datetime.now()
        record.price_at_verify = current_price
        record.actual_direction = actual
        record.price_change_pct = round(price_change_pct, 4)
        record.is_correct = is_correct
        record.status = "verified"

        # Broadcast verification result
        await ws_manager.broadcast_to_stock(record.stock_id, {
            "type": "prediction_verified",
            "data": self._to_dict(record),
        })

    async def get_stats(self, db: AsyncSession, stock_id: Optional[str] = None) -> dict:
        """Get comprehensive prediction statistics."""
        query = select(PredictionRecord).where(PredictionRecord.status == "verified")
        if stock_id:
            query = query.where(PredictionRecord.stock_id == stock_id)
        result = await db.execute(query)
        records = result.scalars().all()

        total = len(records)
        success = sum(1 for r in records if r.is_correct is True)
        fail = sum(1 for r in records if r.is_correct is False)
        flat = sum(1 for r in records if r.is_correct is None)
        effective = success + fail
        rate = (success / effective * 100) if effective > 0 else 0

        def _dir_stats(direction: str):
            subset = [r for r in records if r.predicted_direction == direction]
            s = sum(1 for r in subset if r.is_correct is True)
            f = sum(1 for r in subset if r.is_correct is False)
            eff = s + f
            return {"total": len(subset), "success": s, "fail": f, "rate": round(s/eff*100, 1) if eff else 0}

        def _conf_stats(lo: float, hi: float):
            subset = [r for r in records if lo <= r.predicted_confidence < hi]
            s = sum(1 for r in subset if r.is_correct is True)
            f = sum(1 for r in subset if r.is_correct is False)
            eff = s + f
            return {"total": len(subset), "success": s, "fail": f, "rate": round(s/eff*100, 1) if eff else 0}

        def _period_stats(start_h: int, start_m: int, end_h: int, end_m: int):
            from datetime import time
            start_t = time(start_h, start_m)
            end_t = time(end_h, end_m)
            subset = [r for r in records if r.predicted_at and start_t <= r.predicted_at.time() <= end_t]
            s = sum(1 for r in subset if r.is_correct is True)
            f = sum(1 for r in subset if r.is_correct is False)
            eff = s + f
            return {"total": len(subset), "success": s, "fail": f, "rate": round(s/eff*100, 1) if eff else 0}

        def _rolling(n: int):
            recent = sorted(records, key=lambda r: r.predicted_at, reverse=True)[:n]
            recent = [r for r in recent if r.is_correct is not None]
            if not recent:
                return None
            s = sum(1 for r in recent if r.is_correct is True)
            return round(s / len(recent) * 100, 1)

        return {
            "total_predictions": total,
            "success_count": success,
            "fail_count": fail,
            "flat_count": flat,
            "success_rate": round(rate, 1),
            "by_direction": {
                "bullish": _dir_stats("up"),
                "bearish": _dir_stats("down"),
                "neutral": _dir_stats("flat"),
            },
            "by_confidence": {
                "high": _conf_stats(70, 101),
                "medium": _conf_stats(40, 70),
                "low": _conf_stats(0, 40),
            },
            "by_period": {
                "opening": _period_stats(9, 0, 9, 30),
                "midday": _period_stats(9, 30, 12, 0),
                "closing": _period_stats(12, 0, 13, 30),
            },
            "rolling_20": _rolling(20),
            "rolling_50": _rolling(50),
            "rolling_100": _rolling(100),
        }

    async def get_latest(self, db: AsyncSession, stock_id: Optional[str] = None, limit: int = 10) -> list[dict]:
        """Get the latest prediction records."""
        query = select(PredictionRecord)
        if stock_id:
            query = query.where(PredictionRecord.stock_id == stock_id)
        query = query.order_by(PredictionRecord.predicted_at.desc()).limit(limit)
        result = await db.execute(query)
        records = result.scalars().all()
        return [self._to_dict(r) for r in records]

    async def get_history(self, db: AsyncSession, stock_id: Optional[str] = None, page: int = 1, page_size: int = 20) -> dict:
        """Get paginated prediction history."""
        query = select(PredictionRecord)
        if stock_id:
            query = query.where(PredictionRecord.stock_id == stock_id)
        query = query.order_by(PredictionRecord.predicted_at.desc())

        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar() or 0

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        result = await db.execute(query)
        records = result.scalars().all()

        return {
            "data": [self._to_dict(r) for r in records],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": math.ceil(total / page_size) if page_size else 0,
            },
        }

    @staticmethod
    def _to_dict(r: PredictionRecord) -> dict:
        return {
            "id": r.id,
            "stock_id": r.stock_id,
            "stock_name": r.stock_name,
            "predicted_at": r.predicted_at.isoformat() if r.predicted_at else None,
            "predicted_direction": r.predicted_direction,
            "predicted_confidence": r.predicted_confidence,
            "price_at_prediction": r.price_at_prediction,
            "signal_score": r.signal_score,
            "ai_involved": r.ai_involved,
            "verify_at": r.verify_at.isoformat() if r.verify_at else None,
            "price_at_verify": r.price_at_verify,
            "actual_direction": r.actual_direction,
            "price_change_pct": r.price_change_pct,
            "status": r.status,
            "is_correct": r.is_correct,
        }
