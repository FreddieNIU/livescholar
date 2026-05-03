from datetime import UTC, datetime

from livescholar.models import Paper, SearchWindow
from livescholar.relevance import in_window, score_paper


def test_scores_semantic_id_recommender_paper_with_industry_affiliation() -> None:
    paper = Paper(
        title="Semantic IDs for Generative Retrieval in Recommendation",
        authors=["A. Researcher"],
        source="arXiv",
        url="https://arxiv.org/abs/2601.00001",
        abstract="We study semantic ID generation for recommender systems.",
        affiliations=["Google Research (company)"],
    )

    scored = score_paper(paper, ["Google"])

    assert scored.relevance_score >= 5
    assert scored.industry_affiliations == ["Google"]


def test_in_window_accepts_updated_or_published_date() -> None:
    window = SearchWindow(
        start=datetime(2026, 5, 2, 7, tzinfo=UTC),
        end=datetime(2026, 5, 3, 7, tzinfo=UTC),
        timezone="UTC",
    )
    paper = Paper(
        title="Paper",
        authors=[],
        source="arXiv",
        url="https://example.com",
        updated_at=datetime(2026, 5, 3, 6, 59, tzinfo=UTC),
    )

    assert in_window(paper, window)

