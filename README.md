# Cognitive Comfort Index (CCI)
A real-time environmental monitoring and productivity-scoring system built using a Raspberry Pi and the Pimoroni Enviro Mini.

## Overview
The Cognitive Comfort Index (CCI) is a real-time monitoring platform designed to evaluate how conducive an environment is to productive work. Using a Raspberry Pi combined with an Enviro Mini sensor board, the system measures temperature, humidity, light, and noise, processes these values using a research-informed scoring model, and computes a unified productivity score ranging from 1 to 100.

The results are displayed on a live Flask-based web dashboard. Users may also save study locations to a NoSQL-backed leaderboard, allowing comparison across different environments and identification of the most productive spaces.

## Features
- Real-time environmental measurements with rapid update frequency
- Calibrated readings for temperature, humidity, lux, and noise
- Cognitive Comfort Index (CCI) with individual factor scores
- Flask-based web dashboard with dynamic visualization
- Study spot saving and global leaderboard functionality
- Modular Python architecture for easy extensibility

## System Architecture
 ┌────────────────────┐
 │   Enviro Mini      │
 │ Temp / Light /     │
 │ Humidity / Noise   │
 └─────────┬──────────┘
           ▼
 ┌────────────────────┐
 │   sensors/         │
 │ read_sensors.py    │
 │ noise_reader.py    │
 └─────────┬──────────┘
           ▼
 ┌────────────────────┐
 │   scoring.py       │
 │ Normalize + Score  │
 └─────────┬──────────┘
           ▼
 ┌────────────────────┐
 │ Flask Web Server   │
 │ /sensors /scores   │
 └─────────┬──────────┘
           ▼
 ┌────────────────────┐
 │ Frontend UI        │
 │ HTML/CSS/JS        │
 └────────────────────┘

## Repository Structure
csci4900Proj/
├── data/                 # SQLite DB and other data artifacts
├── flask_app/
│   ├── app.py            # Flask application entrypoint
│   ├── templates/
│   │   └── index.html    # Main dashboard page
│   └── static/
│       ├── css/
│       │   └── style.css
│       └── js/
│           └── main.js
├── sensors/
│   ├── read_sensors.py   # Reads temperature, humidity, light, noise
│   ├── logger.py         # Periodic logger to SQLite
│   └── scoring.py        # Scoring utilities
├── scripts/
│   └── setup_rpi.sh      # Raspberry Pi setup helper
├── requirements.txt      # Pi-focused Python dependencies
├── requirements-rpi.txt  # Primary Pi requirements file
├── run.sh                # Helper to activate venv and start Flask app
└── README.md

## Prerequisites

### Hardware
- Raspberry Pi (tested on Pi 4)
- Pimoroni Enviro Mini
- MicroSD card and power supply
- Wi-Fi connection

### Software
- Python 3.9 or later
- Flask
- Pimoroni Enviro+ libraries (provides `bme280`, `ltr559`)

## Installation and Setup (Raspberry Pi)

This project is intended to run on a Raspberry Pi with a Pimoroni Enviro Mini / Enviro+ HAT.

1. Clone the repository:
```bash
git clone https://github.com/adub48/csci4900Proj
cd csci4900Proj
```

2. Run the Raspberry Pi setup script (recommended):
```bash
bash scripts/setup_rpi.sh
```
This will:
- Update/refresh APT package lists
- Install system packages (Python tooling, BLAS, PortAudio, I2C tools)
- Enable I²C and SPI via `raspi-config`
- Create a `.venv` virtual environment
- Install Python dependencies from `requirements-rpi.txt`

3. Start the app:
```bash
./run.sh
```

4. In a browser on your laptop/phone, navigate to:
```text
http://<your_pi_ip>:5000
```

### Manual Raspberry Pi setup (alternative)

If you don’t want to use the script, follow Pimoroni’s Enviro+ guide and then:

1. Enable I²C and SPI using `raspi-config`.
2. Install system packages:
```bash
sudo apt-get update
sudo apt-get install -y \
    python3-venv python3-dev build-essential \
    libatlas-base-dev libopenblas-dev \
    libportaudio2 portaudio19-dev \
    i2c-tools python3-smbus
```
3. Create and activate a venv, then install Python dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements-rpi.txt
```
4. Run the app with `./run.sh` as above.

Open a browser and navigate to:
```text
http://<your_pi_ip>:5000
```

## Future Improvements
- Integration of full Enviro+ hardware to include particulate and air-quality sensing
- Improved noise smoothing and filtering algorithms
- Historical data visualizations and analytical charts
- User accounts and personalized dashboards
- Machine learning–based scoring enhancements

## License
This project was developed for academic and educational purposes. Users are welcome to fork, modify, and extend the project.

## Acknowledgments
- CSCI 4900
- Pimoroni Enviro hardware
