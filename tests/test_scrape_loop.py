"""Orchestration tests with mocked fetch/AI/DB side effects."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from news_scraper.models import (
    FieldExtractor,
    GeneratedParser,
    PageContent,
    ParserDefinition,
    ScrapeResult,
    ValidationCheck,
    ValidationSuite,
)
from news_scraper.scrape import scrape_news_url
from news_scraper.settings import Settings


def _generated() -> GeneratedParser:
    return GeneratedParser(
        name="techcrunch-latest",
        url_pattern=r"https://techcrunch\.com/latest/?",
        page_kind="listing",
        definition=ParserDefinition(
            js_enabled=False,
            item_selector="li.post",
            source_name="TechCrunch",
            fields={
                "title": FieldExtractor(selector="h2.title a", attr="text"),
                "url": FieldExtractor(selector="h2.title a", attr="href"),
            },
        ),
        validations=ValidationSuite(
            checks=[
                ValidationCheck(type="min_count", value=1),
                ValidationCheck(type="required_fields", fields=["title", "url"]),
            ]
        ),
    )


@pytest.mark.asyncio
async def test_scrape_creates_parser_when_missing(listing_html: str) -> None:
    settings = Settings(
        database_url="postgresql+psycopg://news:news@localhost:5432/news_scraper",
        llm_api_key="test",
        max_repair_attempts=2,
    )
    page = PageContent(
        url="https://techcrunch.com/latest/",
        html=listing_html,
        success=True,
    )
    generated = _generated()
    record = SimpleNamespace(
        id=uuid4(),
        name=generated.name,
        url_pattern=generated.url_pattern,
        page_kind=generated.page_kind,
        definition=generated.definition.model_dump(),
        validations=generated.validations.model_dump(),
        version=1,
        status="draft",
    )

    repo = MagicMock()
    repo.find_by_url = AsyncMock(return_value=None)
    repo.create_from_generated = AsyncMock(return_value=record)
    repo.update_parser = AsyncMock(return_value=record)
    repo.save_run = AsyncMock()

    session = MagicMock()
    session_cm = AsyncMock()
    session_cm.__aenter__.return_value = session
    session_cm.__aexit__.return_value = None

    with (
        patch("news_scraper.scrape.init_db", AsyncMock()),
        patch("news_scraper.scrape.get_async_session", return_value=session_cm),
        patch("news_scraper.scrape.ParserRepository", return_value=repo),
        patch("news_scraper.scrape.fetch_page", AsyncMock(return_value=page)),
        patch("news_scraper.scrape.create_parser", AsyncMock(return_value=generated)),
    ):
        result = await scrape_news_url(
            "https://techcrunch.com/latest/",
            settings=settings,
            ensure_schema=True,
        )

    assert isinstance(result, ScrapeResult)
    assert result.created_parser is True
    assert len(result.articles) == 3
    repo.create_from_generated.assert_awaited_once()
    repo.update_parser.assert_awaited()
    repo.save_run.assert_awaited()
