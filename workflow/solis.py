from pathlib import Path

from playwright.sync_api import expect

from libraries.decorators import screenshot_on_error
from libraries.logger import get_logger
from utils.secrets_util import secret_or_env

logger = get_logger(__name__)
import re
from time import sleep


class Solis:
    def __init__(self):
        self.url = secret_or_env("SOLIS_URL")
        self.login = secret_or_env("SOLIS_LOGIN")
        self.password = secret_or_env("SOLIS_PASSWORD")


    @screenshot_on_error("solis")
    def get_production(self, page) -> tuple[str, str, Path]:
        logger.info("Navigating to %s", self.url)
        page.goto(self.url, wait_until="domcontentloaded")

        logger.info("Logging in")
        page.get_by_role("textbox", name="Username/Email").fill(self.login or "")
        page.get_by_role("textbox", name="Password").fill(self.password or "")
        page.locator(".el-checkbox.el-checkbox--default.el-tooltip__trigger > .el-checkbox__input > .el-checkbox__inner").click()
        page.get_by_role("button", name="Login").click()

        logger.info("Waiting for dashboard")
        daily = page.locator("div").filter(has_text=re.compile(r"^Daily Yield$")).first
        expect(daily).to_be_visible(timeout=60000)
        # check if pop up is live. remove this later
        got_it = page.locator("button.el-button.el-button--default.el-button--small", has_text="Got it")
        if got_it.is_visible():
            got_it.click()

        with page.expect_popup() as page1_info:
            page.locator("div").filter(has_text=re.compile(r"^STATION_NAME$")).nth(1).click()
        new_page = page1_info.value
        production = new_page.locator(
            "div.feature-content"
        )
        
        expect(production).to_be_visible(timeout=60000)

        solis_production = new_page.locator(".electrical-info-item").filter(has_text="Daily Yield").locator(".f__24").inner_text()
        logger.info("Solis production: %s kWh", solis_production)

        out = Path(secret_or_env("ROBOT_ARTIFACTS", "output"))
        out.mkdir(parents=True, exist_ok=True)
        shot = out / "solis_energy_data.png"
        sleep(5)
        production.screenshot(path=shot)
        logger.info("Screenshot saved to %s", shot)

        return solis_production, solis_production, shot

if __name__ == "__main__":
    from dotenv import load_dotenv
    from playwright.sync_api import sync_playwright
    load_dotenv()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        solis = Solis()
        solis.get_production(page)
