"""Repository data model."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Repository:
    owner: str
    name: str
    private: bool
    description: str
    html_url: str
    archived: bool
    created_at: datetime | None
    updated_at: datetime | None
    has_pages: bool
    pages_url: str
    fork: bool = False

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"

    @property
    def short_description(self) -> str:
        from repomanager.i18n import tr

        text = (self.description or "").strip()
        if not text:
            return tr("list.no_desc")
        if len(text) <= 80:
            return text
        return text[:77] + "..."

    def format_created(self) -> str:
        return self.created_at.strftime("%Y-%m-%d") if self.created_at else "-"

    def format_updated(self) -> str:
        return self.updated_at.strftime("%Y-%m-%d") if self.updated_at else "-"

    def with_updates(self, **kwargs: object) -> Repository:
        return replace(self, **kwargs)
