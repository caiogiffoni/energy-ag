import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import expect, sync_playwright

from email_util import send_email_with_image
from libraries.logger import get_logger
from secrets_util import secret_or_env

logger = get_logger(__name__)


class Process:
    """Open Chromium, visit a page, assert the title — minimal Playwright smoke task."""
    def __init__(self, playwright):
        self.playwright = playwright
        self.browser = None
        self.url = secret_or_env("FUSION_URL")
        self.login = secret_or_env("FUSION_LOGIN")
        self.password = secret_or_env("FUSION_PASSWORD")
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
        
        url = secret_or_env("FUSION_URL")
        logger.info("Navigating to %s", url)
        page.goto(url, wait_until="domcontentloaded")

        logger.info("Logging in")
        page.get_by_role("textbox", name="Username or email").fill(secret_or_env("FUSION_LOGIN") or "")
        page.get_by_role("textbox", name="Password").fill(secret_or_env("FUSION_PASSWORD") or "")
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

        out = Path(os.environ.get("ROBOT_ARTIFACTS", "output"))
        out.mkdir(parents=True, exist_ok=True)
        shot = out / "weg_energy_data.png"
        col.screenshot(path=shot)
        logger.info("Screenshot saved to %s", shot)

        to_addr = secret_or_env("EMAIL_TO")
        if to_addr:
            smtp_user = secret_or_env("SMTP_USER")
            smtp_password = secret_or_env("SMTP_PASSWORD")
            if smtp_user and smtp_password:
                logger.info("Sending email to %s", to_addr)
                send_email_with_image(
                    to_addr=to_addr,
                    subject=f"WEG production: {weg_production} kWh",
                    body=(
                        f"WEG production (kWh): {weg_production}\n"
                        f"Raw title attribute: {weg_title!r}\n"
                        f"Screenshot: {shot.name} (attached)\n"
                    ),
                    image_path=shot,
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
    load_dotenv()
    with sync_playwright() as p:
        process = Process(p)
        process.start()
