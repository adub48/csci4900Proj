"""
Central configuration for the Cognitive Comfort Index system.

All hardware calibration constants, scoring model parameters, and
operational settings live here. Import from this module instead of
hard-coding values elsewhere.
"""

# ---------------------------------------------------------------------------
# Hardware / Calibration
# ---------------------------------------------------------------------------

# Empirical factor that removes CPU heat bleed-through from the BME280 reading.
# Increase this value if the sensor reads warmer than a reference thermometer.
CPU_COMP_FACTOR: float = 1.5

# dB offset added to the raw RMS-to-dB conversion for the USB microphone.
# Calibrate against a phone SPL meter in a known-quiet environment (~35 dBA).
NOISE_CALIBRATION_OFFSET: float = 70.0

# Audio capture parameters for noise sampling.
NOISE_SAMPLE_DURATION: float = 0.1   # seconds
NOISE_SAMPLE_RATE: int = 44_100      # Hz

# ---------------------------------------------------------------------------
# Logger / Database
# ---------------------------------------------------------------------------

LOG_INTERVAL_SECONDS: int = 5
DEFAULT_LOCATION_NAME: str = "Bedroom"
MAX_LOCATION_NAME_LEN: int = 60      # enforced in app.py input validation

# ---------------------------------------------------------------------------
# Scoring model coefficients
# ---------------------------------------------------------------------------

# Temperature model — cubic polynomial fit from:
#   Seppanen O. et al. (2006). "Effect of temperature on task performance
#   in office environment." Lawrence Berkeley National Laboratory.
#   https://indoor.lbl.gov/publications/effect-temperature-task-performance
# Optimal temperature is approximately 22 °C (71.6 °F).
TEMP_COEFF_A: float =  0.0000623
TEMP_COEFF_B: float = -0.0058274
TEMP_COEFF_C: float =  0.1647524
TEMP_COEFF_D: float = -0.4685328

# Light model — log scale; optimal lux from:
#   Veitch J. & Newsham G. (1998). "Preferred luminous conditions in open-plan
#   offices." Lighting Research & Technology, 30(3), 139–150.
#   https://www.sciencedirect.com/science/article/abs/pii/S0272494413001060
LIGHT_OPTIMAL_LUX: float = 500.0

# Humidity model — quadratic penalty centered at 45 % RH; coefficients from:
#   Sterling E. et al. (1985). "Criteria for human exposure to humidity in
#   occupied buildings." ASHRAE Transactions, 91(1), 611–622.
#   https://pubmed.ncbi.nlm.nih.gov/15330775/
# Tuned so that 30 % or 60 % RH yields ~95 % of optimal score.
HUMIDITY_OPTIMAL_PCT: float = 45.0
HUMIDITY_K: float = 0.000222

# Noise model — piecewise linear from:
#   Srinivasan K. et al. (2023). "Association between occupational noise
#   exposure and physiological wellbeing." npj Digital Medicine.
#   https://www.springernature.com/gp/open-science/about/the-fundamentals-of-open-access-and-open-research
# Physiological wellbeing is optimal at 50 dBA.
NOISE_OPTIMAL_DB: float = 50.0
NOISE_BELOW_SLOPE: float = 5.4   # % wellbeing loss per 10 dB below optimal
NOISE_ABOVE_SLOPE: float = 1.9   # % wellbeing loss per 10 dB above optimal

# Score aggregation weights (must sum to 1.0).
SCORE_WEIGHTS: dict = {
    "temperature": 0.25,
    "light":       0.25,
    "humidity":    0.25,
    "noise":       0.25,
}
