"""Robocorp tasks using Playwright via `robocorp.browser`."""

from robocorp import browser
from robocorp.tasks import task


@task
def browser_demo() -> None:
    """Open Chromium, visit a page, assert the title — minimal Playwright smoke task."""
    browser.configure(
        browser_engine="chromium",
        screenshot="only-on-failure",
        headless=True,
    )
    page = browser.goto("https://playwright.dev/")
    title = page.title()
    print("hi")
    assert "Playwright" in title, f"unexpected title: {title!r}"


browser_demo()