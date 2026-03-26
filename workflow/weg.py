from secrets_util import secret_or_env
from libraries.logger import get_logger
from pathlib import Path
from playwright.sync_api import expect
logger = get_logger(__name__)

class Weg:
    def __init__(self):
        self.url = secret_or_env("FUSION_URL")
        self.login = secret_or_env("FUSION_LOGIN")
        self.password = secret_or_env("FUSION_PASSWORD")


    def get_production(self, page) -> tuple[str, str, Path]:
        logger.info("Navigating to %s", self.url)
        page.goto(self.url, wait_until="domcontentloaded")

        logger.info("Logging in")
        page.get_by_role("textbox", name="Username or email").fill(self.login or "")
        page.get_by_role("textbox", name="Password").fill(self.password or "")
        page.locator("#btn_outerverify").click()

        logger.info("Waiting for dashboard column")
        col = page.locator(".col-content.margin-right-075rem")
        expect(col).to_be_visible(timeout=60000)
        col.click()

        weg_title = page.locator(".nco-product-power-center").get_attribute("title")
        # e.g. title 'Yield 322.69 kWh'
        parts = (weg_title or "").split()
        weg_production = parts[1] if len(parts) > 1 else ""
        logger.info("WEG title: %r  →  production: %s kWh", weg_title, weg_production)

        out = Path(secret_or_env("ROBOT_ARTIFACTS", "output"))
        out.mkdir(parents=True, exist_ok=True)
        shot = out / "weg_energy_data.png"
        col.screenshot(path=shot)
        logger.info("Screenshot saved to %s", shot)

        return weg_production, weg_title, shot