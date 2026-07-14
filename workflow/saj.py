import math
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect

from libraries.decorators import retry_on_timeout, screenshot_on_error
from libraries.logger import get_logger
from utils.secrets_util import secret_or_env

logger = get_logger(__name__)
from time import sleep


class Saj:
    def __init__(self):
        self.url = secret_or_env("SAJ_URL")
        self.login = secret_or_env("SAJ_LOGIN")
        self.password = secret_or_env("SAJ_PASSWORD")


    @screenshot_on_error("saj")
    @retry_on_timeout(retries=2, base_timeout=60_000, timeout_multiplier=2.0)
    def get_production(self, page, timeout: int = 60_000) -> tuple[str, str, Path, str]:
        notes = ""
        logger.info("Navigating to %s", self.url)
        page.goto(self.url, wait_until="domcontentloaded", timeout=timeout)

        curve_card = page.locator(".plant-chart-card").filter(has_text="Curve Analysis")
        login_box = page.get_by_role("textbox", name="Username/Email")
        # Whichever renders first decides: login form on a fresh page, dashboard
        # card when a retry reuses the already-authenticated page
        login_box.or_(curve_card).first.wait_for(state="visible", timeout=timeout)
        if login_box.is_visible():
            logger.info("Logging in")
            login_box.fill(self.login or "", timeout=timeout)
            page.get_by_role("textbox", name="Password").fill(self.password or "", timeout=timeout)
            page.get_by_text("Login").click(timeout=timeout)
        else:
            logger.info("Session active - skipping login")
            notes += "Session was active - login skipped\n"

        logger.info("Waiting for dashboard column")
        production = curve_card.locator("span.text-2xl.font-bold")
        expect(production).to_be_visible(timeout=timeout)

        saj_production = production.inner_text()
        logger.info("Saj production: %s kWh", saj_production)

        out = Path(secret_or_env("ROBOT_ARTIFACTS", "output"))
        out.mkdir(parents=True, exist_ok=True)
        shot = out / "saj_energy_data.png"
        try:
            curve_card.scroll_into_view_if_needed(timeout=15_000)
            sleep(3)
            curve_card.screenshot(path=shot, timeout=15_000, animations="disabled")
            logger.info("Screenshot saved to %s", shot)
        except PlaywrightTimeoutError:
            page.screenshot(path=shot, full_page=True)
            logger.warning("Card screenshot timed out - saved full-page fallback to %s", shot)
            notes += "Card screenshot timed out - full-page fallback used\n"

        attempt_num = int(math.log2(timeout // 60_000)) + 1
        notes += f"Succeeded on attempt {attempt_num}/3\n"

        return saj_production, saj_production, shot, notes


if __name__ == "__main__":
    from dotenv import load_dotenv
    from playwright.sync_api import sync_playwright
    load_dotenv()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        saj = Saj()
        saj.get_production(page)