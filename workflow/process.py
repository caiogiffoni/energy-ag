import os
import subprocess
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

from libraries.logger import get_logger
from utils.secrets_util import secret_or_env
from utils.utils import send_generated_energy_email
from workflow.growatt import Growatt
from workflow.saj import Saj
from workflow.solis import Solis
from workflow.weg import Weg

logger = get_logger(__name__)


def _ensure_chromium():
    cache = Path.home() / ".cache" / "ms-playwright"
    if not any(cache.glob("chromium-*/chrome-linux64/chrome")):
        logger.info("Chromium not found — installing via playwright")
        subprocess.run(["playwright", "install", "chromium"], check=True)


def _run_browser_scraper(scraper_class, headless, results, errors, key):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        try:
            page = browser.new_page()
            results[key] = scraper_class().get_production(page)
        except Exception as e:
            errors[key] = e
        finally:
            browser.close()


class Process:
    def start(self):
        _ensure_chromium()
        headless = os.environ.get("HEADLESS", "true").lower() != "false"

        results = {}
        errors = {}

        threads = [
            threading.Thread(target=_run_browser_scraper, args=(Weg, headless, results, errors, "weg")),
            threading.Thread(target=_run_browser_scraper, args=(Saj, headless, results, errors, "saj")),
            threading.Thread(target=_run_browser_scraper, args=(Solis, headless, results, errors, "solis")),
        ]

        growatt = Growatt()
        for t in threads:
            t.start()
        growatt_info = growatt.get_production()
        for t in threads:
            t.join()

        if errors:
            for key, err in errors.items():
                logger.error("%s scraper failed: %s", key, err)
            raise next(iter(errors.values()))

        send_generated_energy_email(results["weg"], results["saj"], results["solis"], growatt_info)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    Process().start()
