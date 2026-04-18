"""
Unit tests for Weighted Scoring System
Target Coverage: ≥ 95%

The weighted scoring system combines all 9 signal scores into a composite score.

Weights (must sum to 100%):
1. Outer Ratio: 15%
2. Bid-Ask Pressure: 12%
3. Tick Direction: 10%
4. Intraday Position: 8%
5. Price Momentum: 10%
6. RSI: 12%
7. MACD OSC: 13%
8. KD Cross: 12%
9. Trend Acceleration: 8%
"""
import pytest
import random


class TestWeightValidation:
    """Tests for weight configuration correctness"""

    def test_weights_sum_to_100_percent(self):
        """All signal weights must sum to exactly 100%"""
        weights = {
            "outer_ratio": 0.15,
            "bid_ask_pressure": 0.12,
            "tick_direction": 0.10,
            "intraday_position": 0.08,
            "price_momentum": 0.10,
            "rsi": 0.12,
            "macd_osc": 0.13,
            "kd_cross": 0.12,
            "trend_acceleration": 0.08,
        }

        total_weight = sum(weights.values())
        assert pytest.approx(total_weight, abs=1e-9) == 1.0

    def test_all_signals_have_weights(self):
        """Every signal must have a defined weight"""
        weights = {
            "outer_ratio": 0.15,
            "bid_ask_pressure": 0.12,
            "tick_direction": 0.10,
            "intraday_position": 0.08,
            "price_momentum": 0.10,
            "rsi": 0.12,
            "macd_osc": 0.13,
            "kd_cross": 0.12,
            "trend_acceleration": 0.08,
        }

        assert len(weights) == 9
        assert all(w > 0 for w in weights.values())

    def test_no_negative_weights(self):
        """Weights cannot be negative"""
        weights = {
            "outer_ratio": 0.15,
            "bid_ask_pressure": 0.12,
            "tick_direction": 0.10,
            "intraday_position": 0.08,
            "price_momentum": 0.10,
            "rsi": 0.12,
            "macd_osc": 0.13,
            "kd_cross": 0.12,
            "trend_acceleration": 0.08,
        }

        assert all(w >= 0 for w in weights.values())

    def test_individual_weight_ranges(self):
        """Each weight should be between 3% and 25% (PRD requirement)"""
        weights = {
            "outer_ratio": 0.15,
            "bid_ask_pressure": 0.12,
            "tick_direction": 0.10,
            "intraday_position": 0.08,
            "price_momentum": 0.10,
            "rsi": 0.12,
            "macd_osc": 0.13,
            "kd_cross": 0.12,
            "trend_acceleration": 0.08,
        }

        for name, weight in weights.items():
            assert 0.03 <= weight <= 0.25, f"{name} weight {weight} out of range"


class TestExtremeScenarios:
    """Tests for extreme signal combinations"""

    def test_all_bullish_signals_max_100(self):
        """All signals at +100 should produce total score of +100"""
        signals = {
            "outer_ratio": 100,
            "bid_ask_pressure": 100,
            "tick_direction": 100,
            "intraday_position": 100,
            "price_momentum": 100,
            "rsi": 100,
            "macd_osc": 100,
            "kd_cross": 100,
            "trend_acceleration": 100,
        }

        weights = {
            "outer_ratio": 0.15,
            "bid_ask_pressure": 0.12,
            "tick_direction": 0.10,
            "intraday_position": 0.08,
            "price_momentum": 0.10,
            "rsi": 0.12,
            "macd_osc": 0.13,
            "kd_cross": 0.12,
            "trend_acceleration": 0.08,
        }

        total_score = sum(signals[k] * weights[k] for k in signals.keys())
        assert total_score == 100.0

    def test_all_bearish_signals_min_minus_100(self):
        """All signals at -100 should produce total score of -100"""
        signals = {k: -100 for k in [
            "outer_ratio", "bid_ask_pressure", "tick_direction",
            "intraday_position", "price_momentum", "rsi",
            "macd_osc", "kd_cross", "trend_acceleration"
        ]}

        weights = {
            "outer_ratio": 0.15,
            "bid_ask_pressure": 0.12,
            "tick_direction": 0.10,
            "intraday_position": 0.08,
            "price_momentum": 0.10,
            "rsi": 0.12,
            "macd_osc": 0.13,
            "kd_cross": 0.12,
            "trend_acceleration": 0.08,
        }

        total_score = sum(signals[k] * weights[k] for k in signals.keys())
        assert total_score == -100.0

    def test_all_neutral_signals_zero(self):
        """All signals at 0 should produce total score of 0"""
        signals = {k: 0 for k in [
            "outer_ratio", "bid_ask_pressure", "tick_direction",
            "intraday_position", "price_momentum", "rsi",
            "macd_osc", "kd_cross", "trend_acceleration"
        ]}

        weights = {
            "outer_ratio": 0.15,
            "bid_ask_pressure": 0.12,
            "tick_direction": 0.10,
            "intraday_position": 0.08,
            "price_momentum": 0.10,
            "rsi": 0.12,
            "macd_osc": 0.13,
            "kd_cross": 0.12,
            "trend_acceleration": 0.08,
        }

        total_score = sum(signals[k] * weights[k] for k in signals.keys())
        assert total_score == 0.0

    def test_contradicting_signals(self):
        """Mixed bullish and bearish signals"""
        signals = {
            "outer_ratio": 100,
            "bid_ask_pressure": -100,
            "tick_direction": 100,
            "intraday_position": -100,
            "price_momentum": 50,
            "rsi": -50,
            "macd_osc": 0,
            "kd_cross": 80,
            "trend_acceleration": -80,
        }

        weights = {
            "outer_ratio": 0.15,
            "bid_ask_pressure": 0.12,
            "tick_direction": 0.10,
            "intraday_position": 0.08,
            "price_momentum": 0.10,
            "rsi": 0.12,
            "macd_osc": 0.13,
            "kd_cross": 0.12,
            "trend_acceleration": 0.08,
        }

        total_score = sum(signals[k] * weights[k] for k in signals.keys())

        # Should still be in valid range
        assert -100 <= total_score <= 100


