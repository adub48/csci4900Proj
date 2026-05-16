from pathlib import Path

# Sensor sampling
NOISE_SAMPLE_DURATION = 0.1   # seconds of audio per measurement
NOISE_SAMPLE_RATE     = 44100  # Hz

# Logging
LOG_INTERVAL_SECONDS = 5       # how many seconds to average over
LOCATION_NAME        = "Bedroom"  # default location name

# Database
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH      = str(PROJECT_ROOT / "data" / "sensor_logs.db")
