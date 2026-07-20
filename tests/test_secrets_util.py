import pytest

from utils import secrets_util
from utils.secrets_util import secret_or_env


class FakeVault:
    def __init__(self, data):
        self._data = data

    def get(self, key):
        return self._data.get(key)


def test_returns_default_when_key_missing():
    assert secret_or_env("NONEXISTENT_KEY", "default_val") == "default_val"


def test_returns_env_value_when_set(monkeypatch):
    monkeypatch.setattr(secrets_util, "_load_vault_secret", lambda: None)
    monkeypatch.setenv("SOME_TEST_KEY", "value123")
    assert secret_or_env("SOME_TEST_KEY") == "value123"


def test_vault_value_takes_precedence_over_env(monkeypatch):
    monkeypatch.setenv("SHARED_KEY", "env-value")
    monkeypatch.setattr(secrets_util, "_load_vault_secret", lambda: FakeVault({"SHARED_KEY": "vault-value"}))

    assert secret_or_env("SHARED_KEY") == "vault-value"


@pytest.mark.parametrize("vault_data", [{"SHARED_KEY": "  "}, {}], ids=["blank_value", "missing_key"])
def test_non_present_vault_value_falls_back_to_env(monkeypatch, vault_data):
    monkeypatch.setenv("SHARED_KEY", "env-value")
    monkeypatch.setattr(secrets_util, "_load_vault_secret", lambda: FakeVault(vault_data))

    assert secret_or_env("SHARED_KEY") == "env-value"
