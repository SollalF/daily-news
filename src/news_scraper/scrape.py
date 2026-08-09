"""Public news scrape façade over self-healing-scraper."""

from __future__ import annotations

import logging
from typing import cast

from self_healing_scraper import normalize_url, scrape_url

from news_scraper.db.repository import ParserRepository
from news_scraper.db.session import get_async_session, init_db
from news_scraper.domain import NEWS_DOMAIN
from news_scraper.models import (
    BatchScrapeResult,
    BatchUrlResult,
    NewsArticle,
    ScrapeResult,
)
from news_scraper.settings import Settings, get_settings

__all__ = [
    "normalize_url",
    "scrape_news_url",
    "scrape_news_urls",
    "scrape_news_urls_resilient",
]

logger = logging.getLogger(__name__)


async def scrape_news_url(
    url: str,
    *,
    settings: Settings | None = None,
    ensure_schema: bool = True,
    force_refresh: bool = False,
) -> ScrapeResult:
    """Scrape a news URL using a stored or newly created self-healing parser.

    Article URLs already in ``scrape_runs`` are served from storage unless
    ``force_refresh`` is set.
    """
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
            force_refresh=force_refresh,
        )
        return ScrapeResult(
            url=raw.url,
            articles=[cast(NewsArticle, item) for item in raw.items],
            parser_id=raw.parser_id,
            parser_version=raw.parser_version,
            created_parser=raw.created_parser,
            repaired=raw.repaired,
            attempts=raw.attempts,
            from_cache=raw.from_cache,
        )


async def scrape_news_urls(
    urls: list[str],
    *,
    settings: Settings | None = None,
    ensure_schema: bool = True,
    force_refresh: bool = False,
) -> list[ScrapeResult]:
    results: list[ScrapeResult] = []
    for url in urls:
        results.append(
            await scrape_news_url(
                url,
                settings=settings,
                ensure_schema=ensure_schema,
                force_refresh=force_refresh,
            )
        )
    return results


async def scrape_news_urls_resilient(
    urls: list[str],
    *,
    settings: Settings | None = None,
    ensure_schema: bool = True,
    force_refresh: bool = False,
) -> BatchScrapeResult:
    """Scrape many URLs; capture per-URL failures instead of aborting the batch."""
    cfg = settings or get_settings()
    if ensure_schema and urls:
        await init_db(cfg)

    outcomes: list[BatchUrlResult] = []
    for url in urls:
        try:
            result = await scrape_news_url(
                url,
                settings=cfg,
                ensure_schema=False,
                force_refresh=force_refresh,
            )
            outcomes.append(
                BatchUrlResult(
                    url=result.url,
                    ok=True,
                    articles=result.articles,
                    parser_id=result.parser_id,
                    parser_version=result.parser_version,
                    created_parser=result.created_parser,
                    repaired=result.repaired,
                    attempts=result.attempts,
                    from_cache=result.from_cache,
                )
            )
        except Exception as exc:
            logger.exception("Batch scrape failed for %s", url)
            outcomes.append(
                BatchUrlResult(
                    url=url,
                    ok=False,
                    error=str(exc) or exc.__class__.__name__,
                )
            )
    return BatchScrapeResult(results=outcomes)