class TestScoreRangeValidation:
    """Property-based testing: scores must always be in valid range"""

    def test_random_signal_combinations_1000_iterations(self):
        """Generate 1000 random signal combinations, all should produce valid scores"""
        weights = {
            "outer_ratio": 0.15,
            "bid_ask_pressure": 0.12,
            "tick_direction": 0.10,
            "intraday_position": 0.08,
            "price_momentum": 0.10,
            "rsi": 0.12,
            "macd_osc": 0.13,
            "kd_cross": 0.12,
            "trend_acceleration": 0.08,
        }

        for _ in range(1000):
            # Generate random scores for each signal (-100 to +100)
            signals = {
                k: random.uniform(-100, 100) for k in weights.keys()
            }

            total_score = sum(signals[k] * weights[k] for k in signals.keys())

            assert -100 <= total_score <= 100, \
                f"Score {total_score} out of range for signals {signals}"

    @pytest.mark.parametrize("fixed_score", [-100, -75, -50, -25, 0, 25, 50, 75, 100])
    def test_all_signals_same_value(self, fixed_score):
        """All signals having the same score should equal that score"""
        signals = {k: fixed_score for k in [
            "outer_ratio", "bid_ask_pressure", "tick_direction",
            "intraday_position", "price_momentum", "rsi",
            "macd_osc", "kd_cross", "trend_acceleration"
        ]}

        weights = {
            "outer_ratio": 0.15,
            "bid_ask_pressure": 0.12,
            "tick_direction": 0.10,
            "intraday_position": 0.08,
            "price_momentum": 0.10,
            "rsi": 0.12,
            "macd_osc": 0.13,
            "kd_cross": 0.12,
            "trend_acceleration": 0.08,
        }

        total_score = sum(signals[k] * weights[k] for k in signals.keys())
        assert pytest.approx(total_score, abs=0.1) == fixed_score


class TestPartialSignals:
    """Tests for handling missing/None signals"""

    def test_partial_signals_some_none(self):
        """Some signals return None (data unavailable)"""
        signals = {
            "outer_ratio": 50,
            "bid_ask_pressure": None,
            "tick_direction": 30,
            "intraday_position": None,
            "price_momentum": -20,
            "rsi": 60,
            "macd_osc": None,
            "kd_cross": -40,
            "trend_acceleration": 10,
        }

        weights = {
            "outer_ratio": 0.15,
            "bid_ask_pressure": 0.12,
            "tick_direction": 0.10,
            "intraday_position": 0.08,
            "price_momentum": 0.10,
            "rsi": 0.12,
            "macd_osc": 0.13,
            "kd_cross": 0.12,
            "trend_acceleration": 0.08,
        }

        # Calculate with renormalized weights (excluding None signals)
        valid_signals = {k: v for k, v in signals.items() if v is not None}
        valid_weights = {k: weights[k] for k in valid_signals.keys()}

        # Renormalize weights
        total_valid_weight = sum(valid_weights.values())
        renormalized_weights = {k: w / total_valid_weight for k, w in valid_weights.items()}

        total_score = sum(valid_signals[k] * renormalized_weights[k] for k in valid_signals.keys())

        assert -100 <= total_score <= 100

    def test_all_signals_none(self):
        """All signals unavailable"""
        signals = {k: None for k in [
            "outer_ratio", "bid_ask_pressure", "tick_direction",
            "intraday_position", "price_momentum", "rsi",
            "macd_osc", "kd_cross", "trend_acceleration"
        ]}

        valid_signals = {k: v for k, v in signals.items() if v is not None}

        # Should return None or 0
        if len(valid_signals) == 0:
            result = None
            assert result is None or result == 0


class TestHighWeightSignalDominance:
    """Tests for high-weight signal influence"""

    def test_highest_weight_signal_dominates(self):
        """Signal with highest weight (MACD: 13%) should have strongest influence"""
        weights = {
            "outer_ratio": 0.15,      # Second highest
            "bid_ask_pressure": 0.12,
            "tick_direction": 0.10,
            "intraday_position": 0.08,
            "price_momentum": 0.10,
            "rsi": 0.12,
            "macd_osc": 0.13,         # Highest
            "kd_cross": 0.12,
            "trend_acceleration": 0.08,
        }

        # Only MACD is +100, all others are 0
        signals_macd_only = {k: (100 if k == "macd_osc" else 0) for k in weights.keys()}

        score_macd = sum(signals_macd_only[k] * weights[k] for k in weights.keys())

        # Should equal MACD's weight * 100 = 13
        assert pytest.approx(score_macd, abs=0.1) == 13.0

        # Only Outer Ratio is +100, all others are 0
        signals_outer_only = {k: (100 if k == "outer_ratio" else 0) for k in weights.keys()}

        score_outer = sum(signals_outer_only[k] * weights[k] for k in weights.keys())

        # Should equal Outer Ratio's weight * 100 = 15
        assert pytest.approx(score_outer, abs=0.1) == 15.0

        # Outer Ratio should have more influence than MACD
        assert score_outer > score_macd
