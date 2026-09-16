"""Keep developer configuration out of bootstrap smoke tests."""

import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    for name in tuple(os.environ):
        if name.upper().startswith("POCKETAGENT_"):
            monkeypatch.delenv(name)
