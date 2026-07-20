import inspect
from unittest.mock import Mock

import pytest

from utils import secrets_util
from utils.email_util import send_email_with_image
from utils.utils import send_generated_energy_email

EXPECTED_KWARGS = {
    "to_addr", "subject", "body", "image_path",
    "smtp_host", "smtp_port", "smtp_user", "smtp_password", "from_addr",
}


@pytest.fixture(autouse=True)
def no_vault(monkeypatch):
    monkeypatch.setattr(secrets_util, "_load_vault_secret", lambda: None)


def test_send_email_with_image_signature():
    sig = inspect.signature(send_email_with_image)
    assert set(sig.parameters) == EXPECTED_KWARGS
    for param in sig.parameters.values():
        assert param.kind == inspect.Parameter.KEYWORD_ONLY


def test_send_generated_energy_email_computes_inversor2_and_subject(monkeypatch, tmp_path):
    monkeypatch.setenv("EMAIL_TO", "ops@example.com")
    monkeypatch.setenv("SMTP_USER", "user@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")

    mock_send = Mock()
    monkeypatch.setattr("utils.utils.send_email_with_image", mock_send)

    weg_shot = tmp_path / "weg.png"
    saj_shot = tmp_path / "saj.png"
    solis_shot = tmp_path / "solis.png"

    send_generated_energy_email(
        weg_info=("10.5", "Yield 10.5 kWh", weg_shot, ""),
        saj_info=("1.1", "", saj_shot, ""),
        solis_info=("2.2", "", solis_shot, ""),
        growatt_info=("3.3", "", "", ""),
    )

    mock_send.assert_called_once()
    kwargs = mock_send.call_args.kwargs
    assert kwargs["to_addr"] == "ops@example.com"
    assert kwargs["subject"] == "Weg: 10.5 kWh, II: 6.6 kWh"
    assert kwargs["image_path"] == [weg_shot, saj_shot, solis_shot]


def test_send_generated_energy_email_multiple_recipients(monkeypatch, tmp_path):
    monkeypatch.setenv("EMAIL_TO", "a@example.com, b@example.com")
    monkeypatch.setenv("SMTP_USER", "user@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")

    mock_send = Mock()
    monkeypatch.setattr("utils.utils.send_email_with_image", mock_send)

    shot = tmp_path / "shot.png"
    send_generated_energy_email(
        weg_info=("10.5", "", shot, ""),
        saj_info=("1.1", "", shot, ""),
        solis_info=("2.2", "", shot, ""),
        growatt_info=("3.3", "", "", ""),
    )

    assert mock_send.call_count == 2
    recipients = {call.kwargs["to_addr"] for call in mock_send.call_args_list}
    assert recipients == {"a@example.com", "b@example.com"}


def test_send_generated_energy_email_skips_when_email_to_unset(monkeypatch, tmp_path):
    monkeypatch.delenv("EMAIL_TO", raising=False)
    monkeypatch.setenv("SMTP_USER", "user@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")

    mock_send = Mock()
    monkeypatch.setattr("utils.utils.send_email_with_image", mock_send)

    shot = tmp_path / "shot.png"
    send_generated_energy_email(
        weg_info=("10.5", "", shot, ""),
        saj_info=("1.1", "", shot, ""),
        solis_info=("2.2", "", shot, ""),
        growatt_info=("3.3", "", "", ""),
    )

    mock_send.assert_not_called()


def test_send_generated_energy_email_skips_when_smtp_creds_unset(monkeypatch, tmp_path):
    monkeypatch.setenv("EMAIL_TO", "ops@example.com")
    monkeypatch.delenv("SMTP_USER", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)

    mock_send = Mock()
    monkeypatch.setattr("utils.utils.send_email_with_image", mock_send)

    shot = tmp_path / "shot.png"
    send_generated_energy_email(
        weg_info=("10.5", "", shot, ""),
        saj_info=("1.1", "", shot, ""),
        solis_info=("2.2", "", shot, ""),
        growatt_info=("3.3", "", "", ""),
    )

    mock_send.assert_not_called()
