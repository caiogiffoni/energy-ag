"""Robocorp tasks using Playwright via `robocorp.browser`."""

from pathlib import Path

from dotenv import load_dotenv
from robocorp.tasks import task
from libraries.logger import get_logger
from playwright.sync_api import sync_playwright
from workflow.process import Process

logger = get_logger(__name__)


@task
def energy_production() -> None:
    load_dotenv()
    with sync_playwright() as p:
        process = Process(p)
        process.start()