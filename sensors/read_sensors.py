from bme280 import BME280
from ltr559 import LTR559
import sounddevice as sd
import numpy as np
import time
import os
import math

# Initialize sensors
bme = BME280()
ltr = LTR559()


def temperature_c():
    """Return the current temperature in Celsius."""
    with open("/sys/class/thermal/thermal_zone0/temp") as f:
        cpu_temp = int(f.read().strip())
        cpu_temp = cpu_temp / 1000.0  # Convert millidegree to degrees Celsius
    
    CPU_COMP_FACTOR = 1.5  # adjust until it matches a real thermometer
    raw_temp = bme.get_temperature()
    comp_temp = raw_temp - ((cpu_temp - raw_temp) / CPU_COMP_FACTOR)
    return comp_temp

def temperature_f():
    """Return the current temperature in Farenheit."""
    c = temperature_c()
    f = c * 9.0 / 5.0 + 32.0
    return f

def humidity():
    """Return the current humidity percentage."""
    return bme.get_humidity()

# pressure sensor removed — not used anymore

def light():
    """Return the current light level in lux."""
    return ltr.get_lux()

def noise():
    calibration_offset = 70  # adjust as needed
    duration = 0.1  # seconds
    sample_rate = 44100

    try:
        samples = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype='float32'
        )
        sd.wait()
    except Exception as e:
        # If recording fails (no device, etc.), fall back to a neutral value
        print("Noise measurement failed:", e)
        return 37.8  # e.g., your "quiet" baseline

    samples = samples[:, 0]  # ensure 1D
    rms = float(np.sqrt(np.mean(samples**2)))

    # Avoid log10(0)
    if rms <= 1e-12:
        return 0.0

    raw_db = 20 * math.log10(rms)
    db = raw_db + calibration_offset
    return db

    
    
def get_readings():
    """Return a dict of current sensor readings."""
    return {
        "temperature_c": temperature_c(),
        "temperature_f": temperature_f(),
        "humidity_pct":  humidity(),
        "light_lux": light(),
        "noise_db": noise(),
}
    
if __name__ == "__main__":
    while True:
        readings = get_readings()
        print(readings)
        time.sleep(1)
