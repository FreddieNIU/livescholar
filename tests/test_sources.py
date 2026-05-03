"""功能：验证论文候选去重逻辑优先使用 DOI/arXiv 等稳定标识。"""

from livescholar.models import Paper
from livescholar.sources import dedupe_papers


def test_dedupe_prefers_stable_identifiers() -> None:
    papers = [
        Paper(title="A Semantic ID Paper", authors=[], source="arXiv", url="a", arxiv_id="2601.00001"),
        Paper(title="A Semantic ID Paper", authors=[], source="Scholar", url="b", arxiv_id="2601.00001"),
        Paper(title="Another Paper", authors=[], source="Scholar", url="c"),
    ]

    assert [paper.url for paper in dedupe_papers(papers)] == ["a", "c"]
