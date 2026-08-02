import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from libraries.decorators import retry_on_timeout, screenshot_on_error


class FakePage:
    def __init__(self):
        self.screenshots = []

    def screenshot(self, path, full_page):
        self.screenshots.append(path)


def test_screenshot_on_error_saves_screenshot_and_reraises(monkeypatch, tmp_path):
    monkeypatch.setenv("ROBOT_ARTIFACTS", str(tmp_path))

    class Scraper:
        @screenshot_on_error("testscraper")
        def get_production(self, page):
            raise ValueError("boom")

    page = FakePage()

    with pytest.raises(ValueError, match="boom"):
        Scraper().get_production(page)

    assert len(page.screenshots) == 1
    saved_path = page.screenshots[0]
    assert saved_path.parent == tmp_path
    assert saved_path.name.startswith("testscraper_error_")
    assert saved_path.suffix == ".png"


def test_retry_on_timeout_retries_then_succeeds(monkeypatch, tmp_path):
    monkeypatch.setenv("ROBOT_ARTIFACTS", str(tmp_path))
    calls = []

    class Scraper:
        @retry_on_timeout(retries=2, base_timeout=1000, timeout_multiplier=2.0)
        def get_production(self, page, timeout):
            calls.append(timeout)
            if len(calls) < 3:
                raise PlaywrightTimeoutError("timed out")
            return "success"

    page = FakePage()
    result = Scraper().get_production(page)

    assert result == "success"
    assert calls == [1000, 2000, 4000]
    assert len(page.screenshots) == 2  # only the two failed attempts screenshot


def test_retry_on_timeout_raises_after_exhausting_retries(monkeypatch, tmp_path):
    monkeypatch.setenv("ROBOT_ARTIFACTS", str(tmp_path))
    calls = []

    class Scraper:
        @retry_on_timeout(retries=2, base_timeout=1000, timeout_multiplier=2.0)
        def get_production(self, page, timeout):
            calls.append(timeout)
            raise PlaywrightTimeoutError("always times out")

    page = FakePage()

    with pytest.raises(PlaywrightTimeoutError):
        Scraper().get_production(page)

    assert calls == [1000, 2000, 4000]
    assert len(page.screenshots) == 2  # final attempt re-raises without screenshotting
