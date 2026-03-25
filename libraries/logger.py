"""Shared logging setup for all tasks."""

import logging


def get_logger(name: str) -> logging.Logger:
    """Configure root logging (once) and return a named logger."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(name)
