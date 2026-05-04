"""功能：从 arXiv、Google Scholar 和元数据服务检索、补全、去重论文候选。"""

from __future__ import annotations

import os
import re
import time
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import feedparser
import requests
from dateutil import parser as date_parser

from config.settings import Settings
from .models import Paper, SearchWindow

HTTP_TIMEOUT = 30
HTTP_RETRIES = 3
HTTP_RETRY_BACKOFF_SECONDS = 2.0


def search_all(settings: Settings, window: SearchWindow) -> tuple[list[Paper], list[str]]:
    papers: list[Paper] = []
    log: list[str] = []

    arxiv_papers, arxiv_log = search_arxiv(settings, window)
    papers.extend(arxiv_papers)
    log.extend(arxiv_log)

    scholar_papers, scholar_log = search_google_scholar(settings, window)
    papers.extend(scholar_papers)
    log.extend(scholar_log)

    return dedupe_papers(papers), log


def search_arxiv(settings: Settings, window: SearchWindow) -> tuple[list[Paper], list[str]]:
    papers: list[Paper] = []
    logs: list[str] = []
    start = window.start.astimezone(UTC).strftime("%Y%m%d%H%M")
    end = window.end.astimezone(UTC).strftime("%Y%m%d%H%M")

    for query in settings.queries:
        arxiv_query = f'({query}) AND submittedDate:[{start} TO {end}]'
        url = (
            "https://export.arxiv.org/api/query"
            f"?search_query=all:{quote_plus(arxiv_query)}"
            f"&start=0&max_results={settings.max_results_per_source}"
            "&sortBy=submittedDate&sortOrder=descending"
        )
        logs.append(f"arXiv query: {arxiv_query}")
        try:
            feed = feedparser.parse(_get_text_with_retries(url, logs, source="arXiv", query=query))
        except requests.RequestException as exc:
            logs.append(f"arXiv request failed for {query!r}: {exc}")
            continue
        for entry in feed.entries:
            papers.append(_paper_from_arxiv_entry(entry))

    return papers, logs


def _get_text_with_retries(
    url: str,
    logs: list[str],
    *,
    source: str,
    query: str,
    attempts: int = HTTP_RETRIES,
    backoff_seconds: float = HTTP_RETRY_BACKOFF_SECONDS,
) -> str:
    last_exc: requests.RequestException | None = None
    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(url, timeout=HTTP_TIMEOUT)
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            last_exc = exc
            if attempt == attempts:
                break
            logs.append(
                f"{source} request attempt {attempt}/{attempts} failed for {query!r}; retrying: {exc}"
            )
            time.sleep(backoff_seconds * attempt)
    if last_exc is None:
        raise requests.RequestException(f"{source} request failed without an exception.")
    raise last_exc


def search_google_scholar(settings: Settings, window: SearchWindow) -> tuple[list[Paper], list[str]]:
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return [], ["Google Scholar skipped: SERPAPI_API_KEY is not configured."]

    papers: list[Paper] = []
    logs: list[str] = []
    for query in settings.queries:
        logs.append(f"Google Scholar query via SerpAPI: {query}")
        try:
            response = requests.get(
                "https://serpapi.com/search.json",
                params={
                    "engine": "google_scholar",
                    "q": query,
                    "as_ylo": window.start.year,
                    "num": min(settings.max_results_per_source, 20),
                    "api_key": api_key,
                },
                timeout=HTTP_TIMEOUT,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logs.append(f"Google Scholar request failed for {query!r}: {exc}")
            continue

        for item in response.json().get("organic_results", []):
            papers.append(_paper_from_scholar_item(item))

    return papers, logs


def enrich_metadata(papers: list[Paper], settings: Settings) -> list[Paper]:
    for paper in papers:
        _enrich_from_openalex(paper)
        _enrich_from_semantic_scholar(paper)
    return papers


def dedupe_papers(papers: list[Paper]) -> list[Paper]:
    seen: set[str] = set()
    unique: list[Paper] = []
    for paper in papers:
        key = paper.doi.casefold() or paper.arxiv_id.casefold() or normalize_title(paper.title)
        if key in seen:
            continue
        seen.add(key)
        unique.append(paper)
    return unique


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.casefold()).strip()


