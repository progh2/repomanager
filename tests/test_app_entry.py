"""Tests for the app entry point flags used by packaging smoke tests."""

from __future__ import annotations

from repomanager import __version__
from repomanager.app import run


def test_version_flag_exits_cleanly(capsys) -> None:
    assert run(["repomanager", "--version"]) == 0
    assert __version__ in capsys.readouterr().out
