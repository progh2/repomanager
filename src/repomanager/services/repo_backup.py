"""Backup a GitHub repository: git mirror + issues/milestones metadata as ZIP."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import zipfile
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from github import Auth, Github, GithubException

from repomanager.services.github_client import GitHubClientError

ProgressCb = Callable[[str], None]


def _safe_name(value: str) -> str:
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in value)


def _git_available() -> bool:
    try:
        completed = subprocess.run(
            ["git", "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return completed.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def _clone_mirror(token: str, owner: str, name: str, dest: Path, progress: ProgressCb) -> None:
    """Clone a bare mirror (all branches, tags, refs) into dest."""
    progress(f"git clone --mirror {owner}/{name}")
    # x-access-token works for both classic and fine-grained PATs
    url = f"https://x-access-token:{token}@github.com/{owner}/{name}.git"
    completed = subprocess.run(
        [
            "git",
            "clone",
            "--mirror",
            "--progress",
            url,
            str(dest),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=600,
    )
    if completed.returncode != 0:
        err = (completed.stderr or completed.stdout or "git clone failed").strip()
        # Scrub token if it leaked into error output
        err = err.replace(token, "***")
        raise GitHubClientError(f"git mirror clone failed: {err[:500]}")


def _export_metadata(
    token: str,
    owner: str,
    name: str,
    meta_dir: Path,
    progress: ProgressCb,
) -> dict:
    progress(f"Exporting issues & milestones for {owner}/{name}")
    gh = Github(auth=Auth.Token(token), per_page=100)
    try:
        repo = gh.get_repo(f"{owner}/{name}")
    except GithubException as exc:
        raise GitHubClientError(
            f"Could not open {owner}/{name} for metadata export (HTTP {exc.status}).",
            status=exc.status,
        ) from exc

    repo_info = {
        "full_name": repo.full_name,
        "description": repo.description or "",
        "private": bool(repo.private),
        "archived": bool(repo.archived),
        "html_url": repo.html_url,
        "default_branch": repo.default_branch,
        "clone_url": repo.clone_url,
        "created_at": repo.created_at.isoformat() if repo.created_at else None,
        "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
        "has_pages": bool(getattr(repo, "has_pages", False)),
        "fork": bool(getattr(repo, "fork", False)),
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }
    (meta_dir / "repository.json").write_text(
        json.dumps(repo_info, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    milestones = []
    try:
        for ms in repo.get_milestones(state="all"):
            milestones.append(
                {
                    "number": ms.number,
                    "title": ms.title,
                    "description": ms.description or "",
                    "state": ms.state,
                    "open_issues": ms.open_issues,
                    "closed_issues": ms.closed_issues,
                    "due_on": ms.due_on.isoformat() if ms.due_on else None,
                    "created_at": ms.created_at.isoformat() if ms.created_at else None,
                    "updated_at": ms.updated_at.isoformat() if ms.updated_at else None,
                    "closed_at": ms.closed_at.isoformat() if ms.closed_at else None,
                }
            )
    except GithubException as exc:
        raise GitHubClientError(
            f"Failed to export milestones (HTTP {exc.status}).",
            status=exc.status,
        ) from exc
    (meta_dir / "milestones.json").write_text(
        json.dumps(milestones, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    issues = []
    try:
        # include pull requests as GitHub issues API returns both; mark them
        for issue in repo.get_issues(state="all"):
            is_pr = issue.pull_request is not None
            issues.append(
                {
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body or "",
                    "state": issue.state,
                    "is_pull_request": is_pr,
                    "user": issue.user.login if issue.user else None,
                    "labels": [label.name for label in issue.labels],
                    "milestone": issue.milestone.title if issue.milestone else None,
                    "assignees": [a.login for a in issue.assignees],
                    "created_at": issue.created_at.isoformat() if issue.created_at else None,
                    "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                    "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                    "html_url": issue.html_url,
                    "comments": issue.comments,
                }
            )
    except GithubException as exc:
        raise GitHubClientError(
            f"Failed to export issues (HTTP {exc.status}).",
            status=exc.status,
        ) from exc
    (meta_dir / "issues.json").write_text(
        json.dumps(issues, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    readme = (
        f"# Backup of {repo.full_name}\n\n"
        f"Exported at: {repo_info['exported_at']}\n\n"
        "## Contents\n\n"
        "- `repository.git/` — bare git mirror (all branches, tags, refs). "
        "Restore with: `git clone repository.git restored-folder`\n"
        "- `metadata/repository.json` — repository info\n"
        f"- `metadata/milestones.json` — {len(milestones)} milestones\n"
        f"- `metadata/issues.json` — {len(issues)} issues/PRs\n"
    )
    if not _git_available():
        readme += (
            "\n> Note: git was not available at backup time; "
            "only metadata may be present.\n"
        )
    (meta_dir / "README.md").write_text(readme, encoding="utf-8")

    return {
        "milestones": len(milestones),
        "issues": len(issues),
        "has_mirror": False,
    }


def _zip_directory(source_dir: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in source_dir.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(source_dir).as_posix())


def backup_repository_to_zip(
    token: str,
    owner: str,
    name: str,
    zip_path: Path,
    *,
    progress: ProgressCb | None = None,
) -> dict:
    """
    Create a ZIP backup containing:
    - repository.git/  (git mirror with all branches/tags) when git is available
    - metadata/        (repository.json, issues.json, milestones.json, README.md)
    """
    progress = progress or (lambda _msg: None)
    zip_path = Path(zip_path)
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="repomanager-backup-") as tmp:
        root = Path(tmp) / f"{_safe_name(owner)}-{_safe_name(name)}"
        root.mkdir(parents=True, exist_ok=True)
        meta_dir = root / "metadata"
        meta_dir.mkdir()

        stats = _export_metadata(token, owner, name, meta_dir, progress)
        # Copy README to backup root for convenience
        shutil.copy2(meta_dir / "README.md", root / "README.md")

        if _git_available():
            mirror_dir = root / "repository.git"
            _clone_mirror(token, owner, name, mirror_dir, progress)
            stats["has_mirror"] = True
        else:
            progress("git not found — metadata-only backup")
            stats["has_mirror"] = False
            (root / "NO_GIT_MIRROR.txt").write_text(
                "Git was not found on PATH. Install Git to include all branches "
                "in future backups. This ZIP contains issues/milestones metadata only.\n",
                encoding="utf-8",
            )

        progress(f"Writing ZIP: {zip_path.name}")
        _zip_directory(root, zip_path)

    return stats


def default_backup_filename(owner: str, name: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{_safe_name(owner)}-{_safe_name(name)}-backup-{stamp}.zip"
