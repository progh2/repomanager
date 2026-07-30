"""Tests for the local repository list cache."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

from repomanager.models.repository import Repository
from repomanager.services import repo_cache


def _repo(name: str) -> Repository:
    return Repository(
        owner="octo",
        name=name,
        description="설명 with unicode",
        private=True,
        html_url=f"https://github.com/octo/{name}",
        archived=False,
        created_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
        updated_at=datetime(2025, 3, 4, tzinfo=timezone.utc),
        has_pages=True,
        pages_url=f"https://octo.github.io/{name}/",
        fork=True,
    )


def test_cache_round_trip(tmp_path) -> None:
    path = tmp_path / "cache.json"
    with patch.object(repo_cache, "_cache_path", return_value=path):
        repo_cache.save_cache([_repo("a"), _repo("b")], login="octo")
        cached = repo_cache.load_cache()
    assert cached is not None
    assert cached.login == "octo"
    assert [r.name for r in cached.repositories] == ["a", "b"]
    first = cached.repositories[0]
    assert first.private and first.fork and first.has_pages
    assert first.created_at is not None and first.created_at.year == 2024
    assert first.description == "설명 with unicode"


def test_load_cache_missing(tmp_path) -> None:
    with patch.object(repo_cache, "_cache_path", return_value=tmp_path / "none.json"):
        assert repo_cache.load_cache() is None


def test_load_cache_corrupt(tmp_path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    with patch.object(repo_cache, "_cache_path", return_value=path):
        assert repo_cache.load_cache() is None
