"""Verify configuration sources and validation."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from pocketagent.config import Settings


def test_defaults() -> None:
    settings = Settings()

    assert settings.env == "development"
    assert settings.log_level == "INFO"


def test_environment_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POCKETAGENT_ENV", "testing")
    monkeypatch.setenv("POCKETAGENT_LOG_LEVEL", "DEBUG")

    settings = Settings()

    assert settings.env == "testing"
    assert settings.log_level == "DEBUG"


def test_dotenv_and_environment_precedence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / ".env").write_text(
        "POCKETAGENT_ENV=local\nPOCKETAGENT_LOG_LEVEL=WARNING\nOTHER_VARIABLE=value\n",
        encoding="utf-8",
    )
    assert Settings().env == "local"
    assert Settings().log_level == "WARNING"

    monkeypatch.setenv("POCKETAGENT_ENV", "testing")
    assert Settings().env == "testing"


def test_log_level_is_case_insensitive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POCKETAGENT_LOG_LEVEL", "debug")

    assert Settings().log_level == "DEBUG"


@pytest.mark.parametrize(
    ("name", "value"),
    [("POCKETAGENT_LOG_LEVEL", "unknown"), ("POCKETAGENT_ENV", "")],
)
def test_invalid_configuration(
    name: str, value: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(ValidationError):
        Settings()
