"""
Test data factories for generating realistic market data
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random


class MarketDataFactory:
    """Factory for creating market data test fixtures"""

    @staticmethod
    def create(
        stock_id: str = "2330",
        price: float = 890.0,
        prev_close: float = 878.0,
        volume: int = 25000,
        outer_ratio: float = 0.55,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create standard market data fixture

        Args:
            stock_id: Stock ID (e.g., "2330")
            price: Current price
            prev_close: Previous close price
            volume: Total volume
            outer_ratio: Outer volume ratio (0-1)
            **kwargs: Additional overrides
        """
        high = kwargs.get('high', price * 1.01)
        low = kwargs.get('low', price * 0.98)
        open_price = kwargs.get('open', price * 0.99)

        return {
            "stock_id": stock_id,
            "stock_name": kwargs.get('stock_name', "台積電"),
            "timestamp": kwargs.get('timestamp', datetime.now().isoformat()),
            "price": {
                "open": open_price,
                "high": high,
                "low": low,
                "close": price,
                "prev_close": prev_close,
            },
            "volume": {
                "total": volume,
                "outer": int(volume * outer_ratio),
                "inner": int(volume * (1 - outer_ratio)),
            },
            "order_book": kwargs.get('order_book', OrderBookFactory.create_balanced(price)),
            "ticks": kwargs.get('ticks', TickFactory.create_random(price, count=20)),
            "technical": kwargs.get('technical', TechnicalFactory.create_neutral()),
        }

    @staticmethod
    def create_bullish(stock_id: str = "2330") -> Dict[str, Any]:
        """
        Create bullish market data
        Strong buying pressure with high outer ratio
        """
        price = 900.0
        prev_close = 870.0

        return MarketDataFactory.create(
            stock_id=stock_id,
            price=price,
            prev_close=prev_close,
            volume=50000,
            outer_ratio=0.72,  # 72% outer volume
            order_book=OrderBookFactory.create_buy_heavy(price),
            technical=TechnicalFactory.create_bullish(),
        )

    @staticmethod
    def create_bearish(stock_id: str = "2330") -> Dict[str, Any]:
        """
        Create bearish market data
        Strong selling pressure with low outer ratio
        """
        price = 850.0
        prev_close = 880.0

        return MarketDataFactory.create(
            stock_id=stock_id,
            price=price,
            prev_close=prev_close,
            volume=45000,
            outer_ratio=0.32,  # 32% outer volume (68% inner)
            order_book=OrderBookFactory.create_sell_heavy(price),
            technical=TechnicalFactory.create_bearish(),
        )

    @staticmethod
    def create_consolidation(stock_id: str = "2330") -> Dict[str, Any]:
        """Create consolidating market data with minimal movement"""
        price = 885.0
        prev_close = 884.0

        return MarketDataFactory.create(
            stock_id=stock_id,
            price=price,
            prev_close=prev_close,
            high=886.0,
            low=883.0,
            volume=20000,
            outer_ratio=0.52,
            order_book=OrderBookFactory.create_balanced(price),
            technical=TechnicalFactory.create_neutral(),
        )


class OrderBookFactory:
    """Factory for creating order book (bid/ask) data"""

    @staticmethod
    def create_balanced(base_price: float) -> Dict[str, List[Dict[str, float]]]:
        """Create balanced bid/ask order book"""
        return {
            "bid": [
                {"price": base_price - i, "qty": 100 + i * 20}
                for i in range(5)
            ],
            "ask": [
                {"price": base_price + i + 1, "qty": 100 + i * 20}
                for i in range(5)
            ],
        }

    @staticmethod
    def create_buy_heavy(base_price: float) -> Dict[str, List[Dict[str, float]]]:
        """Create buy-heavy order book (bullish)"""
        return {
            "bid": [
                {"price": base_price - i, "qty": 500 + i * 50}
                for i in range(5)
            ],
            "ask": [
                {"price": base_price + i + 1, "qty": 20 + i * 5}
                for i in range(5)
            ],
        }

    @staticmethod
    def create_sell_heavy(base_price: float) -> Dict[str, List[Dict[str, float]]]:
        """Create sell-heavy order book (bearish)"""
        return {
            "bid": [
                {"price": base_price - i, "qty": 20 + i * 5}
                for i in range(5)
            ],
            "ask": [
                {"price": base_price + i + 1, "qty": 500 + i * 50}
                for i in range(5)
            ],
        }


class TickFactory:
    """Factory for creating tick data (trade details)"""

    @staticmethod
    def create_random(base_price: float, count: int = 20) -> List[Dict[str, Any]]:
        """Create random tick data"""
        ticks = []
        now = datetime.now()

        for i in range(count):
            direction = random.choice(["buy", "sell"])
            price_offset = random.uniform(-0.5, 0.5)

            ticks.append({
                "time": (now - timedelta(seconds=count - i)).strftime("%H:%M:%S"),
                "price": round(base_price + price_offset, 2),
                "qty": random.randint(1, 10),
                "direction": direction,
            })

        return ticks

    @staticmethod
    def create_bullish(base_price: float, count: int = 20) -> List[Dict[str, Any]]:
        """Create bullish tick data (mostly buy direction)"""
        ticks = []
        now = datetime.now()

        for i in range(count):
            # 75% buy direction
            direction = "buy" if random.random() < 0.75 else "sell"

            ticks.append({
                "time": (now - timedelta(seconds=count - i)).strftime("%H:%M:%S"),
                "price": base_price,
                "qty": random.randint(1, 10),
                "direction": direction,
            })

        return ticks

    @staticmethod
    def create_bearish(base_price: float, count: int = 20) -> List[Dict[str, Any]]:
        """Create bearish tick data (mostly sell direction)"""
        ticks = []
        now = datetime.now()

        for i in range(count):
            # 75% sell direction
            direction = "sell" if random.random() < 0.75 else "buy"

            ticks.append({
                "time": (now - timedelta(seconds=count - i)).strftime("%H:%M:%S"),
                "price": base_price,
                "qty": random.randint(1, 10),
                "direction": direction,
            })

        return ticks


class TechnicalFactory:
    """Factory for creating technical indicator data"""

    @staticmethod
    def create_neutral() -> Dict[str, Any]:
        """Create neutral technical indicators"""
        return {
            "rsi_14": 50.0,
            "macd": {
                "dif": 0.5,
                "macd": 0.5,
                "osc": 0.0,
            },
            "kd": {
                "k": 50.0,
                "d": 50.0,
            },
            "ma": {
                "ma5": 890.0,
                "ma10": 885.0,
                "ma20": 880.0,
                "ma60": 870.0,
            },
        }

    @staticmethod
    def create_bullish() -> Dict[str, Any]:
        """Create bullish technical indicators"""
        return {
            "rsi_14": 65.0,
            "macd": {
                "dif": 2.5,
                "macd": 1.8,
                "osc": 0.7,
            },
            "kd": {
                "k": 72.3,
                "d": 65.8,
            },
            "ma": {
                "ma5": 900.0,
                "ma10": 895.0,
                "ma20": 885.0,
                "ma60": 870.0,
            },
        }

    @staticmethod
    def create_bearish() -> Dict[str, Any]:
        """Create bearish technical indicators"""
        return {
            "rsi_14": 35.0,
            "macd": {
                "dif": -2.5,
                "macd": -1.8,
                "osc": -0.7,
            },
            "kd": {
                "k": 28.5,
                "d": 35.2,
            },
            "ma": {
                "ma5": 850.0,
                "ma10": 860.0,
                "ma20": 870.0,
                "ma60": 880.0,
            },
        }
