"""Portfolio (paper trading) service with Taiwan stock trading rules."""

import json
import math
from datetime import datetime, date
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from config import get_settings
from core.exceptions import InsufficientFunds, InsufficientShares, StockNotFound
from models.database_models import UserAccount, Position, TradeRecord, AssetSnapshot


settings = get_settings()


class PortfolioService:
    """Simulated portfolio with real Taiwan stock commission/tax rules."""

    FEE_RATE = settings.FEE_RATE          # 0.1425%
    FEE_DISCOUNT = settings.FEE_DISCOUNT  # 0.6
    TAX_RATE = settings.TAX_RATE          # 0.3%
    MIN_FEE = settings.MIN_FEE            # NT$20

    def __init__(self, quote_service):
        self.quote_service = quote_service

    async def ensure_default_account(self, db: AsyncSession) -> UserAccount:
        """Create default user account if it doesn't exist."""
        result = await db.execute(
            select(UserAccount).where(UserAccount.username == "default")
        )
        account = result.scalar_one_or_none()
        if account is None:
            account = UserAccount(
                username="default",
                initial_capital=settings.INITIAL_CAPITAL,
                current_cash=settings.INITIAL_CAPITAL,
            )
            db.add(account)
            await db.commit()
            await db.refresh(account)
        return account

    async def get_account(self, db: AsyncSession) -> dict:
        """Get account overview with calculated totals (factoring in estimated sell costs)."""
        account = await self.ensure_default_account(db)
        positions = await self.get_positions(db)

        # Use net proceeds (after estimated sell costs) for stock value
        total_stock_value = sum(
            pos.get("market_value", 0) for pos in positions
        )
        total_unrealized_pnl = sum(
            pos.get("unrealized_pnl", 0) for pos in positions
        )

        total_assets = account.current_cash + total_stock_value
        total_pnl = total_assets - account.initial_capital
        total_pnl_pct = (total_pnl / account.initial_capital * 100) if account.initial_capital else 0

        return {
            "username": account.username,
            "initial_capital": account.initial_capital,
            "current_cash": account.current_cash,
            "total_stock_value": round(total_stock_value, 2),
            "total_assets": round(total_assets, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round(total_pnl_pct, 2),
            "total_unrealized_pnl": round(total_unrealized_pnl, 2),
            "positions_count": len(positions),
        }

    async def get_positions(self, db: AsyncSession) -> list[dict]:
        """Get all positions with current price and unrealized PnL (including estimated sell costs)."""
        account = await self.ensure_default_account(db)
        result = await db.execute(
            select(Position).where(Position.user_id == account.id)
        )
        positions = result.scalars().all()
        out = []
        for pos in positions:
            current_price = await self.quote_service.get_price(pos.stock_id)
            market_value = current_price * pos.shares

            # Estimated sell costs (commission + securities transaction tax)
            est_sell_fee = max(market_value * self.FEE_RATE * self.FEE_DISCOUNT, self.MIN_FEE)
            est_sell_fee = math.floor(est_sell_fee)
            est_sell_tax = math.floor(market_value * self.TAX_RATE)
            net_proceeds = market_value - est_sell_fee - est_sell_tax

            # Unrealized PnL = estimated net proceeds - total buy cost (already includes buy fee)
            unrealized_pnl = net_proceeds - pos.total_cost
            unrealized_pnl_pct = (unrealized_pnl / pos.total_cost * 100) if pos.total_cost else 0
            out.append({
                "stock_id": pos.stock_id,
                "stock_name": pos.stock_name,
                "shares": pos.shares,
                "avg_cost": round(pos.avg_cost, 4),
                "total_cost": round(pos.total_cost, 2),
                "current_price": current_price,
                "market_value": round(market_value, 2),
                "est_sell_fee": est_sell_fee,
                "est_sell_tax": est_sell_tax,
                "unrealized_pnl": round(unrealized_pnl, 2),
                "unrealized_pnl_pct": round(unrealized_pnl_pct, 2),
            })
        return out

    async def buy(self, db: AsyncSession, stock_id: str, shares: int, price: Optional[float] = None) -> dict:
        """
        Execute a simulated buy order.
        fee = max(amount * 0.1425% * 0.6, 20), floor-rounded.
        """
        stock_name = self.quote_service.get_stock_name(stock_id)
        if price is None:
            price = await self.quote_service.get_price(stock_id)

        amount = price * shares
        fee = max(amount * self.FEE_RATE * self.FEE_DISCOUNT, self.MIN_FEE)
        fee = math.floor(fee)
        total_cost = amount + fee

        account = await self.ensure_default_account(db)
        if account.current_cash < total_cost:
            raise InsufficientFunds(
                f"現金不足：需要 {total_cost:,.0f}，餘額 {account.current_cash:,.0f}"
            )

        # Deduct cash
        account.current_cash -= total_cost

        # Update or create position
        result = await db.execute(
            select(Position).where(
                Position.user_id == account.id,
                Position.stock_id == stock_id,
            )
        )
        position = result.scalar_one_or_none()

        if position:
            old_total = position.avg_cost * position.shares
            new_total = old_total + total_cost
            position.shares += shares
            position.avg_cost = new_total / position.shares
            position.total_cost = new_total
        else:
            position = Position(
                user_id=account.id,
                stock_id=stock_id,
                stock_name=stock_name,
                shares=shares,
                avg_cost=total_cost / shares,
                total_cost=total_cost,
            )
            db.add(position)

        # Create trade record
        trade = TradeRecord(
            user_id=account.id,
            stock_id=stock_id,
            stock_name=stock_name,
            trade_type="buy",
            shares=shares,
            price=price,
            amount=amount,
            fee=fee,
            tax=0,
            net_amount=total_cost,
            realized_pnl=None,
        )
        db.add(trade)
        await db.commit()
        await db.refresh(trade)
        await db.refresh(position)
        await db.refresh(account)

        return {
            "trade": {
                "id": trade.id,
                "stock_id": stock_id,
                "stock_name": stock_name,
                "trade_type": "buy",
                "shares": shares,
                "price": price,
                "amount": amount,
                "fee": fee,
                "tax": 0,
                "net_amount": total_cost,
                "realized_pnl": None,
                "traded_at": trade.traded_at.isoformat() if trade.traded_at else datetime.now().isoformat(),
            },
            "position": {
                "stock_id": position.stock_id,
                "stock_name": position.stock_name,
                "shares": position.shares,
                "avg_cost": round(position.avg_cost, 4),
                "total_cost": round(position.total_cost, 2),
            },
            "account_balance": round(account.current_cash, 2),
        }

    async def sell(self, db: AsyncSession, stock_id: str, shares: int, price: Optional[float] = None) -> dict:
        """
        Execute a simulated sell order.
        fee = max(amount * 0.1425% * 0.6, 20), floor-rounded.
        tax = floor(amount * 0.3%).
        """
        stock_name = self.quote_service.get_stock_name(stock_id)
        if price is None:
            price = await self.quote_service.get_price(stock_id)

        account = await self.ensure_default_account(db)
        result = await db.execute(
            select(Position).where(
                Position.user_id == account.id,
                Position.stock_id == stock_id,
            )
        )
        position = result.scalar_one_or_none()

        if not position or position.shares < shares:
            raise InsufficientShares(
                f"持有股數不足：需賣出 {shares}，持有 {position.shares if position else 0}"
            )

        amount = price * shares
        fee = max(amount * self.FEE_RATE * self.FEE_DISCOUNT, self.MIN_FEE)
        fee = math.floor(fee)
        tax = math.floor(amount * self.TAX_RATE)
        net_proceeds = amount - fee - tax

        # Calculate realized PnL
        cost_basis = position.avg_cost * shares
        realized_pnl = net_proceeds - cost_basis

        # Credit cash
        account.current_cash += net_proceeds

        # Update position
        position.shares -= shares
        position_out = None
        if position.shares == 0:
            await db.delete(position)
        else:
            position.total_cost = position.avg_cost * position.shares
            position_out = {
                "stock_id": position.stock_id,
                "stock_name": position.stock_name,
                "shares": position.shares,
                "avg_cost": round(position.avg_cost, 4),
                "total_cost": round(position.total_cost, 2),
            }

        # Create trade record
        trade = TradeRecord(
            user_id=account.id,
            stock_id=stock_id,
            stock_name=stock_name,
            trade_type="sell",
            shares=shares,
            price=price,
            amount=amount,
            fee=fee,
            tax=tax,
            net_amount=net_proceeds,
            realized_pnl=realized_pnl,
        )
        db.add(trade)
        await db.commit()
        await db.refresh(trade)
        await db.refresh(account)

        return {
            "trade": {
                "id": trade.id,
                "stock_id": stock_id,
                "stock_name": stock_name,
                "trade_type": "sell",
                "shares": shares,
                "price": price,
                "amount": amount,
                "fee": fee,
                "tax": tax,
                "net_amount": net_proceeds,
                "realized_pnl": round(realized_pnl, 2),
                "traded_at": trade.traded_at.isoformat() if trade.traded_at else datetime.now().isoformat(),
            },
            "position": position_out,
            "account_balance": round(account.current_cash, 2),
        }

    async def get_trades(self, db: AsyncSession, page: int = 1, page_size: int = 20, stock_id: Optional[str] = None, trade_type: Optional[str] = None) -> dict:
        """Get paginated trade records."""
        account = await self.ensure_default_account(db)
        query = select(TradeRecord).where(TradeRecord.user_id == account.id)
        if stock_id:
            query = query.where(TradeRecord.stock_id == stock_id)
        if trade_type:
            query = query.where(TradeRecord.trade_type == trade_type)
        query = query.order_by(TradeRecord.traded_at.desc())

        # Count total
        from sqlalchemy import func
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        result = await db.execute(query)
        trades = result.scalars().all()

        return {
            "data": [
                {
                    "id": t.id,
                    "stock_id": t.stock_id,
                    "stock_name": t.stock_name,
                    "trade_type": t.trade_type,
                    "shares": t.shares,
                    "price": t.price,
                    "amount": t.amount,
                    "fee": t.fee,
                    "tax": t.tax,
                    "net_amount": t.net_amount,
                    "realized_pnl": t.realized_pnl,
                    "traded_at": t.traded_at.isoformat() if t.traded_at else None,
                }
                for t in trades
            ],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": math.ceil(total / page_size) if page_size else 0,
            },
        }

    async def reset(self, db: AsyncSession, initial_capital: Optional[float] = None) -> dict:
        """Reset portfolio to initial state."""
        account = await self.ensure_default_account(db)
        capital = initial_capital or settings.INITIAL_CAPITAL

        # Delete all positions and trades for this user
        await db.execute(delete(Position).where(Position.user_id == account.id))
        await db.execute(delete(TradeRecord).where(TradeRecord.user_id == account.id))
        await db.execute(delete(AssetSnapshot).where(AssetSnapshot.user_id == account.id))

        account.initial_capital = capital
        account.current_cash = capital
        await db.commit()
        await db.refresh(account)

        return {
            "message": "模擬倉已重置",
            "initial_capital": capital,
            "current_cash": capital,
        }

    async def take_daily_snapshot(self, db: AsyncSession):
        """Take end-of-day asset snapshot."""
        account = await self.ensure_default_account(db)
        positions = await self.get_positions(db)

        stock_value = sum(
            (p.get("current_price", 0) or 0) * p["shares"]
            for p in positions
        )
        total_assets = account.current_cash + stock_value

        # Previous snapshot
        result = await db.execute(
            select(AssetSnapshot)
            .where(AssetSnapshot.user_id == account.id)
            .order_by(AssetSnapshot.snapshot_date.desc())
            .limit(1)
        )
        prev = result.scalar_one_or_none()
        prev_total = prev.total_assets if prev else account.initial_capital

        daily_pnl = total_assets - prev_total
        daily_pnl_pct = (daily_pnl / prev_total * 100) if prev_total else 0
        total_pnl = total_assets - account.initial_capital
        total_pnl_pct = (total_pnl / account.initial_capital * 100) if account.initial_capital else 0

        snapshot = AssetSnapshot(
            user_id=account.id,
            snapshot_date=date.today(),
            cash=account.current_cash,
            stock_value=stock_value,
            total_assets=total_assets,
            daily_pnl=round(daily_pnl, 2),
            daily_pnl_pct=round(daily_pnl_pct, 2),
            total_pnl=round(total_pnl, 2),
            total_pnl_pct=round(total_pnl_pct, 2),
            positions_detail=json.dumps(positions, ensure_ascii=False),
        )
        db.add(snapshot)
        await db.commit()
        logger.info(f"Daily snapshot taken: total_assets={total_assets:.2f}")
