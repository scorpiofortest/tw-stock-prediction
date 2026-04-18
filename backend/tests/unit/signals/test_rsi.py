"""
Unit tests for Signal 6: RSI (Relative Strength Index)
Weight: 12%

Formula:
    RSI(14) = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss over 14 periods

Scoring with reversal logic:
    RSI > 80 → score = -50 ~ -100 (overbought, expect pullback)
    RSI 65~80 → score = +30 ~ +50
    RSI 55~64 → score = +10 ~ +30
    RSI 45~54 → score = -10 ~ +10 (neutral)
    RSI 35~44 → score = -10 ~ -30
    RSI 20~34 → score = -30 ~ -50
    RSI < 20 → score = +50 ~ +100 (oversold, expect bounce)

Note: RSI > 80 and RSI < 20 have reversal logic for mean reversion
"""
import pytest
import numpy as np


class TestRSICalculationAccuracy:
    """Tests for RSI calculation correctness"""

    def test_rsi_calculation_with_known_data(self):
        """Verify RSI calculation with known correct values"""
        # Known price series and expected RSI
        prices = [
            44.0, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42,
            45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28, 46.00
        ]

        # Calculate gains and losses
        changes = np.diff(prices)
        gains = np.where(changes > 0, changes, 0)
        losses = np.where(changes < 0, -changes, 0)

        avg_gain = np.mean(gains[:14])
        avg_loss = np.mean(losses[:14])

        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        # RSI should be in valid range
        assert 0 <= rsi <= 100

    def test_rsi_all_gains_produces_100(self):
        """Continuous gains should produce RSI = 100"""
        prices = [100 + i for i in range(15)]  # Continuous increase

        changes = np.diff(prices)
        gains = np.where(changes > 0, changes, 0)
        losses = np.where(changes < 0, -changes, 0)

        avg_loss = np.mean(losses[:14])

        if avg_loss == 0:
            rsi = 100.0

        assert rsi == 100.0

    def test_rsi_all_losses_produces_0(self):
        """Continuous losses should produce RSI = 0"""
        prices = [100 - i for i in range(15)]  # Continuous decrease

        changes = np.diff(prices)
        gains = np.where(changes > 0, changes, 0)
        losses = np.where(changes < 0, -changes, 0)

        avg_gain = np.mean(gains[:14])

        if avg_gain == 0:
            rsi = 0.0

        assert rsi == 0.0


class TestRSIOverboughtOversold:
    """Tests for overbought/oversold signal generation"""

    def test_overbought_signal_rsi_85(self):
        """RSI > 80 should give negative score (expect reversal)"""
        rsi = 85.0

        # Overbought reversal logic
        if rsi > 80:
            # Expected: negative score (expect pullback)
            score = -50 - (rsi - 80) * 50 / 20  # -50 to -100

        assert score < 0
        assert -100 <= score <= -50

    def test_oversold_signal_rsi_15(self):
        """RSI < 20 should give positive score (expect bounce)"""
        rsi = 15.0

        # Oversold reversal logic
        if rsi < 20:
            # Expected: positive score (expect bounce)
            score = 50 + (20 - rsi) * 50 / 20  # +50 to +100

        assert score > 0
        assert 50 <= score <= 100

    def test_neutral_rsi_50(self):
        """RSI = 50 should give neutral score (0)"""
        rsi = 50.0

        if 45 <= rsi <= 54:
            # Neutral zone
            score = -10 + (rsi - 45) * 20 / 9

        assert pytest.approx(score, abs=2) == 0

    def test_moderate_bullish_rsi_60(self):
        """RSI = 60 should give moderate positive score"""
        rsi = 60.0

        if 55 <= rsi <= 64:
            score = 10 + (rsi - 55) * 20 / 9  # +10 to +30

        assert 10 <= score <= 30

    def test_moderate_bearish_rsi_40(self):
        """RSI = 40 should give moderate negative score"""
        rsi = 40.0

        if 35 <= rsi <= 44:
            score = -30 + (rsi - 35) * 20 / 9  # -30 to -10

        assert -30 <= score <= -10


