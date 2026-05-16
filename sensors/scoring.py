from __future__ import annotations

import numpy as np

from sensors.config import (
    TEMP_COEFF_A, TEMP_COEFF_B, TEMP_COEFF_C, TEMP_COEFF_D,
    LIGHT_OPTIMAL_LUX,
    HUMIDITY_OPTIMAL_PCT, HUMIDITY_K,
    NOISE_OPTIMAL_DB, NOISE_BELOW_SLOPE, NOISE_ABOVE_SLOPE,
    SCORE_WEIGHTS,
)


def _round_safe(v: object) -> int | None:
    try:
        return int(round(float(v)))  # type: ignore[arg-type]
    except Exception:
        return None


def temperature_score(temperature_c: float) -> float:
    """
    Return a 0–100 productivity score based on ambient temperature in Celsius.

    Uses a cubic polynomial fit derived from:
      Seppanen O. et al. (2006). "Effect of temperature on task performance
      in office environment." Lawrence Berkeley National Laboratory.
      https://indoor.lbl.gov/publications/effect-temperature-task-performance

    Optimal temperature is approximately 22 °C (71.6 °F). Output is clamped
    to [0, 100].
    """
    t = float(temperature_c)
    score = (
        TEMP_COEFF_A * t ** 3
        + TEMP_COEFF_B * t ** 2
        + TEMP_COEFF_C * t
        + TEMP_COEFF_D
    ) * 100
    return max(0.0, min(100.0, score))


def light_score(lux: float) -> float:
    """
    Return a 0–100 productivity score based on ambient light level.

    Uses a logarithmic approach-to-optimal model with 500 lux as the target,
    based on:
      Veitch J. & Newsham G. (1998). "Preferred luminous conditions in
      open-plan offices." Lighting Research & Technology, 30(3), 139–150.
      https://www.sciencedirect.com/science/article/abs/pii/S0272494413001060

      Eklund N. (2000). "Lighting quality and office work." IESNA.
      https://journals.sagepub.com/doi/10.1177/096032719002200201

    Output is clamped to [0, 100].
    """
    lux = max(0.0, float(lux))
    score = 100 * np.log(lux + 1) / np.log(LIGHT_OPTIMAL_LUX)
    return max(0.0, min(100.0, float(score)))


def humidity_score(humidity_pct: float) -> float:
    """
    Return a 0–100 comfort score based on relative humidity.

    Uses a quadratic penalty centered at 45 % RH, based on:
      Sterling E. et al. (1985). "Criteria for human exposure to humidity
      in occupied buildings." ASHRAE Transactions, 91(1), 611–622.
      https://pubmed.ncbi.nlm.nih.gov/15330775/

    Representative scores:
      45 % RH → 100   (optimal)
      30 % or 60 % RH → ~95
      20 % or 70 % RH → ~80
    """
    rh = max(0.0, min(100.0, float(humidity_pct)))
    score = (1.0 - HUMIDITY_K * (rh - HUMIDITY_OPTIMAL_PCT) ** 2) * 100
    return max(0.0, min(100.0, score))


def noise_score(db: float) -> float:
    """
    Return a 0–100 productivity score based on A-weighted noise level (dBA).

    Based on piecewise-linear wellbeing data from:
      Srinivasan K. et al. (2023). "Association between occupational noise
      exposure and physiological wellbeing." npj Digital Medicine.
      https://www.springernature.com/gp/open-science/about/the-fundamentals-of-open-access-and-open-research

    Physiological wellbeing is optimal at 50 dBA:
      - Below 50 dBA: +5.4 % loss per 10 dB drop
      - Above 50 dBA: +1.9 % loss per 10 dB rise
    """
    db = max(0.0, min(120.0, float(db)))
    if db <= NOISE_OPTIMAL_DB:
        score = 100.0 - NOISE_BELOW_SLOPE * ((NOISE_OPTIMAL_DB - db) / 10.0)
    else:
        score = 100.0 - NOISE_ABOVE_SLOPE * ((db - NOISE_OPTIMAL_DB) / 10.0)
    return max(0.0, min(100.0, score))


def total_score(
    temp: float,
    light: float,
    humidity: float,
    noise: float,
) -> float:
    """Return the weighted composite CCI score (0–100)."""
    return (
        temp     * SCORE_WEIGHTS["temperature"]
        + light  * SCORE_WEIGHTS["light"]
        + humidity * SCORE_WEIGHTS["humidity"]
        + noise  * SCORE_WEIGHTS["noise"]
    )


def calculate_scores(readings: dict) -> dict:
    """
    Compute individual and composite CCI scores from a readings dict.

    Expected keys: temperature_c, light_lux, humidity_pct, noise_db.
    Any value may be None (e.g. sensor unavailable); the corresponding score
    will also be None in that case.

    Returns a dict with keys:
      temperature_score, light_score, humidity_score, noise_score, total_score
    All values are integers in [0, 100] or None.
    """
    temp_s    = _round_safe(temperature_score(readings["temperature_c"])) if readings.get("temperature_c") is not None else None
    light_s   = _round_safe(light_score(readings["light_lux"]))           if readings.get("light_lux")     is not None else None
    hum_s     = _round_safe(humidity_score(readings["humidity_pct"]))     if readings.get("humidity_pct")  is not None else None
    noise_s   = _round_safe(noise_score(readings["noise_db"]))            if readings.get("noise_db")      is not None else None

    components = [v for v in (temp_s, light_s, hum_s, noise_s) if v is not None]
    tot = _round_safe(sum(components) / len(components)) if components else None

    return {
        "temperature_score": temp_s,
        "light_score":       light_s,
        "humidity_score":    hum_s,
        "noise_score":       noise_s,
        "total_score":       tot,
    }
