"""News-specific models and re-exports of engine types."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from self_healing_scraper.models import (
    FieldExtractor,
    GeneratedParser,
    PageContent,
    PageKind,
    ParserDefinition,
    ParserStatus,
    ValidationCheck,
    ValidationFailure,
    ValidationResult,
    ValidationSuite,
)
from typing_extensions import TypedDict

__all__ = [
    "BatchScrapeResult",
    "BatchUrlResult",
    "FieldExtractor",
    "GeneratedParser",
    "NewsArticle",
    "PageContent",
    "PageKind",
    "ParserDefinition",
    "ParserStatus",
    "ScrapeResult",
    "ValidationCheck",
    "ValidationFailure",
    "ValidationResult",
    "ValidationSuite",
]


class NewsArticle(TypedDict, total=False):
    title: str
    url: str
    description: str | None
    published_date: str | None
    source: str
    image_url: str | None
    category: str | None
    content: str | None
    authors: str | None
    tags: str | None
    metadata: dict[str, Any] | None


class ScrapeResult(BaseModel):
    url: str
    articles: list[NewsArticle]
    parser_id: str | None = None
    parser_version: int | None = None
    created_parser: bool = False
    repaired: bool = False
    attempts: int = 1


class BatchUrlResult(BaseModel):
    """Per-URL outcome for a resilient batch scrape."""

    url: str
    ok: bool
    articles: list[NewsArticle] = []
    parser_id: str | None = None
    parser_version: int | None = None
    created_parser: bool = False
    repaired: bool = False
    attempts: int = 0
    error: str | None = None


class BatchScrapeResult(BaseModel):
    """Envelope returned by ``scrape_news_urls_resilient`` / ``news-scrape batch``."""

    results: list[BatchUrlResult]
