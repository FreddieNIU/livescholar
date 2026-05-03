from __future__ import annotations

import re

from .models import Paper, SearchWindow

RECOMMENDER_TERMS = (
    "recommender",
    "recommendation",
    "recommendations",
    "collaborative filtering",
    "retrieval",
    "ranking",
)

SEMANTIC_ID_TERMS = (
    "semantic id",
    "semantic ids",
    "semantic identifier",
    "semantic identifiers",
    "semantic token",
    "semantic tokens",
    "semantic code",
    "semantic codes",
    "id generation",
    "generative retrieval",
)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()


def score_paper(paper: Paper, industry_names: list[str]) -> Paper:
    haystack = normalize_text(f"{paper.title} {paper.abstract}")
    reasons: list[str] = []
    score = 0

    semantic_hits = [term for term in SEMANTIC_ID_TERMS if term in haystack]
    recommender_hits = [term for term in RECOMMENDER_TERMS if term in haystack]

    if semantic_hits:
        score += 2
        reasons.append(f"semantic-ID terms: {', '.join(sorted(set(semantic_hits)))}")
    if recommender_hits:
        score += 2
        reasons.append(f"recommendation terms: {', '.join(sorted(set(recommender_hits)))}")
    if "generative retrieval" in haystack:
        score += 1
        reasons.append("mentions generative retrieval")

    industry_hits = detect_industry_affiliations(paper.affiliations, industry_names)
    if industry_hits:
        paper.industry_affiliations = industry_hits
        score += 1
        reasons.append(f"industry affiliation: {', '.join(industry_hits)}")

    paper.relevance_score = score
    paper.relevance_reasons = reasons
    return paper


def in_window(paper: Paper, window: SearchWindow) -> bool:
    candidates = [dt for dt in (paper.updated_at, paper.published_at) if dt is not None]
    return bool(candidates) and any(window.start <= dt.astimezone(window.start.tzinfo) <= window.end for dt in candidates)


def detect_industry_affiliations(affiliations: list[str], industry_names: list[str]) -> list[str]:
    hits: list[str] = []
    lowered_affiliations = [aff.casefold() for aff in affiliations]
    for name in industry_names:
        needle = name.casefold()
        if any(needle in aff for aff in lowered_affiliations):
            hits.append(name)
    return sorted(set(hits))

