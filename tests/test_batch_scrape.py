"""Resilient batch scrape façade tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from news_scraper.models import BatchScrapeResult, ScrapeResult
from news_scraper.scrape import scrape_news_urls_resilient
from news_scraper.settings import Settings


@pytest.mark.asyncio
async def test_scrape_news_urls_resilient_continues_after_failure() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://news:news@localhost:5432/news_scraper",
        llm_api_key="test",
    )
    ok = ScrapeResult(
        url="https://example.com/ok/",
        articles=[
            {
                "title": "Ok Story",
                "url": "https://example.com/ok-story/",
                "source": "Example",
            }
        ],
        parser_id="p1",
        parser_version=2,
        created_parser=False,
        repaired=True,
        attempts=2,
    )

    async def fake_scrape(
        url: str,
        *,
        settings: Settings | None = None,
        ensure_schema: bool = True,
    ) -> ScrapeResult:
        if "fail" in url:
            raise RuntimeError("boom")
        return ok

    with (
        patch("news_scraper.scrape.init_db", AsyncMock()),
        patch("news_scraper.scrape.scrape_news_url", side_effect=fake_scrape),
    ):
        batch = await scrape_news_urls_resilient(
            [
                "https://example.com/ok/",
                "https://example.com/fail/",
                "https://example.com/ok-again/",
            ],
            settings=settings,
        )

    assert isinstance(batch, BatchScrapeResult)
    assert len(batch.results) == 3
    assert batch.results[0].ok is True
    assert batch.results[0].articles[0]["title"] == "Ok Story"
    assert batch.results[0].repaired is True
    assert batch.results[1].ok is False
    assert batch.results[1].error == "boom"
    assert batch.results[1].articles == []
    assert batch.results[2].ok is True


@pytest.mark.asyncio
async def test_scrape_news_urls_resilient_empty() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://news:news@localhost:5432/news_scraper",
        llm_api_key="test",
    )
    with patch("news_scraper.scrape.init_db", AsyncMock()) as init_db:
        batch = await scrape_news_urls_resilient([], settings=settings)

    assert batch.results == []
    init_db.assert_not_awaited()
