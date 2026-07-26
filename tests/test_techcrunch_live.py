"""Optional live integration against TechCrunch + Postgres."""

from __future__ import annotations

import pytest

from news_scraper import scrape_news_url
from news_scraper.db.repository import ParserRepository
from news_scraper.db.session import get_async_session, init_db
from news_scraper.settings import get_settings


@pytest.mark.live
@pytest.mark.asyncio
async def test_techcrunch_latest_live() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    if not settings.database_url:
        pytest.skip("DATABASE_URL not set")

    await init_db(settings)
    async with get_async_session(settings) as session:
        existing = await ParserRepository(session).find_by_url(
            "https://techcrunch.com/latest/"
        )
    if existing is None and not settings.llm_api_key:
        pytest.skip("LLM_API_KEY required to create the first parser")

    result = await scrape_news_url("https://techcrunch.com/latest/", settings=settings)
    assert result.articles
    assert all(a.get("title") and a.get("url") for a in result.articles)
    assert result.parser_id is not None

    again = await scrape_news_url("https://techcrunch.com/latest/", settings=settings)
    assert again.created_parser is False
    assert again.articles
