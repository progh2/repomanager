"""Tests for i18n helpers."""

from repomanager.i18n import resolve_language, set_language, tr


def test_tr_switches_language() -> None:
    set_language("en", notify=False)
    assert tr("btn.refresh") == "Refresh"
    set_language("ko", notify=False)
    assert tr("btn.refresh") == "새로고침"
    set_language("ja", notify=False)
    assert tr("btn.refresh") == "更新"


def test_resolve_unsupported_falls_back() -> None:
    assert resolve_language("fr") == "en"
    assert resolve_language("ko") == "ko"
