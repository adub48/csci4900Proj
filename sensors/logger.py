import os
import sqlite3
import time
from datetime import datetime, timezone

from bme280 import BME280
from ltr559 import LTR559

import sounddevice as sd
import numpy as np

from pathlib import Path
import sys

# ------------ CONFIG ------------
LOCATION_NAME = "Bedroom"  # default if no name is provided
LOG_INTERVAL_SECONDS = 5  # how often to log
NOISE_SAMPLE_DURATION = 0.1  # seconds of audio to sample for noise
NOISE_SAMPLE_RATE = 44100
# -------------------------------

bme = BME280()
ltr = LTR559()

BASE_DIR = Path(__file__).resolve().parent       # .../csci4900Proj/flask_app
PROJECT_ROOT = BASE_DIR.parent                   # .../csci4900Proj
sys.path.append(str(PROJECT_ROOT))

from sensors.scoring import calculateScores
from sensors.read_sensors import get_readings

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sensor_logs.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def ensure_db():
    """Create the sensor_logs table if it doesn't already exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sensor_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_utc TEXT NOT NULL,
            location TEXT NOT NULL,
            temperature_f REAL,
            humidity_pct REAL,
            light_lux REAL,
            noise_db REAL,
            temperature_score REAL,
            light_score REAL,
            humidity_score REAL,
            noise_score REAL,
            total_score REAL
        );
        """
    )

    conn.commit()
    conn.close()



def insert_reading(timestamp_utc, location, reading,scores):
    """Insert a single reading into the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO sensor_logs (
            timestamp_utc, location,
            temperature_f, humidity_pct, light_lux, noise_db,
            temperature_score, light_score, humidity_score, noise_score, total_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            timestamp_utc,
            location,
            reading["temperature_f"],
            reading["humidity_pct"],
            reading["light_lux"],
            reading["noise_db"],

            scores["temperature_score"],
            scores["light_score"],
            scores["humidity_score"],
            scores["noise_score"],
            scores["total_score"],
        ),
    )

    conn.commit()
    conn.close()


def main(name: str | None = None):
    

    now_utc = datetime.now(timezone.utc).isoformat()
    start = time.time()
    count = 0
    sum_tempC = 0.0
    sum_temp = 0.0
    sum_hum = 0.0
    sum_light = 0.0
    sum_noise = 0.0

    # Collect readings over LOG_INTERVAL_SECONDS seconds
    while time.time() - start < LOG_INTERVAL_SECONDS:
        raw = get_readings()
        sum_tempC += float(raw.get("temperature_c", 0.0))
        sum_temp += float(raw.get("temperature_f", 0.0))
        sum_hum += float(raw.get("humidity_pct", 0.0))
        sum_light += float(raw.get("light_lux", 0.0))
        sum_noise += float(raw.get("noise_db", 0.0))
        count += 1
        time.sleep(1)

    # Compute and print averages at the end of the interval
    avg_tempC = (sum_tempC / count) if count else 0.0
    avg_temp = (sum_temp / count) if count else 0.0
    avg_hum = (sum_hum / count) if count else 0.0
    avg_light = (sum_light / count) if count else 0.0
    avg_noise = (sum_noise / count) if count else 0.0

    now_utc = datetime.now(timezone.utc).isoformat()
    print(
        f"[{now_utc}] Averages over {LOG_INTERVAL_SECONDS}s — "
        f"Temp: {avg_temp:.2f} °F | Humidity: {avg_hum:.2f} % | Light: {avg_light:.2f} lux | Noise: {avg_noise:.5f} RMS"
    )
    
    reading = {
        "temperature_c": avg_tempC,
        "temperature_f": avg_temp,
        "humidity_pct":  avg_hum,
        "light_lux": avg_light,
        "noise_db": avg_noise,
    }
    scores = calculateScores(reading)
    print(f"Scores: {scores}\n")
    # Insert the averaged reading into the database
    ensure_db()
    location = name if (isinstance(name, str) and name.strip()) else LOCATION_NAME
    print(f"Location: {location}")
    print(f"Interval: {LOG_INTERVAL_SECONDS} seconds\n")
    insert_reading(now_utc, location, reading, scores)


if __name__ == "__main__":
    main()
