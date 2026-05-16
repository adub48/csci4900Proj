from __future__ import annotations

import logging
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent   # .../csci4900Proj/sensors
PROJECT_ROOT = BASE_DIR.parent               # .../csci4900Proj
sys.path.append(str(PROJECT_ROOT))

from sensors.config import DEFAULT_LOCATION_NAME, LOG_INTERVAL_SECONDS
from sensors.read_sensors import get_readings
from sensors.scoring import calculate_scores

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(str(PROJECT_ROOT), "data", "sensor_logs.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def ensure_db() -> None:
    """Create the sensor_logs table and indexes if they do not already exist."""
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
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_sensor_logs_location ON sensor_logs(location);"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_sensor_logs_timestamp ON sensor_logs(timestamp_utc);"
    )
    conn.commit()
    conn.close()


def insert_reading(
    timestamp_utc: str,
    location: str,
    reading: dict,
    scores: dict,
) -> None:
    """Insert a single averaged reading into the SQLite database."""
    try:
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
    except Exception:
        logger.exception("Failed to insert reading for location %r", location)


def main(name: str | None = None) -> None:
    """
    Average sensor readings over LOG_INTERVAL_SECONDS seconds, score them,
    and persist the result to the database under the given location name.
    """
    now_utc = datetime.now(timezone.utc).isoformat()
    start = time.time()
    count = 0
    sum_temp_c = 0.0
    sum_temp_f = 0.0
    sum_hum    = 0.0
    sum_light  = 0.0
    sum_noise  = 0.0

    while time.time() - start < LOG_INTERVAL_SECONDS:
        raw = get_readings()
        sum_temp_c += float(raw.get("temperature_c") or 0.0)
        sum_temp_f += float(raw.get("temperature_f") or 0.0)
        sum_hum    += float(raw.get("humidity_pct")  or 0.0)
        sum_light  += float(raw.get("light_lux")     or 0.0)
        sum_noise  += float(raw.get("noise_db")      or 0.0)
        count += 1
        time.sleep(1)

    avg_temp_c = (sum_temp_c / count) if count else 0.0
    avg_temp_f = (sum_temp_f / count) if count else 0.0
    avg_hum    = (sum_hum    / count) if count else 0.0
    avg_light  = (sum_light  / count) if count else 0.0
    avg_noise  = (sum_noise  / count) if count else 0.0

    now_utc = datetime.now(timezone.utc).isoformat()
    logger.info(
        "[%s] %ds averages — Temp: %.2f °F | Humidity: %.2f %% | "
        "Light: %.2f lux | Noise: %.5f dB",
        now_utc, LOG_INTERVAL_SECONDS,
        avg_temp_f, avg_hum, avg_light, avg_noise,
    )

    reading = {
        "temperature_c": avg_temp_c,
        "temperature_f": avg_temp_f,
        "humidity_pct":  avg_hum,
        "light_lux":     avg_light,
        "noise_db":      avg_noise,
    }
    scores = calculate_scores(reading)
    logger.info("Scores: %s", scores)

    try:
        ensure_db()
    except Exception:
        logger.exception("Failed to ensure database schema")
        return

    location = name.strip() if (isinstance(name, str) and name.strip()) else DEFAULT_LOCATION_NAME
    logger.info("Logging location: %r over %ds", location, LOG_INTERVAL_SECONDS)
    insert_reading(now_utc, location, reading, scores)


if __name__ == "__main__":
    main()
