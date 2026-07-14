"""Robocorp tasks."""

from dotenv import load_dotenv
from robocorp.tasks import task

from libraries.logger import get_logger
from workflow.process import Process

logger = get_logger(__name__)


@task
def energy_production() -> None:
    load_dotenv()
    Process().start()
