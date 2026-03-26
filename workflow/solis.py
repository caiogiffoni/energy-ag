from secrets_util import secret_or_env
from libraries.logger import get_logger
from pathlib import Path
from playwright.sync_api import expect
logger = get_logger(__name__)
from time import sleep

class Solis:
    def __init__(self):
        self.url = secret_or_env("SOLIS_URL")
        self.login = secret_or_env("SOLIS_LOGIN")
        self.password = secret_or_env("SOLIS_PASSWORD")


    def get_production(self, page) -> tuple[str, str, Path]:
        logger.info("Navigating to %s", self.url)
        page.goto(self.url, wait_until="domcontentloaded")

        logger.info("Logging in")
        page.get_by_role("textbox", name="Username/Email").fill(self.login or "")
        page.get_by_role("textbox", name="Password").fill(self.password or "")
        page.locator(".el-checkbox.el-checkbox--default.el-tooltip__trigger > .el-checkbox__input > .el-checkbox__inner").click()
        page.get_by_role("button", name="Login").click()

        logger.info("Waiting for dashboard column")
        page.locator("div.is-scrolling-left table tbody tr.el-table__row").click()
        production = page.locator(
            "p.item-title:has-text('Daily Yield') ~ div.item-content span.f__24"
        )
        
        expect(production).to_be_visible(timeout=60000)

        solis_production = production.inner_text()
        logger.info("Solis production: %s kWh", solis_production)

        out = Path(secret_or_env("ROBOT_ARTIFACTS", "output"))
        out.mkdir(parents=True, exist_ok=True)
        shot = out / "solis_energy_data.png"
        sleep(5)
        page.locator("div.station-echarts").screenshot(path=shot)
        logger.info("Screenshot saved to %s", shot)

        return solis_production, solis_production, shot