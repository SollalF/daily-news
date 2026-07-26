"""Façade tests with mocked engine scrape_url."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from self_healing_scraper.models import ScrapeResult as EngineScrapeResult

from news_scraper.models import ScrapeResult
from news_scraper.scrape import scrape_news_url
from news_scraper.settings import Settings


@pytest.mark.asyncio
async def test_scrape_news_url_maps_engine_result() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://news:news@localhost:5432/news_scraper",
        llm_api_key="test",
        max_repair_attempts=2,
    )
    engine_result = EngineScrapeResult(
        url="https://techcrunch.com/latest/",
        items=[
            {
                "title": "Alpha Story",
                "url": "https://techcrunch.com/2026/07/25/alpha/",
                "source": "TechCrunch",
            }
        ],
        parser_id=str(uuid4()),
        parser_version=1,
        created_parser=True,
        repaired=False,
        attempts=1,
    )

    session = MagicMock()
    session_cm = AsyncMock()
    session_cm.__aenter__.return_value = session
    session_cm.__aexit__.return_value = None

    with (
        patch("news_scraper.scrape.init_db", AsyncMock()),
        patch("news_scraper.scrape.get_async_session", return_value=session_cm),
        patch(
            "news_scraper.scrape.scrape_url",
            AsyncMock(return_value=engine_result),
        ) as mocked_scrape,
    ):
        result = await scrape_news_url(
            "https://techcrunch.com/latest/",
            settings=settings,
            ensure_schema=True,
        )

    assert isinstance(result, ScrapeResult)
    assert result.created_parser is True
    assert len(result.articles) == 1
    assert result.articles[0]["title"] == "Alpha Story"
    mocked_scrape.assert_awaited_once()
    kwargs = mocked_scrape.await_args
    assert kwargs is not None
    assert kwargs.kwargs["domain"] is not None
    assert kwargs.kwargs["store"] is not None
