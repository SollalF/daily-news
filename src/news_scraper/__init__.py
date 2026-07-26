"""Self-healing, database-backed news scraper built on self-healing-scraper."""

from news_scraper.models import NewsArticle, ScrapeResult
from news_scraper.scrape import scrape_news_url, scrape_news_urls

__all__ = [
    "NewsArticle",
    "ScrapeResult",
    "scrape_news_url",
    "scrape_news_urls",
]
