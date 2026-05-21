from utils.secrets_util import secret_or_env
from libraries.logger import get_logger
from libraries.decorators import screenshot_on_error
from pathlib import Path
from playwright.sync_api import expect
logger = get_logger(__name__)
from time import sleep

class Saj:
    def __init__(self):
        self.url = secret_or_env("SAJ_URL")
        self.login = secret_or_env("SAJ_LOGIN")
        self.password = secret_or_env("SAJ_PASSWORD")


    @screenshot_on_error("saj")
    def get_production(self, page) -> tuple[str, str, Path]:
        logger.info("Navigating to %s", self.url)
        page.goto(self.url, wait_until="domcontentloaded")

        logger.info("Logging in")
        page.get_by_role("textbox", name="Username/Email").fill(self.login or "")
        page.get_by_role("textbox", name="Please enter your password").fill(self.password or "")
        page.get_by_role("button", name="Login").click()

        logger.info("Waiting for dashboard column")
        production = page.locator(
            "p.tip:has-text(\"Today's production\") + p.value span:first-child"
        )
        expect(production).to_be_visible(timeout=60000)

        saj_production = production.inner_text()
        logger.info("Saj production: %s kWh", saj_production)

        out = Path(secret_or_env("ROBOT_ARTIFACTS", "output"))
        out.mkdir(parents=True, exist_ok=True)
        shot = out / "saj_energy_data.png"
        sleep(5)
        page.get_by_text("Curve Analysis ToDayWeekMonthYearTotal Export Lifetime Production :").screenshot(path=shot)
        logger.info("Screenshot saved to %s", shot)

        return saj_production, saj_production, shot