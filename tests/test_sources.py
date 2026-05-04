"""功能：验证论文候选去重逻辑优先使用 DOI/arXiv 等稳定标识。"""

from datetime import UTC, datetime

import requests

from config.settings import Settings
from livescholar.models import Paper
from livescholar.models import SearchWindow
from livescholar.sources import dedupe_papers, search_arxiv


def test_dedupe_prefers_stable_identifiers() -> None:
    papers = [
        Paper(title="A Semantic ID Paper", authors=[], source="arXiv", url="a", arxiv_id="2601.00001"),
        Paper(title="A Semantic ID Paper", authors=[], source="Scholar", url="b", arxiv_id="2601.00001"),
        Paper(title="Another Paper", authors=[], source="Scholar", url="c"),
    ]

    assert [paper.url for paper in dedupe_papers(papers)] == ["a", "c"]


def test_arxiv_search_retries_transient_request_failures(monkeypatch) -> None:
    attempts = 0

    class Response:
        text = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <id>https://arxiv.org/abs/2601.00001</id>
            <title>A Semantic ID Paper</title>
            <summary>Recommendation with semantic IDs.</summary>
            <published>2026-05-04T07:00:00Z</published>
            <updated>2026-05-04T07:00:00Z</updated>
          </entry>
        </feed>
        """

        def raise_for_status(self) -> None:
            return None

    def fake_get(url: str, timeout: int) -> Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise requests.ConnectionError("temporary DNS failure")
        return Response()

    monkeypatch.setattr("livescholar.sources.requests.get", fake_get)
    monkeypatch.setattr("livescholar.sources.time.sleep", lambda seconds: None)

    settings = Settings(queries=["semantic ID recommender"], max_results_per_source=50)
    window = SearchWindow(
        start=datetime(2026, 5, 3, 7, tzinfo=UTC),
        end=datetime(2026, 5, 4, 7, tzinfo=UTC),
        timezone="Europe/Dublin",
    )

    papers, logs = search_arxiv(settings, window)

    assert attempts == 2
    assert [paper.arxiv_id for paper in papers] == ["2601.00001"]
    assert any("retrying" in log for log in logs)
