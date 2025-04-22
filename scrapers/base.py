"""
Base interface for news scrapers.
"""

from abc import ABC, abstractmethod
from typing import TypedDict


class NewsArticle(TypedDict):
    """TypedDict representing the structure of a news article."""

    title: str
    url: str
    description: str | None
    published_date: str | None
    source: str
    image_url: str | None
    category: str
    content: str | None


class NewsScraper(ABC):
    """Abstract base class for news scrapers."""

    def __init__(self, source_name: str = "Unknown"):
        """
        Initialize the scraper with a source name.

        Args:
            source_name: Name of the news source
        """
        self.source_name: str = source_name

    @abstractmethod
    def fetch_articles(
        self, category: str = "default", max_articles: int = 5
    ) -> list[NewsArticle]:
        """
        Fetch news articles from the source.

        Args:
            category: News category to fetch
            max_articles: Maximum number of articles to return

        Returns:
            List of NewsArticle objects
        """

    @abstractmethod
    def fetch_article_by_url(self, url: str) -> NewsArticle:
        """
        Fetch a single news article from the source by its URL.

        Args:
            url: The URL of the news article to fetch.

        Returns:
            A NewsArticle object representing the article at the given URL.
        """

    def get_available_categories(self) -> list[str]:
        """
        Get the list of categories available from this source.

        Returns:
            List of category strings
        """
        return ["general"]
