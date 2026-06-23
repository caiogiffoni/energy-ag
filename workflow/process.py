import subprocess
import sys

from libraries.logger import get_logger
from utils.email_util import send_email_with_image
from utils.secrets_util import secret_or_env
from utils.utils import send_generated_energy_email
from workflow.growatt import Growatt
from workflow.saj import Saj
from workflow.solis import Solis
from workflow.weg import Weg

logger = get_logger(__name__)


class Process:
    """Open Chromium, visit a page, assert the title — minimal Playwright smoke task."""
    def __init__(self, playwright):
        self.playwright = playwright
        self.browser = None
        self.email_to = secret_or_env("EMAIL_TO")
        self.email_from = secret_or_env("EMAIL_FROM")

    def start(self):
        logger.info("Installing Playwright Chromium browser")
        subprocess.run(
            ["playwright", "install", "chromium"],
            check=True
        )
        self.browser = self.playwright.chromium.launch()
        page = self.browser.new_page()
        
        weg = Weg()
        weg_info = weg.get_production(page)

        saj = Saj()
        saj_info = saj.get_production(page)

        solis = Solis()
        solis_info = solis.get_production(page)

        growatt = Growatt()
        growatt_info = growatt.get_production()

        send_generated_energy_email(weg_info, saj_info, solis_info, growatt_info)


if __name__ == "__main__":
    from dotenv import load_dotenv
    from playwright.sync_api import expect, sync_playwright
    load_dotenv()
    with sync_playwright() as p:
        process = Process(p)
        process.start()
