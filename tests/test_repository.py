"""Unit tests for Repository model."""

from datetime import datetime, timezone

from repomanager.models.repository import Repository


def _repo(**kwargs):
    defaults = dict(
        owner="alice",
        name="demo",
        private=True,
        description="A short demo",
        html_url="https://github.com/alice/demo",
        archived=False,
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        has_pages=False,
        pages_url="",
    )
    defaults.update(kwargs)
    return Repository(**defaults)


def test_full_name_and_visibility() -> None:
    repo = _repo()
    assert repo.full_name == "alice/demo"
    assert repo.visibility == "비공개"
    assert repo.short_description == "A short demo"
    assert repo.format_created() == "2025-01-01"
    assert repo.format_updated() == "2026-01-01"


def test_short_description_truncates() -> None:
    long_desc = "x" * 100
    repo = _repo(private=False, description=long_desc, updated_at=None, created_at=None)
    assert repo.visibility == "공개"
    assert repo.short_description.endswith("...")
    assert len(repo.short_description) == 80


def test_empty_description() -> None:
    repo = _repo(private=False, description="", archived=True, updated_at=None)
    assert repo.short_description == "(설명 없음)"


def test_with_updates() -> None:
    repo = _repo()
    updated = repo.with_updates(description="new", private=False)
    assert updated.description == "new"
    assert updated.private is False
    assert repo.description == "A short demo"
