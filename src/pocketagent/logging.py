"""Minimal application logging setup."""

import logging


def configure_logging(log_level: str = "INFO") -> None:
    """Configure stderr logging once at application startup."""
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
