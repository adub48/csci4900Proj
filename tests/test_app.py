"""
Integration tests for Flask routes in flask_app/app.py.

Hardware calls are patched so these tests run on any machine without a Pi.
"""
import json
import pytest
from unittest.mock import MagicMock, patch

FAKE_READINGS = {
    "temperature_c": 22.0,
    "temperature_f": 71.6,
    "humidity_pct":  45.0,
    "light_lux":    350.0,
    "noise_db":      48.0,
}
FAKE_SCORES = {
    "temperature_score": 90,
    "light_score":       88,
    "humidity_score":    97,
    "noise_score":       99,
    "total_score":       94,
}


@pytest.fixture
def client():
    with (
        patch("sensors.read_sensors._get_bme", return_value=MagicMock()),
        patch("sensors.read_sensors._get_ltr", return_value=MagicMock()),
        patch("sensors.read_sensors.get_readings", return_value=FAKE_READINGS),
        patch("sensors.scoring.calculate_scores", return_value=FAKE_SCORES),
        patch("flask_app.app.ensure_db"),
        patch("flask_app.app.log_reading"),
    ):
        from flask_app.app import app
        app.config["TESTING"] = True
        with app.test_client() as c:
            yield c


class TestIndexRoute:
    def test_returns_200(self, client):
        assert client.get("/").status_code == 200

    def test_contains_product_name(self, client):
        assert b"Cognitive Comfort Index" in client.get("/").data


class TestSensorsRoute:
    def test_returns_json(self, client):
        r = client.get("/sensors")
        assert r.content_type == "application/json"

    def test_contains_readings_and_scores(self, client):
        data = json.loads(client.get("/sensors").data)
        assert "readings" in data
        assert "scores" in data


class TestLogRoute:
    def test_missing_name_returns_400(self, client):
        assert client.post("/api/log", json={}).status_code == 400

    def test_empty_name_returns_400(self, client):
        assert client.post("/api/log", json={"name": ""}).status_code == 400

    def test_valid_name_returns_200(self, client):
        r = client.post("/api/log", json={"name": "Library 3rd Floor"})
        assert r.status_code == 200

    def test_name_too_long_returns_400(self, client):
        r = client.post("/api/log", json={"name": "A" * 61})
        assert r.status_code == 400

    def test_script_tag_in_name_returns_400(self, client):
        r = client.post("/api/log", json={"name": "<script>alert(1)</script>"})
        assert r.status_code == 400


class TestLeaderboardRoute:
    def test_returns_list(self, client):
        data = json.loads(client.get("/leaderboard").data)
        assert isinstance(data, list)