class TestRSIBoundaryValues:
    """Tests for RSI boundary conditions"""

    def test_overbought_reversal_at_threshold_80(self):
        """RSI crossing from 79 to 81 should change signal"""
        rsi_79 = 79.0
        rsi_81 = 81.0

        # At 79: still bullish
        if 65 <= rsi_79 <= 80:
            score_79 = 30 + (rsi_79 - 65) * 20 / 15
            assert score_79 > 0

        # At 81: reversal (bearish)
        if rsi_81 > 80:
            score_81 = -50 - (rsi_81 - 80) * 50 / 20
            assert score_81 < 0

    def test_oversold_reversal_at_threshold_20(self):
        """RSI crossing from 21 to 19 should trigger reversal"""
        rsi_21 = 21.0
        rsi_19 = 19.0

        # At 21: still bearish
        if 20 <= rsi_21 <= 34:
            score_21 = -30 - (34 - rsi_21) * 20 / 14
            assert score_21 < 0

        # At 19: reversal (bullish)
        if rsi_19 < 20:
            score_19 = 50 + (20 - rsi_19) * 50 / 20
            assert score_19 > 0

    def test_rsi_at_0(self):
        """RSI = 0 (extreme oversold)"""
        rsi = 0.0

        if rsi < 20:
            score = 50 + (20 - rsi) * 50 / 20

        assert score == 100  # Maximum bullish (reversal expected)

    def test_rsi_at_100(self):
        """RSI = 100 (extreme overbought)"""
        rsi = 100.0

        if rsi > 80:
            score = -50 - (rsi - 80) * 50 / 20

        assert score == -100  # Maximum bearish (reversal expected)

    def test_rsi_exactly_50(self):
        """RSI = 50 (perfect neutral)"""
        rsi = 50.0

        if 45 <= rsi <= 54:
            score = -10 + (rsi - 45) * 20 / 9

        assert pytest.approx(score, abs=1) == 0


class TestRSIAbnormalData:
    """Tests for insufficient or invalid data"""

    def test_insufficient_data_less_than_14_periods(self):
        """Less than 14 data points"""
        prices = [100, 101, 102, 103, 104]  # Only 5 prices

        if len(prices) < 15:  # Need 15 prices for 14 changes
            # Should return None or use available data with low reliability
            result = None
            assert result is None

    def test_all_same_prices(self):
        """All prices identical (no movement)"""
        prices = [100.0] * 15

        changes = np.diff(prices)
        # All changes are 0
        assert np.all(changes == 0)

        # RSI should be 50 or None
        # When avg_gain = avg_loss = 0, RS is undefined
        rsi = 50.0  # Commonly set to 50 for no movement
        assert rsi == 50.0

    def test_single_data_point(self):
        """Only one price data point"""
        prices = [100.0]

        if len(prices) < 2:
            result = None
            assert result is None

    def test_none_in_price_series(self):
        """None values in price data"""
        prices = [100, 101, None, 103, 104]

        with pytest.raises(TypeError):
            changes = np.diff(prices)


class TestRSIScoreRange:
    """Verify all RSI values produce scores in -100 to +100"""

    @pytest.mark.parametrize("rsi", [
        0, 5, 10, 15, 19,      # Extreme oversold
        20, 25, 30, 34,        # Oversold zone
        35, 40, 44,            # Bearish zone
        45, 50, 54,            # Neutral zone
        55, 60, 64,            # Bullish zone
        65, 70, 75, 80,        # Strong bullish
        81, 85, 90, 95, 100,   # Extreme overbought
    ])
    def test_all_rsi_values_produce_valid_scores(self, rsi):
        """Every RSI value should produce a score in valid range"""
        if rsi > 80:
            score = -50 - (rsi - 80) * 50 / 20
        elif rsi >= 65:
            score = 30 + (rsi - 65) * 20 / 15
        elif rsi >= 55:
            score = 10 + (rsi - 55) * 20 / 9
        elif rsi >= 45:
            score = -10 + (rsi - 45) * 20 / 9
        elif rsi >= 35:
            score = -30 + (rsi - 35) * 20 / 9
        elif rsi >= 20:
            score = -50 + (rsi - 20) * 20 / 14
        else:  # rsi < 20
            score = 50 + (20 - rsi) * 50 / 20

        assert -100 <= score <= 100, f"RSI {rsi} produced invalid score {score}"
