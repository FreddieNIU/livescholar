"""功能：定义 LiveScholar 的配置数据模型，并从 YAML 文件加载运行配置。"""

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
