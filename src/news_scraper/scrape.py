"""Public news scrape façade over self-healing-scraper."""

from __future__ import annotations

from typing import cast

from self_healing_scraper import normalize_url, scrape_url

from news_scraper.db.repository import ParserRepository
from news_scraper.db.session import get_async_session, init_db
from news_scraper.domain import NEWS_DOMAIN
from news_scraper.models import NewsArticle, ScrapeResult
from news_scraper.settings import Settings, get_settings

__all__ = ["normalize_url", "scrape_news_url", "scrape_news_urls"]


async def scrape_news_url(
    url: str,
    *,
    settings: Settings | None = None,
    ensure_schema: bool = True,
) -> ScrapeResult:
    """Scrape a news URL using a stored or newly created self-healing parser."""
    cfg = settings or get_settings()
    if ensure_schema:
        await init_db(cfg)

    async with get_async_session(cfg) as session:
        store = ParserRepository(session)
        raw = await scrape_url(
            url,
            store=store,
            domain=NEWS_DOMAIN,
            settings=cfg.to_engine(),
        )
        return ScrapeResult(
            url=raw.url,
            articles=[cast(NewsArticle, item) for item in raw.items],
            parser_id=raw.parser_id,
            parser_version=raw.parser_version,
            created_parser=raw.created_parser,
            repaired=raw.repaired,
            attempts=raw.attempts,
        )


async def scrape_news_urls(
    urls: list[str],
    *,
    settings: Settings | None = None,
    ensure_schema: bool = True,
) -> list[ScrapeResult]:
    results: list[ScrapeResult] = []
    for url in urls:
        results.append(
            await scrape_news_url(url, settings=settings, ensure_schema=ensure_schema)
        )
    return results
