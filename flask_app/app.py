from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request

from bme280 import BME280
from ltr559 import LTR559
import sounddevice as sd
import numpy as np


from pathlib import Path
import sqlite3
import sys

BASE_DIR = Path(__file__).resolve().parent       # .../csci4900Proj/flask_app
PROJECT_ROOT = BASE_DIR.parent                   # .../csci4900Proj
sys.path.append(str(PROJECT_ROOT))

from sensors.scoring import calculateScores
from sensors.read_sensors import get_readings
from sensors.logger import main, ensure_db
from threading import Lock

import logging
log = logging.getLogger('werkzeug')

app = Flask(__name__)

# Global lock to coordinate sensor access between routes
sensor_lock = Lock()


# ------------ ROUTES ------------

@app.route("/")
def index():
    """
    Frontend page with a button. The JS on this page will call /api/read.
    """
    return render_template("index.html")


@app.route("/sensors", methods=["GET"])
def sensors():
    log.setLevel(logging.ERROR)
    # Wait here if another route (e.g. /api/log) is currently
    # holding the sensor lock while doing a longer measurement.
    with sensor_lock:
        readings = get_readings()
    scores = calculateScores(readings)
    return jsonify({"readings": readings, "scores": scores})

@app.route("/api/log", methods=["POST"])
def log_reading():
    log.setLevel(logging.INFO)
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    if not name or not isinstance(name, str):
        return jsonify({"status": "error", "message": "Missing or invalid 'name'"}), 400

    try:
        # Take exclusive access to the sensors while we perform
        # the longer logging routine so /sensors pauses until done.
        with sensor_lock:
            main(name)
        return jsonify({"status": "success", "message": "Reading logged.", "name": name})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/leaderboard", methods=["GET"])
def leaderboard():
    log.setLevel(logging.INFO)
    db_path = PROJECT_ROOT / "data" / "sensor_logs.db"
    # Make sure database and table exist so first load works
    try:
        ensure_db()
    except Exception:
        return jsonify([])
    if not db_path.exists():
        return jsonify([])

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Get the latest reading per location by max timestamp, then sort by total_score desc
    cur.execute(
        """
        SELECT sl.timestamp_utc, sl.location,
               sl.temperature_score, sl.humidity_score, sl.light_score, sl.noise_score, sl.total_score
        FROM sensor_logs sl
        INNER JOIN (
            SELECT location, MAX(timestamp_utc) AS max_ts
            FROM sensor_logs
            GROUP BY location
        ) latest ON latest.location = sl.location AND latest.max_ts = sl.timestamp_utc
        ORDER BY sl.total_score DESC;
        """
    )
    rows = cur.fetchall()
    conn.close()

    result = [
        {
            "timestamp_utc": r["timestamp_utc"],
            "location": r["location"],
            "temperature_score": r["temperature_score"],
            "humidity_score": r["humidity_score"],
            "light_score": r["light_score"],
            "noise_score": r["noise_score"],
            "total_score": r["total_score"],
        }
        for r in rows
    ]

    return jsonify(result)
    


# ------------ ENTRYPOINT ------------

if __name__ == "__main__":
    # 0.0.0.0 so you can reach it from your laptop on the same network
    app.run(host="0.0.0.0", port=5000, debug=False)
