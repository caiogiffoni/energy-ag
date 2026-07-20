from datetime import date
from unittest.mock import MagicMock

import pytest

from utils import secrets_util
from utils.utils import _get_gspread_client, post_to_sheets


@pytest.fixture(autouse=True)
def no_vault(monkeypatch):
    monkeypatch.setattr(secrets_util, "_load_vault_secret", lambda: None)


def test_get_gspread_client_returns_none_when_credentials_unset(monkeypatch):
    monkeypatch.delenv("GOOGLE_CREDENTIALS_JSON", raising=False)
    assert _get_gspread_client() is None


def test_post_to_sheets_skips_when_sheet_id_unset(monkeypatch):
    monkeypatch.delenv("GOOGLE_SHEET_ID", raising=False)
    mock_get_client = MagicMock()
    monkeypatch.setattr("utils.utils._get_gspread_client", mock_get_client)

    post_to_sheets(weg=1, saj=2, solis=3, growatt=4)

    mock_get_client.assert_not_called()


def test_post_to_sheets_skips_when_credentials_unset(monkeypatch):
    monkeypatch.setenv("GOOGLE_SHEET_ID", "sheet123")
    monkeypatch.setattr("utils.utils._get_gspread_client", lambda: None)

    post_to_sheets(weg=1, saj=2, solis=3, growatt=4)  # must not raise


def test_post_to_sheets_appends_new_row_when_no_existing_today_row(monkeypatch):
    monkeypatch.setenv("GOOGLE_SHEET_ID", "sheet123")
    mock_ws = MagicMock()
    mock_ws.get_all_values.return_value = [
        ["Date", "Weg", "Total", "", "", "", "Saj", "Solis", "Growatt"],  # header
        ["01/01/2025", "10", "=G2+H2+I2", "", "", "", "3", "4", "5"],
    ]
    mock_client = MagicMock()
    mock_client.open_by_key.return_value.sheet1 = mock_ws
    monkeypatch.setattr("utils.utils._get_gspread_client", lambda: mock_client)

    today_str = date.today().strftime("%d/%m/%Y")
    post_to_sheets(weg=11.1, saj=2.2, solis=3.3, growatt=4.4)

    mock_ws.update.assert_any_call("A3:C3", [[today_str, 11.1, "=G3+H3+I3"]], value_input_option="USER_ENTERED")
    mock_ws.update.assert_any_call("G3:I3", [[2.2, 3.3, 4.4]])


def test_post_to_sheets_overwrites_existing_today_row(monkeypatch):
    monkeypatch.setenv("GOOGLE_SHEET_ID", "sheet123")
    today_str = date.today().strftime("%d/%m/%Y")
    mock_ws = MagicMock()
    mock_ws.get_all_values.return_value = [
        ["Date", "Weg", "Total"],
        [today_str, "10", "=G2+H2+I2"],
    ]
    mock_client = MagicMock()
    mock_client.open_by_key.return_value.sheet1 = mock_ws
    monkeypatch.setattr("utils.utils._get_gspread_client", lambda: mock_client)

    post_to_sheets(weg=11.1, saj=2.2, solis=3.3, growatt=4.4)

    mock_ws.update.assert_any_call("A2:C2", [[today_str, 11.1, "=G2+H2+I2"]], value_input_option="USER_ENTERED")
    mock_ws.update.assert_any_call("G2:I2", [[2.2, 3.3, 4.4]])
