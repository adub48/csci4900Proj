from __future__ import annotations

import logging
import math
import os
import time

import numpy as np

from sensors.config import (
    CPU_COMP_FACTOR,
    NOISE_CALIBRATION_OFFSET,
    NOISE_SAMPLE_DURATION,
    NOISE_SAMPLE_RATE,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy hardware accessors — imports and sensor objects are created on first
# use so the module can be imported on any machine without crashing.
# ---------------------------------------------------------------------------

_bme = None
_ltr = None


def _get_bme():
    global _bme
    if _bme is None:
        try:
            from bme280 import BME280
            _bme = BME280()
        except Exception as exc:
            logger.warning("BME280 unavailable: %s", exc)
    return _bme


def _get_ltr():
    global _ltr
    if _ltr is None:
        try:
            from ltr559 import LTR559
            _ltr = LTR559()
        except Exception as exc:
            logger.warning("LTR559 unavailable: %s", exc)
    return _ltr


# ---------------------------------------------------------------------------
# Sensor reading functions
# ---------------------------------------------------------------------------

def temperature_c() -> float | None:
    """Return the current temperature in Celsius with CPU heat compensation."""
    bme = _get_bme()
    if bme is None:
        return None
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            cpu_temp = int(f.read().strip()) / 1000.0
        raw_temp = bme.get_temperature()
        return raw_temp - ((cpu_temp - raw_temp) / CPU_COMP_FACTOR)
    except Exception as exc:
        logger.warning("temperature_c read failed: %s", exc)
        return None


def temperature_f() -> float | None:
    """Return the current temperature in Fahrenheit."""
    c = temperature_c()
    return None if c is None else c * 9.0 / 5.0 + 32.0


def humidity() -> float | None:
    """Return the current relative humidity percentage."""
    bme = _get_bme()
    if bme is None:
        return None
    try:
        return bme.get_humidity()
    except Exception as exc:
        logger.warning("humidity read failed: %s", exc)
        return None


def light() -> float | None:
    """Return the current ambient light level in lux."""
    ltr = _get_ltr()
    if ltr is None:
        return None
    try:
        return ltr.get_lux()
    except Exception as exc:
        logger.warning("light read failed: %s", exc)
        return None


def noise() -> float | None:
    """
    Return an estimated A-weighted noise level in dBA.

    Records a short audio burst, computes the RMS amplitude, and converts
    to dB using the calibration offset defined in sensors/config.py.
    Returns None if the audio device is unavailable.
    """
    try:
        import sounddevice as sd
        samples = sd.rec(
            int(NOISE_SAMPLE_DURATION * NOISE_SAMPLE_RATE),
            samplerate=NOISE_SAMPLE_RATE,
            channels=1,
            dtype="float32",
        )
        sd.wait()
    except Exception as exc:
        logger.warning("Noise measurement failed: %s", exc)
        return None

    samples = samples[:, 0]
    rms = float(np.sqrt(np.mean(samples ** 2)))
    if rms <= 1e-12:
        return 0.0
    return 20 * math.log10(rms) + NOISE_CALIBRATION_OFFSET


# ---------------------------------------------------------------------------
# Aggregate reading + mock mode
# ---------------------------------------------------------------------------

# Set MOCK_SENSORS=1 in the environment to run the app without hardware.
# Useful for development and demos on non-Pi machines.
_MOCK = os.getenv("MOCK_SENSORS", "0") == "1"

_MOCK_READINGS: dict = {
    "temperature_c": 22.0,
    "temperature_f": 71.6,
    "humidity_pct":  45.0,
    "light_lux":    350.0,
    "noise_db":      48.0,
}


def get_readings() -> dict:
    """Return a dict of current sensor readings (or mock values if MOCK_SENSORS=1)."""
    if _MOCK:
        return dict(_MOCK_READINGS)
    return {
        "temperature_c": temperature_c(),
        "temperature_f": temperature_f(),
        "humidity_pct":  humidity(),
        "light_lux":     light(),
        "noise_db":      noise(),
    }


if __name__ == "__main__":
    while True:
        print(get_readings())
        time.sleep(1)
