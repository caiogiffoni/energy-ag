import subprocess
import sys

from email_util import send_email_with_image
from libraries.logger import get_logger
from secrets_util import secret_or_env
from workflow.saj import Saj
from workflow.weg import Weg
from workflow.growatt import Growatt
from workflow.solis import Solis
logger = get_logger(__name__)


class Process:
    """Open Chromium, visit a page, assert the title — minimal Playwright smoke task."""
    def __init__(self, playwright):
        self.playwright = playwright
        self.browser = None
        self.email_to = secret_or_env("EMAIL_TO")
        self.email_from = secret_or_env("EMAIL_FROM")
        self.playwright = playwright

    def start(self):
        logger.info("Installing Playwright Chromium browser")
        subprocess.run(
            ["playwright", "install", "chromium"],
            check=True
        )
        self.browser = self.playwright.chromium.launch()
        page = self.browser.new_page()
        
        weg = Weg()
        weg_production, weg_title, weg_shot = weg.get_production(page)

        saj = Saj()
        saj_production, saj_title, saj_shot = saj.get_production(page)

        solis = Solis()
        solis_production, solis_title, solis_shot = solis.get_production(page)

        growatt = Growatt()
        growatt_production, growatt_title, growatt_shot = growatt.get_production()

        to_addr = secret_or_env("EMAIL_TO")
        if to_addr:
            smtp_user = secret_or_env("SMTP_USER")
            smtp_password = secret_or_env("SMTP_PASSWORD")
            if smtp_user and smtp_password:
                logger.info("Sending email to %s", to_addr)
                inversor2 = round(float(saj_production) + float(solis_production) + float(growatt_production), 2)
                send_email_with_image(
                    to_addr=to_addr,
                    subject=f"Weg: {weg_production} kWh, II: {inversor2} kWh",
                    body=(
                        f"WEG production (kWh): {weg_production}\n"
                        f"Saj production (kWh): {saj_production}\n"
                        f"Solis production (kWh): {solis_production}\n"
                        f"Growatt production (kWh): {growatt_production}\n"
                        f"Screenshot: {weg_shot.name} (attached)\n"
                        f"Screenshot: {saj_shot.name} (attached)\n"
                        f"Screenshot: {solis_shot.name} (attached)\n"
                    ),
                    image_path=[weg_shot, saj_shot, solis_shot],
                    smtp_host=secret_or_env("SMTP_HOST"),
                    smtp_port=int(secret_or_env("SMTP_PORT") or "587"),
                    smtp_user=smtp_user,
                    smtp_password=smtp_password,
                    from_addr=secret_or_env("EMAIL_FROM") or smtp_user,
                )
                logger.info("Email sent")
            else:
                logger.warning("SMTP credentials missing — email skipped")
        else:
            logger.info("EMAIL_TO not set — email skipped")



if __name__ == "__main__":
    from playwright.sync_api import expect, sync_playwright
    from dotenv import load_dotenv
    load_dotenv()
    with sync_playwright() as p:
        process = Process(p)
        process.start()
