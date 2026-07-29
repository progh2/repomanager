"""Unit tests for Repository model."""

from datetime import datetime, timezone

from repomanager.models.repository import Repository


def test_full_name_and_visibility() -> None:
    repo = Repository(
        owner="alice",
        name="demo",
        private=True,
        description="A short demo",
        html_url="https://github.com/alice/demo",
        archived=False,
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    assert repo.full_name == "alice/demo"
    assert repo.visibility == "Private"
    assert repo.short_description == "A short demo"


def test_short_description_truncates() -> None:
    long_desc = "x" * 100
    repo = Repository(
        owner="a",
        name="b",
        private=False,
        description=long_desc,
        html_url="https://github.com/a/b",
        archived=False,
        updated_at=None,
    )
    assert repo.visibility == "Public"
    assert repo.short_description.endswith("...")
    assert len(repo.short_description) == 80


def test_empty_description() -> None:
    repo = Repository(
        owner="a",
        name="b",
        private=False,
        description="",
        html_url="https://github.com/a/b",
        archived=True,
        updated_at=None,
    )
    assert repo.short_description == "(설명 없음)"
