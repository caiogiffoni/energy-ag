
import logging
from datetime import date

import pytest

from utils import secrets_util
from workflow.growatt import Growatt


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


@pytest.fixture(autouse=True)
def no_vault(monkeypatch):
    monkeypatch.setattr(secrets_util, "_load_vault_secret", lambda: None)


@pytest.fixture(autouse=True)
def growatt_env(monkeypatch):
    monkeypatch.setenv("GROWATT_URL", "https://example.invalid/api")
    monkeypatch.setenv("GROWATT_TOKEN", "tok123")
    monkeypatch.setenv("GROWATT_SN", "SN123")
    monkeypatch.setenv("GROWATT_TYPE", "inverter")


def test_get_production_parses_response_and_posts_expected_payload(monkeypatch):
    captured = {}

    def fake_post(url, headers=None, data=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["data"] = data
        return FakeResponse({"data": {"datas": [{"eacToday": 10.567}]}})

    monkeypatch.setattr("workflow.growatt.requests.post", fake_post)

    result = Growatt().get_production()

    expected = round(10.567, 2)
    assert result == (expected, "", "", "")
    assert isinstance(result[0], float)

    assert captured["url"] == "https://example.invalid/api"
    assert captured["headers"]["token"] == "tok123"
    assert captured["data"]["deviceSn"] == "SN123"
    assert captured["data"]["deviceType"] == "inverter"
    assert captured["data"]["date"] == date.today().strftime("%Y-%m-%d")


def test_get_production_logs_url(monkeypatch, caplog):
    def fake_post(url, headers=None, data=None):
        return FakeResponse({"data": {"datas": [{"eacToday": 1.0}]}})

    monkeypatch.setattr("workflow.growatt.requests.post", fake_post)

    with caplog.at_level(logging.INFO):
        Growatt().get_production()

    assert "https://example.invalid/api" in caplog.text
