"""
Unit tests for sensors/scoring.py.

All scoring functions are pure Python with no I/O or hardware dependencies,
so no mocking is required.
"""
import pytest
from sensors.scoring import (
    temperature_score,
    light_score,
    humidity_score,
    noise_score,
    total_score,
    calculate_scores,
)


class TestTemperatureScore:
    def test_optimal_temp_is_near_100(self):
        assert temperature_score(22.0) >= 85

    def test_cold_temp_is_penalized(self):
        assert temperature_score(10.0) < temperature_score(22.0)

    def test_hot_temp_is_penalized(self):
        assert temperature_score(35.0) < temperature_score(22.0)

    def test_extreme_cold_clamped_to_zero(self):
        assert temperature_score(-50.0) == 0.0

    def test_output_never_exceeds_100(self):
        assert temperature_score(22.0) <= 100.0


class TestLightScore:
    def test_zero_lux_returns_zero(self):
        assert light_score(0.0) == 0.0

    def test_optimal_lux_near_100(self):
        assert light_score(500.0) >= 99.0

    def test_negative_lux_clamped_to_zero(self):
        assert light_score(-10.0) == light_score(0.0)

    def test_monotonic_increase_toward_optimal(self):
        assert light_score(100.0) < light_score(300.0) < light_score(500.0)

    def test_output_never_exceeds_100(self):
        assert light_score(500.0) <= 100.0


class TestHumidityScore:
    def test_optimal_humidity_near_100(self):
        assert humidity_score(45.0) >= 99.0

    def test_low_humidity_penalized(self):
        assert humidity_score(20.0) < humidity_score(45.0)

    def test_high_humidity_penalized(self):
        assert humidity_score(80.0) < humidity_score(45.0)

    def test_output_bounds_across_range(self):
        for rh in [0, 20, 45, 70, 100]:
            score = humidity_score(float(rh))
            assert 0.0 <= score <= 100.0

    def test_values_above_100_clamped(self):
        assert humidity_score(110.0) == humidity_score(100.0)


class TestNoiseScore:
    def test_optimal_noise_is_100(self):
        assert noise_score(50.0) == pytest.approx(100.0)

    def test_quiet_environment_penalized(self):
        assert noise_score(20.0) < 100.0

    def test_loud_environment_penalized(self):
        assert noise_score(80.0) < noise_score(50.0)

    def test_negative_db_clamped(self):
        assert noise_score(-5.0) == noise_score(0.0)

    def test_above_120_clamped(self):
        assert noise_score(150.0) == noise_score(120.0)


class TestTotalScore:
    def test_equal_weights_are_average(self):
        result = total_score(80.0, 60.0, 40.0, 20.0)
        assert result == pytest.approx(50.0)

    def test_all_100_returns_100(self):
        assert total_score(100.0, 100.0, 100.0, 100.0) == pytest.approx(100.0)


class TestCalculateScores:
    TYPICAL = {
        "temperature_c": 22.0,
        "light_lux":    500.0,
        "humidity_pct":  45.0,
        "noise_db":      50.0,
    }

    def test_returns_all_expected_keys(self):
        result = calculate_scores(self.TYPICAL)
        for key in (
            "temperature_score", "light_score",
            "humidity_score", "noise_score", "total_score",
        ):
            assert key in result

    def test_scores_are_integers_or_none(self):
        result = calculate_scores(self.TYPICAL)
        for v in result.values():
            assert v is None or isinstance(v, int)

    def test_optimal_readings_yield_high_scores(self):
        result = calculate_scores(self.TYPICAL)
        assert result["total_score"] >= 95

    def test_none_sensor_value_gives_none_score(self):
        readings = {**self.TYPICAL, "temperature_c": None}
        result = calculate_scores(readings)
        assert result["temperature_score"] is None

    def test_all_none_sensors_give_none_total(self):
        readings = {k: None for k in self.TYPICAL}
        result = calculate_scores(readings)
        assert result["total_score"] is None
