from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class Settings(BaseModel):
    timezone: str = "Europe/Dublin"
    topic: str = "recommender systems semantic ID"
    max_results_per_source: int = 50
    min_relevance_score: int = 3
    queries: list[str] = Field(default_factory=list)
    industry_affiliations: list[str] = Field(default_factory=list)


def load_settings(path: str | Path) -> Settings:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return Settings.model_validate(data)

