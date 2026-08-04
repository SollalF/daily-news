"""Self-healing, database-backed news scraper built on self-healing-scraper."""

from news_scraper.models import (
    BatchScrapeResult,
    BatchUrlResult,
    NewsArticle,
    ScrapeResult,
)
from news_scraper.scrape import (
    scrape_news_url,
    scrape_news_urls,
    scrape_news_urls_resilient,
)

__all__ = [
    "BatchScrapeResult",
    "BatchUrlResult",
    "NewsArticle",
    "ScrapeResult",
    "scrape_news_url",
    "scrape_news_urls",
    "scrape_news_urls_resilient",
]
