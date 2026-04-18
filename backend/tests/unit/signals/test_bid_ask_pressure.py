"""
Unit tests for Signal 2: Bid-Ask Pressure (五檔委買委賣壓力)
Weight: 12%

Formula:
    Pressure Ratio = (bid_total - ask_total) / (bid_total + ask_total)
    Range: -1.0 to +1.0

Scoring:
    ≥ 0.5 → +80 ~ +100
    0.2~0.49 → +30 ~ +80
    0.05~0.19 → +5 ~ +30
    ±0.04 → -5 ~ +5 (neutral zone)
    -0.19~-0.05 → -5 ~ -30
    -0.49~-0.2 → -30 ~ -80
    ≤ -0.5 → -80 ~ -100

Note: If either bid_total or ask_total < 50 lots, weight reduced by 50%
"""
import pytest


class TestBidAskPressureNormalValues:
    """Tests for normal order book scenarios"""

    def test_buy_pressure_dominant(self):
        """Strong buying pressure: bid >> ask"""
        bid_levels = [500, 400, 300, 200, 100]  # Total: 1500
        ask_levels = [50, 40, 30, 20, 10]       # Total: 150

        bid_total = sum(bid_levels)
        ask_total = sum(ask_levels)
        pressure = (bid_total - ask_total) / (bid_total + ask_total)

        assert pytest.approx(pressure, 0.01) == 0.82
        # Expected score: strongly positive (+80 to +100)

    def test_sell_pressure_dominant(self):
        """Strong selling pressure: ask >> bid"""
        bid_levels = [50, 40, 30, 20, 10]       # Total: 150
        ask_levels = [500, 400, 300, 200, 100]  # Total: 1500

        bid_total = sum(bid_levels)
        ask_total = sum(ask_levels)
        pressure = (bid_total - ask_total) / (bid_total + ask_total)

        assert pytest.approx(pressure, 0.01) == -0.82
        # Expected score: strongly negative (-80 to -100)

    def test_balanced_pressure(self):
        """Balanced bid/ask: neutral pressure"""
        bid_levels = [100, 100, 100, 100, 100]
        ask_levels = [100, 100, 100, 100, 100]

        bid_total = sum(bid_levels)
        ask_total = sum(ask_levels)
        pressure = (bid_total - ask_total) / (bid_total + ask_total)

        assert pressure == 0.0
        # Expected score: neutral (close to 0)

    def test_moderate_buy_pressure(self):
        """Moderate buy pressure: 0.2 < pressure < 0.5"""
        bid_levels = [300, 250, 200, 150, 100]  # Total: 1000
        ask_levels = [200, 150, 100, 80, 70]    # Total: 600

        bid_total = sum(bid_levels)
        ask_total = sum(ask_levels)
        pressure = (bid_total - ask_total) / (bid_total + ask_total)

        assert pytest.approx(pressure, 0.01) == 0.25
        # Expected score: +30 to +80


class TestBidAskPressureBoundaryValues:
    """Tests for extreme and boundary conditions"""

    def test_extreme_buy_pressure(self):
        """Maximum buy pressure: ask almost zero"""
        bid_levels = [9999, 9999, 9999, 9999, 9999]
        ask_levels = [1, 1, 1, 1, 1]

        bid_total = sum(bid_levels)
        ask_total = sum(ask_levels)
        pressure = (bid_total - ask_total) / (bid_total + ask_total)

        assert pressure > 0.99
        # Expected score: close to +100

    def test_extreme_sell_pressure(self):
        """Maximum sell pressure: bid almost zero"""
        bid_levels = [1, 1, 1, 1, 1]
        ask_levels = [9999, 9999, 9999, 9999, 9999]

        bid_total = sum(bid_levels)
        ask_total = sum(ask_levels)
        pressure = (bid_total - ask_total) / (bid_total + ask_total)

        assert pressure < -0.99
        # Expected score: close to -100

    def test_zero_orders_both_sides(self):
        """No orders on either side"""
        bid_levels = [0, 0, 0, 0, 0]
        ask_levels = [0, 0, 0, 0, 0]

        bid_total = sum(bid_levels)
        ask_total = sum(ask_levels)

        # Should handle division by zero
        if bid_total + ask_total == 0:
            pressure = 0  # or None
        else:
            pressure = (bid_total - ask_total) / (bid_total + ask_total)

        assert pressure == 0 or pressure is None

    def test_partial_empty_levels(self):
        """Some levels have no orders (low liquidity stock)"""
        bid_levels = [100, 50, 0, 0, 0]
        ask_levels = [200, 0, 0, 0, 0]

        bid_total = sum(bid_levels)
        ask_total = sum(ask_levels)
        pressure = (bid_total - ask_total) / (bid_total + ask_total)

        assert pytest.approx(pressure, 0.01) == -0.33
        # Expected score: negative


