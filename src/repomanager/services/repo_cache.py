"""Local cache of the last loaded repository list for instant startup."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QStandardPaths

from repomanager.models.repository import Repository

CACHE_VERSION = 1


@dataclass(frozen=True)
class CachedList:
    repositories: list[Repository]
    login: str
    saved_at: datetime


def _cache_path() -> Path:
    base = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppDataLocation
    )
    return Path(base) / "repo_cache.json"


def _dt_to_str(value: datetime | None) -> str:
    return value.isoformat() if value else ""


def _dt_from_str(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def save_cache(repositories: list[Repository], login: str) -> None:
    payload = {
        "version": CACHE_VERSION,
        "login": login,
        "saved_at": datetime.now().astimezone().isoformat(),
        "repositories": [
            {
                "owner": repo.owner,
                "name": repo.name,
                "description": repo.description,
                "private": repo.private,
                "html_url": repo.html_url,
                "archived": repo.archived,
                "created_at": _dt_to_str(repo.created_at),
                "updated_at": _dt_to_str(repo.updated_at),
                "has_pages": repo.has_pages,
                "pages_url": repo.pages_url,
                "fork": repo.fork,
            }
            for repo in repositories
        ],
    }
    path = _cache_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass  # cache is best-effort


def load_cache() -> CachedList | None:
    path = _cache_path()
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if payload.get("version") != CACHE_VERSION:
        return None
    saved_at = _dt_from_str(str(payload.get("saved_at", "")))
    if saved_at is None:
        return None
    try:
        repositories = [
            Repository(
                owner=item["owner"],
                name=item["name"],
                description=item.get("description", ""),
                private=bool(item.get("private", False)),
                html_url=item.get("html_url", ""),
                archived=bool(item.get("archived", False)),
                created_at=_dt_from_str(item.get("created_at", "")),
                updated_at=_dt_from_str(item.get("updated_at", "")),
                has_pages=bool(item.get("has_pages", False)),
                pages_url=item.get("pages_url", ""),
                fork=bool(item.get("fork", False)),
            )
            for item in payload.get("repositories", [])
        ]
    except (KeyError, TypeError):
        return None
    return CachedList(
        repositories=repositories,
        login=str(payload.get("login", "")),
        saved_at=saved_at,
    )
