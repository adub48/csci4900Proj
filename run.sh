#!/usr/bin/env bash
set -e

# Prefer local venv, fallback to a user venv if present
if [[ -f .venv/bin/activate ]]; then
	source .venv/bin/activate
elif [[ -f ~/.virtualenvs/pimoroni/bin/activate ]]; then
	# legacy path
	source ~/.virtualenvs/pimoroni/bin/activate
else
	echo "No virtual environment found. Creating .venv and installing requirements..."
	python3 -m venv .venv
	source .venv/bin/activate
	python -m pip install --upgrade pip
	if [[ -f requirements.txt ]]; then
		pip install -r requirements.txt
	fi
fi

exec python ./flask_app/app.py