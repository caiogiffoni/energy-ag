import os
import subprocess
from pathlib import Path

from libraries.logger import get_logger
from utils.secrets_util import secret_or_env
from utils.utils import post_to_sheets, send_generated_energy_email
from workflow.growatt import Growatt
from workflow.saj import Saj
from workflow.solis import Solis
from workflow.weg import Weg

logger = get_logger(__name__)


class Process:
    def __init__(self, playwright):
        self.playwright = playwright
        self.browser = None
        self.email_to = secret_or_env("EMAIL_TO")
        self.email_from = secret_or_env("EMAIL_FROM")

    def _ensure_chromium(self):
        cache = Path.home() / ".cache" / "ms-playwright"
        if not any(cache.glob("chromium-*/chrome-linux64/chrome")):
            logger.info("Chromium not found - installing via playwright")
            subprocess.run(["playwright", "install", "chromium"], check=True)

    def start(self):
        self._ensure_chromium()
        headless = os.environ.get("HEADLESS", "true").lower() != "false"
        self.browser = self.playwright.chromium.launch(headless=headless)
        page = self.browser.new_page()
        
        results = {}
        errors = {}
        for key, scraper_class in [("weg", Weg), ("saj", Saj), ("solis", Solis)]:
            try:
                results[key] = scraper_class().get_production(page)
            except Exception as e:
                logger.error("%s scraper failed - continuing with the rest: %s", key, e)
                errors[key] = e
                results[key] = ("", "", None, f"FAILED: {e}")
        try:
            results["growatt"] = Growatt().get_production()
        except Exception as e:
            logger.error("growatt scraper failed - continuing with the rest: %s", e)
            errors["growatt"] = e
            results["growatt"] = ("", "", None, f"FAILED: {e}")

        # Row goes out with blanks for failures
        post_to_sheets(
            weg=results["weg"][0],
            saj=results["saj"][0],
            solis=results["solis"][0],
            growatt=results["growatt"][0],
        )

        if errors:
            logger.error("Scrapers failed (%s) - sheet row posted, email skipped", ", ".join(errors))
            raise next(iter(errors.values()))

        send_generated_energy_email(results["weg"], results["saj"], results["solis"], results["growatt"])


if __name__ == "__main__":
    from dotenv import load_dotenv
    from playwright.sync_api import expect, sync_playwright
    load_dotenv()
    with sync_playwright() as p:
        process = Process(p)
        process.start()
