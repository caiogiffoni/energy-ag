from unittest.mock import MagicMock

import pytest

from utils import secrets_util
from workflow import process as process_module
from workflow.process import Process


def make_scraper(return_value=None, raises=None):
    """Fake scraper class whose get_production() returns/raises the given value.

    Accepts any call shape (with a `page` arg for weg/saj/solis, or none for growatt).
    """
    class FakeScraper:
        def get_production(self, *args, **kwargs):
            if raises:
                raise raises
            return return_value
    return FakeScraper


@pytest.fixture(autouse=True)
def no_vault(monkeypatch):
    monkeypatch.setattr(secrets_util, "_load_vault_secret", lambda: None)


@pytest.fixture(autouse=True)
def no_chromium_check(monkeypatch):
    monkeypatch.setattr(Process, "_ensure_chromium", lambda self: None)


@pytest.fixture
def fake_playwright():
    return MagicMock()


def test_start_posts_sheet_row_and_sends_email_on_full_success(monkeypatch, fake_playwright):
    monkeypatch.setattr(process_module, "Weg", make_scraper(("10.5", "Yield 10.5 kWh", "weg.png", "")))
    monkeypatch.setattr(process_module, "Saj", make_scraper(("1.1", "1.1", "saj.png", "")))
    monkeypatch.setattr(process_module, "Solis", make_scraper(("2.2", "2.2", "solis.png", "")))
    monkeypatch.setattr(process_module, "Growatt", make_scraper((3.3, "", "", "")))

    mock_post_to_sheets = MagicMock()
    mock_send_email = MagicMock()
    monkeypatch.setattr(process_module, "post_to_sheets", mock_post_to_sheets)
    monkeypatch.setattr(process_module, "send_generated_energy_email", mock_send_email)

    Process(fake_playwright).start()

    mock_post_to_sheets.assert_called_once_with(weg="10.5", saj="1.1", solis="2.2", growatt=3.3)
    mock_send_email.assert_called_once_with(
        ("10.5", "Yield 10.5 kWh", "weg.png", ""),
        ("1.1", "1.1", "saj.png", ""),
        ("2.2", "2.2", "solis.png", ""),
        (3.3, "", "", ""),
    )


def test_start_continues_after_one_scraper_fails_posts_sheet_but_skips_email(monkeypatch, fake_playwright):
    monkeypatch.setattr(process_module, "Weg", make_scraper(raises=RuntimeError("weg boom")))
    monkeypatch.setattr(process_module, "Saj", make_scraper(("1.1", "1.1", "saj.png", "")))
    monkeypatch.setattr(process_module, "Solis", make_scraper(("2.2", "2.2", "solis.png", "")))
    monkeypatch.setattr(process_module, "Growatt", make_scraper((3.3, "", "", "")))

    mock_post_to_sheets = MagicMock()
    mock_send_email = MagicMock()
    monkeypatch.setattr(process_module, "post_to_sheets", mock_post_to_sheets)
    monkeypatch.setattr(process_module, "send_generated_energy_email", mock_send_email)

    with pytest.raises(RuntimeError, match="weg boom"):
        Process(fake_playwright).start()

    mock_post_to_sheets.assert_called_once()
    kwargs = mock_post_to_sheets.call_args.kwargs
    assert kwargs["weg"] == ""  # failed scraper contributes a blank
    assert kwargs["saj"] == "1.1"
    assert kwargs["solis"] == "2.2"
    assert kwargs["growatt"] == 3.3
    mock_send_email.assert_not_called()


def test_start_growatt_failure_does_not_block_other_scrapers(monkeypatch, fake_playwright):
    monkeypatch.setattr(process_module, "Weg", make_scraper(("10.5", "", "weg.png", "")))
    monkeypatch.setattr(process_module, "Saj", make_scraper(("1.1", "", "saj.png", "")))
    monkeypatch.setattr(process_module, "Solis", make_scraper(("2.2", "", "solis.png", "")))
    monkeypatch.setattr(process_module, "Growatt", make_scraper(raises=RuntimeError("growatt boom")))

    mock_post_to_sheets = MagicMock()
    mock_send_email = MagicMock()
    monkeypatch.setattr(process_module, "post_to_sheets", mock_post_to_sheets)
    monkeypatch.setattr(process_module, "send_generated_energy_email", mock_send_email)

    with pytest.raises(RuntimeError, match="growatt boom"):
        Process(fake_playwright).start()

    kwargs = mock_post_to_sheets.call_args.kwargs
    assert kwargs["growatt"] == ""
    mock_send_email.assert_not_called()