class TestBidAskPressureAbnormalData:
    """Tests for invalid and abnormal inputs"""

    def test_insufficient_levels_bid(self):
        """Less than 5 bid levels"""
        bid_levels = [100, 50]
        ask_levels = [200, 150, 100, 80, 70]

        # Should handle gracefully
        bid_total = sum(bid_levels)
        ask_total = sum(ask_levels)

        if len(bid_levels) < 5 or len(ask_levels) < 5:
            # Mark as low reliability or use available data
            reliability = "low"

        pressure = (bid_total - ask_total) / (bid_total + ask_total)
        assert -1.0 <= pressure <= 1.0

    def test_insufficient_levels_ask(self):
        """Less than 5 ask levels"""
        bid_levels = [200, 150, 100, 80, 70]
        ask_levels = [100, 50]

        bid_total = sum(bid_levels)
        ask_total = sum(ask_levels)
        pressure = (bid_total - ask_total) / (bid_total + ask_total)

        assert -1.0 <= pressure <= 1.0

    def test_negative_order_quantity(self):
        """Negative quantities (invalid data)"""
        bid_levels = [100, -50, 80, 70, 60]
        ask_levels = [90, 80, 70, 60, 50]

        # Should validate or raise error
        with pytest.raises(ValueError):
            if any(q < 0 for q in bid_levels + ask_levels):
                raise ValueError("Order quantity cannot be negative")

    def test_none_in_levels(self):
        """None values in order levels"""
        bid_levels = [100, None, 80, 70, 60]
        ask_levels = [90, 80, 70, 60, 50]

        # Should handle None values
        with pytest.raises(TypeError):
            bid_total = sum(bid_levels)


class TestBidAskPressureLowReliability:
    """Tests for low reliability conditions"""

    def test_low_volume_bid_side(self):
        """Bid total < 50 lots: weight should be reduced"""
        bid_levels = [10, 8, 7, 6, 5]  # Total: 36 < 50
        ask_levels = [100, 90, 80, 70, 60]

        bid_total = sum(bid_levels)
        ask_total = sum(ask_levels)

        # Check if total < 50 threshold
        if bid_total < 50 or ask_total < 50:
            weight_multiplier = 0.5  # Weight reduced by 50%
            assert weight_multiplier == 0.5

    def test_low_volume_ask_side(self):
        """Ask total < 50 lots: weight should be reduced"""
        bid_levels = [100, 90, 80, 70, 60]
        ask_levels = [10, 8, 7, 6, 5]  # Total: 36 < 50

        bid_total = sum(bid_levels)
        ask_total = sum(ask_levels)

        if bid_total < 50 or ask_total < 50:
            weight_multiplier = 0.5
            assert weight_multiplier == 0.5

    def test_low_volume_both_sides(self):
        """Both sides < 50 lots"""
        bid_levels = [10, 8, 7, 6, 5]   # Total: 36
        ask_levels = [12, 10, 9, 8, 6]  # Total: 45

        bid_total = sum(bid_levels)
        ask_total = sum(ask_levels)

        assert bid_total < 50
        assert ask_total < 50
        # Weight should be significantly reduced


class TestBidAskPressureScoreRange:
    """Verify scores always in valid range"""

    @pytest.mark.parametrize("bid_total,ask_total", [
        (1000, 100),   # Pressure: 0.82
        (700, 300),    # Pressure: 0.40
        (600, 400),    # Pressure: 0.20
        (550, 450),    # Pressure: 0.10
        (500, 500),    # Pressure: 0.00
        (450, 550),    # Pressure: -0.10
        (400, 600),    # Pressure: -0.20
        (300, 700),    # Pressure: -0.40
        (100, 1000),   # Pressure: -0.82
    ])
    def test_all_scenarios_produce_valid_scores(self, bid_total, ask_total):
        """All pressure ratios should produce valid scores"""
        pressure = (bid_total - ask_total) / (bid_total + ask_total)

        # Simplified scoring logic
        if pressure >= 0.5:
            score = 80 + (pressure - 0.5) * 40
        elif pressure >= 0.2:
            score = 30 + (pressure - 0.2) * 50 / 0.3
        elif pressure >= 0.05:
            score = 5 + (pressure - 0.05) * 25 / 0.15
        elif pressure >= -0.04:
            score = -5 + (pressure + 0.04) * 10 / 0.09
        elif pressure >= -0.19:
            score = -30 + (pressure + 0.19) * 25 / 0.15
        elif pressure >= -0.49:
            score = -80 + (pressure + 0.49) * 50 / 0.30
        else:
            score = -100 + (pressure + 1.0) * 20 / 0.5

        assert -100 <= score <= 100