def _paper_from_arxiv_entry(entry: object) -> Paper:
    url = getattr(entry, "link", "")
    arxiv_id = url.rstrip("/").split("/")[-1]
    published = _parse_datetime(getattr(entry, "published", ""))
    updated = _parse_datetime(getattr(entry, "updated", ""))
    authors = [author.get("name", "") for author in getattr(entry, "authors", [])]
    doi = ""
    for link in getattr(entry, "links", []):
        if link.get("title") == "doi":
            doi = link.get("href", "").replace("http://dx.doi.org/", "").replace("https://doi.org/", "")
    return Paper(
        title=re.sub(r"\s+", " ", getattr(entry, "title", "")).strip(),
        authors=[author for author in authors if author],
        source="arXiv",
        url=url,
        published_at=published,
        updated_at=updated,
        abstract=re.sub(r"\s+", " ", getattr(entry, "summary", "")).strip(),
        doi=doi,
        arxiv_id=arxiv_id,
        venue="arXiv",
    )


def _paper_from_scholar_item(item: dict) -> Paper:
    publication_info = item.get("publication_info", {})
    authors = [author.get("name", "") for author in publication_info.get("authors", [])]
    year_match = re.search(r"\b(20\d{2}|19\d{2})\b", publication_info.get("summary", ""))
    published_at = datetime(int(year_match.group(1)), 1, 1, tzinfo=UTC) if year_match else None
    return Paper(
        title=item.get("title", ""),
        authors=[author for author in authors if author],
        source="Google Scholar",
        url=item.get("link", ""),
        published_at=published_at,
        abstract=item.get("snippet", ""),
        venue=publication_info.get("summary", ""),
        notes=["Discovered via Google Scholar; exact posting date must be verified from primary source."],
    )


def _enrich_from_openalex(paper: Paper) -> None:
    if not paper.title:
        return
    try:
        response = requests.get(
            "https://api.openalex.org/works",
            params={"search": paper.title, "per-page": 1},
            timeout=HTTP_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException:
        paper.notes.append("OpenAlex metadata lookup failed.")
        return

    results = response.json().get("results", [])
    if not results:
        return
    work = results[0]
    if not paper.published_at and work.get("publication_date"):
        paper.published_at = _parse_datetime(work["publication_date"])
    if not paper.doi and work.get("doi"):
        paper.doi = work["doi"].replace("https://doi.org/", "")
    if not paper.venue:
        paper.venue = (work.get("primary_location") or {}).get("source", {}).get("display_name") or ""
    affiliations = []
    for authorship in work.get("authorships", []):
        for institution in authorship.get("institutions", []):
            display_name = institution.get("display_name")
            inst_type = institution.get("type")
            if display_name:
                affiliations.append(f"{display_name} ({inst_type})" if inst_type else display_name)
    paper.affiliations = sorted(set([*paper.affiliations, *affiliations]))


def _enrich_from_semantic_scholar(paper: Paper) -> None:
    if not paper.title:
        return
    headers = {}
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key
    try:
        response = requests.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params={
                "query": paper.title,
                "limit": 1,
                "fields": "title,abstract,venue,year,externalIds,authors",
            },
            headers=headers,
            timeout=HTTP_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException:
        paper.notes.append("Semantic Scholar metadata lookup failed.")
        return

    data = response.json().get("data", [])
    if not data:
        return
    match = data[0]
    if not paper.abstract and match.get("abstract"):
        paper.abstract = match["abstract"]
    if not paper.venue and match.get("venue"):
        paper.venue = match["venue"]
    external_ids = match.get("externalIds") or {}
    if not paper.doi and external_ids.get("DOI"):
        paper.doi = external_ids["DOI"]
    if not paper.arxiv_id and external_ids.get("ArXiv"):
        paper.arxiv_id = external_ids["ArXiv"]


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        parsed = date_parser.parse(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed
