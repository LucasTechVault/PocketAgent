"""Verify imports resolve through the installed package."""

from importlib.metadata import version

import pocketagent


def test_installed_package_version() -> None:
    assert pocketagent.__version__ == version("pocketagent")
