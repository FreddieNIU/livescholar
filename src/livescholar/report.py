"""功能：把筛选后的论文列表渲染为 Markdown 文献报告。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from jinja2 import Template

from config.settings import Settings
from .models import Paper, SearchWindow


REPORT_TEMPLATE = Template(
    """# LiveScholar Literature Report

**Scope:** {{ settings.topic }}
**Window:** {{ window.start.strftime("%Y-%m-%d %H:%M %Z") }} to {{ window.end.strftime("%Y-%m-%d %H:%M %Z") }}
**Generated:** {{ generated_at.strftime("%Y-%m-%d %H:%M %Z") }}
**Included papers:** {{ papers|length }}

{% if industry_papers %}
## Industry-Affiliated Highlights

{% for paper in industry_papers %}
### {{ loop.index }}. {{ paper.title }}

- **Authors:** {{ paper.authors|join(", ") or "Unknown" }}
- **Source:** {{ paper.source }}{% if paper.venue %}, {{ paper.venue }}{% endif %}
- **Date:** {{ paper.display_date }}
- **Industry signal:** {{ paper.industry_affiliations|join(", ") }}
- **Why included:** {{ paper.relevance_reasons|join("; ") }}
- **Link:** {{ paper.url }}

{{ paper.abstract|truncate(700) }}

{% endfor %}
{% endif %}

## All Included Papers

| Title | Source | Date | Industry | Score |
|---|---:|---:|---:|---:|
{% for paper in papers -%}
| [{{ paper.title }}]({{ paper.url }}) | {{ paper.source }} | {{ paper.display_date }} | {{ paper.industry_affiliations|join(", ") or "-" }} | {{ paper.relevance_score }} |
{% endfor %}

{% for paper in papers %}
## {{ paper.title }}

- **Authors:** {{ paper.authors|join(", ") or "Unknown" }}
- **Venue/source:** {{ paper.venue or paper.source }}
- **URL:** {{ paper.url }}
- **DOI/arXiv:** {{ paper.doi or paper.arxiv_id or "-" }}
- **Relevance:** {{ paper.relevance_reasons|join("; ") }}
- **Affiliations found:** {{ paper.affiliations|join("; ") or "Not verified" }}

### Summary

{{ paper.abstract|truncate(1000) if paper.abstract else "No abstract was available from the checked metadata sources." }}

{% if paper.notes %}
### Notes

{{ paper.notes|join(" ") }}
{% endif %}

{% endfor %}

## Search Log

{% for item in search_log %}
- {{ item }}
{% endfor %}
"""
)


def render_report(
    papers: list[Paper],
    settings: Settings,
    window: SearchWindow,
    search_log: list[str],
    output_dir: str | Path = "reports",
) -> tuple[Path, str]:
    generated_at = datetime.now(window.end.tzinfo)
    industry_papers = [paper for paper in papers if paper.industry_affiliations]
    body = REPORT_TEMPLATE.render(
        papers=papers,
        industry_papers=industry_papers,
        settings=settings,
        window=window,
        generated_at=generated_at,
        search_log=search_log,
    )
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"livescholar-{window.end.strftime('%Y-%m-%d')}.md"
    path.write_text(body, encoding="utf-8")
    return path, body
