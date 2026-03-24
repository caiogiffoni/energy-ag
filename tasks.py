"""Robocorp tasks using Playwright via `robocorp.browser`."""

import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import expect
from robocorp import browser
from robocorp.tasks import task

from email_util import send_email_with_image


@task
def browser_demo() -> None:
    """Open Chromium, visit a page, assert the title — minimal Playwright smoke task."""
    load_dotenv()
    browser.configure(
        browser_engine="chromium",
        screenshot="only-on-failure",
        headless=False,
    )
    page = browser.goto(os.getenv("FUSION_URL"))
    page.get_by_role("textbox", name="Username or email").fill(os.getenv("FUSION_LOGIN"))
    page.get_by_role("textbox", name="Password").fill(os.getenv("FUSION_PASSWORD"))
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

    to_addr = os.environ.get("EMAIL_TO")
    if to_addr:
        send_email_with_image(
            to_addr=to_addr,
            subject=f"WEG production: {weg_production} kWh",
            body=(
                f"WEG production (kWh): {weg_production}\n"
                f"Raw title attribute: {weg_title!r}\n"
                f"Screenshot: {shot.name} (attached)\n"
            ),
            image_path=shot,
        )

browser_demo()