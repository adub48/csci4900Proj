#!/usr/bin/env bash
set -euo pipefail

# Raspberry Pi setup script for CCI project
# - Installs system deps (I2C, PortAudio, build tools)
# - Enables I2C via raspi-config
# - Creates .venv and installs Python deps from requirements-rpi.txt

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$PROJECT_DIR"

if ! command -v sudo >/dev/null 2>&1; then
  echo "sudo is required to install system packages" >&2
  exit 1
fi

echo "[1/5] Updating apt lists..."
sudo apt-get update -y

echo "[2/5] Installing system packages..."
sudo apt-get install -y \
  python3-venv python3-dev python3-pip build-essential \
  libatlas-base-dev libopenblas-dev \
  libportaudio2 portaudio19-dev \
  i2c-tools python3-smbus

if command -v raspi-config >/dev/null 2>&1; then
  echo "[3/5] Enabling I2C with raspi-config..."
  sudo raspi-config nonint do_i2c 0 || true
  echo "[3b/5] Enabling SPI with raspi-config..."
  sudo raspi-config nonint do_spi 0 || true
else
  echo "raspi-config not found; skipping I2C enable step."
fi

mkdir -p data

echo "[4/5] Creating Python virtual env (.venv)..."
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip wheel setuptools

REQ_FILE="requirements-rpi.txt"
if [[ ! -f "$REQ_FILE" ]]; then
  echo "requirements-rpi.txt not found; falling back to requirements.txt"
  REQ_FILE="requirements.txt"
fi

echo "[5/5] Installing Python dependencies from $REQ_FILE ..."
pip install -r "$REQ_FILE"

echo "Done. Activate the environment with:"
echo "  source .venv/bin/activate"
echo "Run the app with:"
echo "  ./run.sh"