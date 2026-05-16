from __future__ import annotations

import logging
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent   # .../csci4900Proj/flask_app
PROJECT_ROOT = BASE_DIR.parent               # .../csci4900Proj
sys.path.append(str(PROJECT_ROOT))

from sensors.config import MAX_LOCATION_NAME_LEN
from sensors.logger import ensure_db, main as log_reading
from sensors.read_sensors import get_readings
from sensors.scoring import calculate_scores

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Coordinates sensor access between the live-feed and log routes so a
# 5-second logging run doesn't race with a /sensors poll.
sensor_lock = Lock()

_VALID_NAME_RE = re.compile(r"^[\w\s\-',.()]{1,60}$")


# ------------ ROUTES ------------

@app.route("/")
def index():
    """Render the main dashboard page."""
    return render_template("index.html")


@app.route("/sensors", methods=["GET"])
def sensors():
    """
    Return the latest sensor readings and CCI scores as JSON.

    Acquires the sensor lock so this call pauses if /api/log is currently
    running its 5-second averaging routine.
    """
    with sensor_lock:
        readings = get_readings()
    scores = calculate_scores(readings)
    return jsonify({"readings": readings, "scores": scores})


@app.route("/api/log", methods=["POST"])
def api_log():
    """
    Average sensor readings over a short interval and persist them under
    the provided location name.

    Request body (JSON): { "name": "<study spot name>" }
    """
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()

    if not name:
        return jsonify({"status": "error", "message": "Name is required."}), 400
    if len(name) > MAX_LOCATION_NAME_LEN:
        return jsonify({
            "status": "error",
            "message": f"Name must be {MAX_LOCATION_NAME_LEN} characters or fewer.",
        }), 400
    if not _VALID_NAME_RE.match(name):
        return jsonify({
            "status": "error",
            "message": "Name contains invalid characters.",
        }), 400

    try:
        with sensor_lock:
            log_reading(name)
        return jsonify({"status": "success", "message": "Reading logged.", "name": name})
    except Exception:
        logger.exception("Failed to log reading for %r", name)
        return jsonify({"status": "error", "message": "Internal error while logging."}), 500


@app.route("/leaderboard", methods=["GET"])
def leaderboard():
    """
    Return the best (highest CCI) reading per location, sorted descending.
    """
    db_path = PROJECT_ROOT / "data" / "sensor_logs.db"
    try:
        ensure_db()
    except Exception:
        logger.exception("Could not ensure database")
        return jsonify([])

    if not db_path.exists():
        return jsonify([])

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT sl.timestamp_utc, sl.location,
                   sl.temperature_score, sl.humidity_score,
                   sl.light_score, sl.noise_score, sl.total_score
            FROM sensor_logs sl
            INNER JOIN (
                SELECT location, MAX(timestamp_utc) AS max_ts
                FROM sensor_logs
                GROUP BY location
            ) latest
              ON latest.location = sl.location
             AND latest.max_ts   = sl.timestamp_utc
            ORDER BY sl.total_score DESC;
            """
        )
        rows = cur.fetchall()
        conn.close()
    except Exception:
        logger.exception("Leaderboard query failed")
        return jsonify([])

    return jsonify([
        {
            "timestamp_utc":     r["timestamp_utc"],
            "location":          r["location"],
            "temperature_score": r["temperature_score"],
            "humidity_score":    r["humidity_score"],
            "light_score":       r["light_score"],
            "noise_score":       r["noise_score"],
            "total_score":       r["total_score"],
        }
        for r in rows
    ])


# ------------ ENTRYPOINT ------------

if __name__ == "__main__":
    # 0.0.0.0 makes the dashboard reachable from other devices on the network.
    app.run(host="0.0.0.0", port=5000, debug=False)
