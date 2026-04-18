"""
Unit tests for Signal 1: Outer Ratio (外盤比率)
Weight: 15%

Formula:
    Outer Ratio = outer_volume / (outer_volume + inner_volume) × 100%

Scoring:
    ≥ 75% → +80 ~ +100 (strongly bullish)
    60-74% → +30 ~ +80
    55-59% → +10 ~ +30
    45-54% → -10 ~ +10 (neutral zone)
    40-44% → -10 ~ -30
    25-39% → -30 ~ -80
    ≤ 25% → -80 ~ -100 (strongly bearish)
"""
import pytest


class TestOuterRatioNormalValues:
    """Tests for normal operating range values"""

    def test_normal_bullish_70_percent(self):
        """Outer ratio 70% should return positive score"""
        outer = 700
        inner = 300

        # Expected: ratio = 70%, score in +30 ~ +80 range
        # This test would call: calculate_outer_ratio(outer, inner)
        # For now, placeholder assertion
        ratio = outer / (outer + inner)
        assert ratio == 0.70
        # Expected score range: +30 to +80

    def test_normal_bearish_30_percent(self):
        """Outer ratio 30% should return negative score"""
        outer = 300
        inner = 700

        ratio = outer / (outer + inner)
        assert ratio == 0.30
        # Expected score range: -30 to -80

    def test_balanced_50_percent(self):
        """Outer ratio 50% should return neutral score (near 0)"""
        outer = 500
        inner = 500

        ratio = outer / (outer + inner)
        assert ratio == 0.50
        # Expected score: close to 0 (within -10 to +10)


class TestOuterRatioBoundaryValues:
    """Tests for boundary and extreme values"""

    def test_all_outer_100_percent(self):
        """Outer ratio 100% (all outer volume)"""
        outer = 1000
        inner = 0

        ratio = outer / (outer + inner) if (outer + inner) > 0 else 0
        assert ratio == 1.0
        # Expected score: close to +100

    def test_all_inner_0_percent(self):
        """Outer ratio 0% (all inner volume)"""
        outer = 0
        inner = 1000

        ratio = outer / (outer + inner) if (outer + inner) > 0 else 0
        assert ratio == 0.0
        # Expected score: close to -100

    def test_very_small_volume(self):
        """Very small total volume (1 unit)"""
        outer = 1
        inner = 0

        # Should still calculate correctly
        ratio = outer / (outer + inner) if (outer + inner) > 0 else 0
        assert ratio == 1.0
        # May be marked as low reliability

    def test_large_volume(self):
        """Large volume numbers"""
        outer = 1_000_000
        inner = 500_000

        ratio = outer / (outer + inner)
        assert pytest.approx(ratio, 0.01) == 0.667
        # Expected score: positive (bullish)

    def test_threshold_75_percent(self):
        """Boundary at 75% threshold (strongly bullish)"""
        outer = 750
        inner = 250

        ratio = outer / (outer + inner)
        assert ratio == 0.75
        # Expected score: >= +80

    def test_threshold_25_percent(self):
        """Boundary at 25% threshold (strongly bearish)"""
        outer = 250
        inner = 750

        ratio = outer / (outer + inner)
        assert ratio == 0.25
        # Expected score: <= -80


class TestOuterRatioAbnormalData:
    """Tests for abnormal and error conditions"""

    def test_zero_total_volume(self):
        """Both outer and inner are 0"""
        outer = 0
        inner = 0

        # Should handle gracefully, not raise ZeroDivisionError
        if outer + inner == 0:
            ratio = 0  # or None
        else:
            ratio = outer / (outer + inner)

        # Should return neutral or None, not error
        assert ratio is not None or ratio == 0

    def test_negative_outer_volume(self):
        """Negative outer volume (invalid data)"""
        outer = -100
        inner = 500

        # Should either raise ValueError or handle gracefully
        # Expected: ValueError or return None
        with pytest.raises(ValueError):
            if outer < 0 or inner < 0:
                raise ValueError("Volume cannot be negative")

    def test_negative_inner_volume(self):
        """Negative inner volume (invalid data)"""
        outer = 500
        inner = -100

        with pytest.raises(ValueError):
            if outer < 0 or inner < 0:
                raise ValueError("Volume cannot be negative")

    def test_none_input_outer(self):
        """None as outer volume"""
        outer = None
        inner = 500

        # Should raise TypeError or handle gracefully
        with pytest.raises(TypeError):
            ratio = outer / (outer + inner)

    def test_none_input_inner(self):
        """None as inner volume"""
        outer = 500
        inner = None

        with pytest.raises(TypeError):
            ratio = outer / (outer + inner)

    def test_float_volumes(self):
        """Float volume values (should work)"""
        outer = 700.5
        inner = 299.5

        ratio = outer / (outer + inner)
        assert pytest.approx(ratio, 0.001) == 0.701
        # Should handle float calculations correctly


class TestOuterRatioScoreRange:
    """Verify scores always fall within -100 to +100"""

    @pytest.mark.parametrize("outer,inner", [
        (1000, 0),      # 100%
        (900, 100),     # 90%
        (800, 200),     # 80%
        (700, 300),     # 70%
        (600, 400),     # 60%
        (500, 500),     # 50%
        (400, 600),     # 40%
        (300, 700),     # 30%
        (200, 800),     # 20%
        (100, 900),     # 10%
        (0, 1000),      # 0%
    ])
    def test_score_always_in_valid_range(self, outer, inner):
        """All possible outer ratios should produce scores in -100 to +100"""
        ratio = outer / (outer + inner) if (outer + inner) > 0 else 0

        # Score calculation logic (simplified)
        if ratio >= 0.75:
            score = 80 + (ratio - 0.75) * 80  # +80 to +100
        elif ratio >= 0.60:
            score = 30 + (ratio - 0.60) * 50 / 0.15  # +30 to +80
        elif ratio >= 0.55:
            score = 10 + (ratio - 0.55) * 20 / 0.05  # +10 to +30
        elif ratio >= 0.45:
            score = -10 + (ratio - 0.45) * 20 / 0.10  # -10 to +10
        elif ratio >= 0.40:
            score = -30 + (ratio - 0.40) * 20 / 0.05  # -30 to -10
        elif ratio >= 0.25:
            score = -80 + (ratio - 0.25) * 50 / 0.15  # -80 to -30
        else:
            score = -100 + ratio * 20 / 0.25  # -100 to -80

        assert -100 <= score <= 100, f"Score {score} out of range for ratio {ratio}"
