"""功能：定义文献检索窗口和论文记录等核心数据结构。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class SearchWindow:
    start: datetime
    end: datetime
    timezone: str


@dataclass
class Paper:
    title: str
    authors: list[str]
    source: str
    url: str
    published_at: datetime | None = None
    updated_at: datetime | None = None
    abstract: str = ""
    doi: str = ""
    arxiv_id: str = ""
    venue: str = ""
    affiliations: list[str] = field(default_factory=list)
    industry_affiliations: list[str] = field(default_factory=list)
    relevance_score: int = 0
    relevance_reasons: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def display_date(self) -> str:
        dt = self.updated_at or self.published_at
        return dt.strftime("%Y-%m-%d %H:%M %Z") if dt else "unknown"
