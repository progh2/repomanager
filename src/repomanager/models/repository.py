"""Repository data model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Repository:
    owner: str
    name: str
    private: bool
    description: str
    html_url: str
    archived: bool
    updated_at: datetime | None

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"

    @property
    def visibility(self) -> str:
        return "Private" if self.private else "Public"

    @property
    def short_description(self) -> str:
        text = (self.description or "").strip()
        if not text:
            return "(설명 없음)"
        if len(text) <= 80:
            return text
        return text[:77] + "..."
