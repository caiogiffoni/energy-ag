"""Robocorp tasks using Playwright via `robocorp.browser`."""

import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import expect
from robocorp import browser
from robocorp.tasks import task

from email_util import send_email_with_image
from secrets_util import secret_or_env


@task
def energy_production() -> None:
    """Open Chromium, visit a page, assert the title — minimal Playwright smoke task."""
    load_dotenv()
    browser.configure(
        browser_engine="chromium",
        screenshot="only-on-failure",
        headless=True,
    )
    page = browser.goto(secret_or_env("FUSION_URL"), wait_until="domcontentloaded")
    page.get_by_role("textbox", name="Username or email").fill(secret_or_env("FUSION_LOGIN") or "")
    page.get_by_role("textbox", name="Password").fill(secret_or_env("FUSION_PASSWORD") or "")
    page.locator("#btn_outerverify").click()
    col = page.locator(".col-content.margin-right-075rem")
    expect(col).to_be_visible(timeout=60000)
    col.click()
    weg_title = page.locator(".nco-product-power-center").get_attribute("title")
    # e.g. title 'Yield 322.69 kWh'
    parts = (weg_title or "").split()
    weg_production = parts[1] if len(parts) > 1 else ""
    out = Path(os.environ.get("ROBOT_ARTIFACTS", "output"))
    out.mkdir(parents=True, exist_ok=True)
    shot = out / "weg_energy_data.png"
    col.screenshot(path=shot)

    to_addr = secret_or_env("EMAIL_TO")
    if to_addr:
        smtp_user = secret_or_env("SMTP_USER")
        smtp_password = secret_or_env("SMTP_PASSWORD")
        if smtp_user and smtp_password:
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