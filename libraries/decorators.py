import functools
from datetime import datetime
from pathlib import Path

from libraries.logger import get_logger
from secrets_util import secret_or_env

logger = get_logger(__name__)


def screenshot_on_error(name: str):
    """Decorator for Playwright scraper methods with signature (self, page, ...).
    Takes a full-page screenshot into output/ on any unhandled exception, then re-raises.
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(self, page, *args, **kwargs):
            try:
                return fn(self, page, *args, **kwargs)
            except Exception:
                out = Path(secret_or_env("ROBOT_ARTIFACTS", "output"))
                out.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                error_shot = out / f"{name}_error_{timestamp}.png"
                page.screenshot(path=error_shot, full_page=True)
                logger.error("%s scraper failed — error screenshot saved to %s", name, error_shot)
                raise
        return wrapper
    return decorator
