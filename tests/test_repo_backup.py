"""Tests for repository ZIP backup helpers."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from repomanager.services.github_client import GitHubClientError
from repomanager.services.repo_backup import (
    backup_repository_to_zip,
    default_backup_filename,
)


def test_default_backup_filename() -> None:
    name = default_backup_filename("alice", "my-repo")
    assert name.startswith("alice-my-repo-backup-")
    assert name.endswith(".zip")


@patch("repomanager.services.repo_backup._git_available", return_value=False)
@patch("repomanager.services.repo_backup.Github")
def test_backup_metadata_only(mock_github_cls: MagicMock, _git: MagicMock, tmp_path: Path) -> None:
    gh = mock_github_cls.return_value
    repo = MagicMock()
    repo.full_name = "alice/demo"
    repo.description = "desc"
    repo.private = False
    repo.archived = False
    repo.html_url = "https://github.com/alice/demo"
    repo.default_branch = "main"
    repo.clone_url = "https://github.com/alice/demo.git"
    repo.created_at = None
    repo.updated_at = None
    repo.has_pages = False
    repo.fork = False

    ms = SimpleNamespace(
        number=1,
        title="M1",
        description="first",
        state="open",
        open_issues=1,
        closed_issues=0,
        due_on=None,
        created_at=None,
        updated_at=None,
        closed_at=None,
    )
    issue = SimpleNamespace(
        number=7,
        title="Bug",
        body="details",
        state="open",
        pull_request=None,
        user=SimpleNamespace(login="alice"),
        labels=[SimpleNamespace(name="bug")],
        milestone=ms,
        assignees=[],
        created_at=None,
        updated_at=None,
        closed_at=None,
        html_url="https://github.com/alice/demo/issues/7",
        comments=0,
    )
    repo.get_milestones.return_value = [ms]
    repo.get_issues.return_value = [issue]
    gh.get_repo.return_value = repo

    zip_path = tmp_path / "demo.zip"
    stats = backup_repository_to_zip("token", "alice", "demo", zip_path)

    assert zip_path.is_file()
    assert stats["has_mirror"] is False
    assert stats["milestones"] == 1
    assert stats["issues"] == 1

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        assert any(n.endswith("metadata/issues.json") for n in names)
        assert any(n.endswith("metadata/milestones.json") for n in names)
        assert any(n.endswith("NO_GIT_MIRROR.txt") for n in names)
        issues = json.loads(
            zf.read(next(n for n in names if n.endswith("issues.json"))).decode("utf-8")
        )
        assert issues[0]["number"] == 7
        assert issues[0]["milestone"] == "M1"


@patch("repomanager.services.repo_backup._git_available", return_value=True)
@patch("repomanager.services.repo_backup._clone_mirror")
@patch("repomanager.services.repo_backup.Github")
def test_backup_with_mirror(
    mock_github_cls: MagicMock,
    mock_clone: MagicMock,
    _git: MagicMock,
    tmp_path: Path,
) -> None:
    gh = mock_github_cls.return_value
    repo = MagicMock()
    repo.full_name = "alice/demo"
    repo.description = ""
    repo.private = True
    repo.archived = False
    repo.html_url = "https://github.com/alice/demo"
    repo.default_branch = "main"
    repo.clone_url = "https://github.com/alice/demo.git"
    repo.created_at = None
    repo.updated_at = None
    repo.has_pages = False
    repo.fork = False
    repo.get_milestones.return_value = []
    repo.get_issues.return_value = []
    gh.get_repo.return_value = repo

    def _fake_clone(_token, _owner, _name, dest: Path, _progress) -> None:
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
        (dest / "config").write_text("[core]\n", encoding="utf-8")

    mock_clone.side_effect = _fake_clone

    zip_path = tmp_path / "with-git.zip"
    stats = backup_repository_to_zip("token", "alice", "demo", zip_path)
    assert stats["has_mirror"] is True
    with zipfile.ZipFile(zip_path) as zf:
        assert any("repository.git/HEAD" in n for n in zf.namelist())


@patch("repomanager.services.repo_backup.Github")
def test_backup_maps_api_error(mock_github_cls: MagicMock, tmp_path: Path) -> None:
    from github import GithubException

    gh = mock_github_cls.return_value
    gh.get_repo.side_effect = GithubException(404, {"message": "Not Found"}, None)
    with pytest.raises(GitHubClientError):
        backup_repository_to_zip("token", "a", "b", tmp_path / "x.zip")
