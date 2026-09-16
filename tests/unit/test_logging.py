"""Verify logging levels and the operational log format."""

import logging
import re

import pytest

from pocketagent.logging import configure_logging


def test_logging_format_and_level(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = logging.getLogger()
    monkeypatch.setattr(root, "handlers", [])
    monkeypatch.setattr(root, "level", logging.WARNING)

    configure_logging("INFO")
    logger = logging.getLogger("pocketagent.test")
    logger.debug("filtered message")
    logger.info("bootstrap ready")

    stderr = capsys.readouterr().err
    assert re.search(
        r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} "
        r"INFO pocketagent.test: bootstrap ready",
        stderr,
    )
    assert "filtered message" not in stderr
