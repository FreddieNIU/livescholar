"""功能：编排搜索、元数据补全、筛选排序和报告生成的完整执行流程。"""

from __future__ import annotations

from pathlib import Path

from config.settings import Settings
from .models import Paper, SearchWindow
from .relevance import in_window, score_paper
from .report import render_report
from .sources import enrich_metadata, search_all


def run_pipeline(
    settings: Settings,
    window: SearchWindow,
    output_dir: str | Path = "reports",
) -> tuple[Path, str, list[Paper], list[str]]:
    raw_papers, search_log = search_all(settings, window)
    enriched = enrich_metadata(raw_papers, settings)

    screened: list[Paper] = []
    excluded = 0
    for paper in enriched:
        scored = score_paper(paper, settings.industry_affiliations)
        if in_window(scored, window) and scored.relevance_score >= settings.min_relevance_score:
            screened.append(scored)
        else:
            excluded += 1

    screened.sort(
        key=lambda paper: (bool(paper.industry_affiliations), paper.relevance_score, paper.updated_at or paper.published_at),
        reverse=True,
    )
    search_log.append(f"Screened {len(raw_papers)} unique candidates; excluded {excluded}.")
    report_path, body = render_report(screened, settings, window, search_log, output_dir)
    return report_path, body, screened, search_log
