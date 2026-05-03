"""功能：把每次执行的检索日志和结果摘要写入 logs 目录，便于追踪历史运行。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from livescholar.models import Paper, SearchWindow


def write_run_log(
    search_log: list[str],
    papers: list[Paper],
    window: SearchWindow,
    log_dir: str | Path = "logs",
) -> Path:
    out_dir = Path(log_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(window.end.tzinfo)
    path = out_dir / f"run-{generated_at.strftime('%Y%m%d-%H%M%S')}.log"
    lines = [
        "LiveScholar run log",
        f"Window: {window.start.strftime('%Y-%m-%d %H:%M %Z')} to {window.end.strftime('%Y-%m-%d %H:%M %Z')}",
        f"Generated: {generated_at.strftime('%Y-%m-%d %H:%M %Z')}",
        f"Included papers: {len(papers)}",
        "",
        "Search log:",
        *[f"- {item}" for item in search_log],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path

