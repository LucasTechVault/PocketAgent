"""Exercise the installed console script from outside the repository."""

import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest

from pocketagent import __version__


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    script_name = "pocketagent.exe" if sys.platform == "win32" else "pocketagent"
    script = Path(sysconfig.get_path("scripts")) / script_name
    return subprocess.run(
        [str(script), *args],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("--help", "Usage:"),
        ("version", __version__),
        ("doctor", "Status:        READY"),
    ],
)
def test_installed_cli(command: str, expected: str) -> None:
    result = run_cli(command)

    assert result.returncode == 0, result.stderr
    assert expected in result.stdout


def test_doctor_uses_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POCKETAGENT_ENV", "testing")
    monkeypatch.setenv("POCKETAGENT_LOG_LEVEL", "DEBUG")

    result = run_cli("doctor")

    assert result.returncode == 0, result.stderr
    assert "Configuration: OK (testing)" in result.stdout
    assert "DEBUG pocketagent.cli:" in result.stderr


def test_invalid_configuration_fails_cleanly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POCKETAGENT_LOG_LEVEL", "unknown")

    result = run_cli("doctor")

    assert result.returncode == 2
    assert "Invalid configuration:" in result.stderr
    assert "READY" not in result.stdout
    assert "Traceback" not in result.stderr
