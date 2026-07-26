"""Public scrape orchestration with self-healing parsers."""

from __future__ import annotations

import logging
from urllib.parse import urlsplit, urlunsplit

from news_scraper.agent.create_parser import create_parser
from news_scraper.agent.repair_parser import repair_parser
from news_scraper.db.repository import ParserRepository
from news_scraper.db.session import get_async_session, init_db
from news_scraper.fetch.crawler import fetch_page
from news_scraper.models import (
    ParserDefinition,
    ParserStatus,
    ScrapeResult,
    ValidationSuite,
)
from news_scraper.runtime.executor import execute_parser
from news_scraper.runtime.validators import run_validations
from news_scraper.settings import Settings, get_settings

logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    path = parts.path or "/"
    return urlunsplit((parts.scheme, parts.netloc.lower(), path, parts.query, ""))


async def scrape_news_url(
    url: str,
    *,
    settings: Settings | None = None,
    ensure_schema: bool = True,
) -> ScrapeResult:
    """Scrape a news URL using a stored or newly created self-healing parser."""
    cfg = settings or get_settings()
    url = normalize_url(url)
    if ensure_schema:
        await init_db(cfg)

    async with get_async_session(cfg) as session:
        repo = ParserRepository(session)
        record = await repo.find_by_url(url)
        created_parser = False
        repaired = False

        # Initial fetch without parser hints (or with existing definition hints).
        definition = (
            ParserDefinition.model_validate(record.definition) if record else None
        )
        page = await fetch_page(url, definition=definition, settings=cfg)
        if not page.success:
            raise RuntimeError(page.error_message or f"Failed to fetch {url}")

        if record is None:
            logger.info("No parser for %s — creating via AI", url)
            generated = await create_parser(page, settings=cfg)
            record = await repo.create_from_generated(
                generated, status=ParserStatus.DRAFT
            )
            created_parser = True
            # Re-fetch with wait_for / js hints from the new definition.
            definition = ParserDefinition.model_validate(record.definition)
            page = await fetch_page(url, definition=definition, settings=cfg)
            if not page.success:
                raise RuntimeError(page.error_message or f"Failed to fetch {url}")

        attempts = 0
        max_attempts = max(1, cfg.max_repair_attempts)
        last_errors: list[dict] = []

        while attempts < max_attempts:
            attempts += 1
            definition = ParserDefinition.model_validate(record.definition)
            validations = ValidationSuite.model_validate(record.validations)

            # Optionally refresh page with current wait hints after repair.
            if attempts > 1 or created_parser:
                page = await fetch_page(url, definition=definition, settings=cfg)
                if not page.success:
                    last_errors = [{"message": page.error_message or "fetch failed"}]
                    await repo.update_parser(
                        record,
                        status=ParserStatus.FAILED,
                        last_error=page.error_message,
                    )
                    break

            articles = execute_parser(page, definition, record.page_kind)
            validation = run_validations(articles, validations, page)

            if validation.passed:
                await repo.update_parser(record, mark_success=True)
                await repo.save_run(
                    url=url,
                    parser_id=record.id,
                    parser_version=record.version,
                    success=True,
                    articles=articles,
                    page_sample=page.html[: cfg.page_sample_chars],
                )
                return ScrapeResult(
                    url=url,
                    articles=articles,
                    parser_id=str(record.id),
                    parser_version=record.version,
                    created_parser=created_parser,
                    repaired=repaired,
                    attempts=attempts,
                )

            last_errors = [f.model_dump() for f in validation.failures]
            logger.warning(
                "Validation failed for %s (attempt %s/%s): %s",
                url,
                attempts,
                max_attempts,
                last_errors,
            )

            if attempts >= max_attempts:
                await repo.update_parser(
                    record,
                    status=ParserStatus.FAILED,
                    last_error=str(last_errors),
                )
                await repo.save_run(
                    url=url,
                    parser_id=record.id,
                    parser_version=record.version,
                    success=False,
                    articles=articles,
                    validation_errors=last_errors,
                    page_sample=page.html[: cfg.page_sample_chars],
                    error_message="Validation failed after max repair attempts",
                )
                break

            generated = await repair_parser(
                page=page,
                name=record.name,
                url_pattern=record.url_pattern,
                page_kind=record.page_kind,
                definition=definition,
                validations=validations,
                validation_result=validation,
                settings=cfg,
            )
            record = await repo.update_parser(
                record,
                name=generated.name,
                url_pattern=generated.url_pattern,
                page_kind=generated.page_kind,
                definition=generated.definition,
                validations=generated.validations,
                status=ParserStatus.DRAFT,
                bump_version=True,
                last_error=str(last_errors),
            )
            repaired = True

        raise RuntimeError(
            f"Failed to scrape {url} after {attempts} attempt(s): {last_errors}"
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
