"""
Base interface for news scrapers.
"""

from abc import ABC, abstractmethod
from typing import TypedDict
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from logger import logger


class NewsArticle(TypedDict):
    """TypedDict representing the structure of a news article."""

    title: str
    url: str
    description: str | None
    published_date: str | None
    source: str
    image_url: str | None
    category: str | None
    content: str | None


class NewsScraper(ABC):
    """Abstract base class for news scrapers."""

    def __init__(
        self,
        base_url: str,
        category_urls: dict[str, str],
        source_name: str = "Unknown",
    ):
        """
        Initialize the scraper with a source name.

        Args:
            source_name: Name of the news source
        """
        self.base_url: str = base_url
        self.category_urls: dict[str, str] = category_urls
        self.source_name: str = source_name

    def fetch_articles(
        self, category: str = "default", max_articles: int = 5
    ) -> list[NewsArticle]:
        """
        Fetch articles from TechCrunch for a given category.

        Args:
            category: The category to fetch articles for.
            max_articles: The maximum number of articles to fetch.

        Returns:
            A list of NewsArticle objects.
        """

        # Get the URL for the category
        try:
            url = self.get_category_url(category)
        except ValueError:
            logger.warning(f"Category '{category}' not found. Skipping.")
            return []

        logger.info(
            f"Fetching articles from {url} in category {category} with max {max_articles} articles"
        )

        # Fetch and parse the HTML
        soup = self.fetch_html_content(url)
        if not soup:
            return []

        # Find article elements using the _select_article_elements method
        article_elements = self._select_article_elements(soup, max_articles)

        articles: list[NewsArticle] = []

        # Extract articles from elements
        for element in article_elements:
            article = self._extract_article_from_list_item(element, category)
            if article:
                articles.append(article)

        logger.info(f"Total articles fetched: {len(articles)}")
        return articles

    @abstractmethod
    def fetch_article_by_url(self, url: str) -> NewsArticle:
        """
        Fetch a single news article from the source by its URL.

        Args:
            url: The URL of the news article to fetch.

        Returns:
            A NewsArticle object representing the article at the given URL.
        """

    def get_category_url(self, category: str) -> str:
        """
        Get the full URL for a given category.

        Args:
            category: The category to get the URL for.

        Returns:
            The full URL for the category.
        """
        if category not in self.category_urls:
            raise ValueError(f"Category '{category}' not found")

        category_path = self.category_urls[category]
        return urljoin(self.base_url, category_path)

    def get_available_categories(self) -> list[str]:
        """
        Get the list of categories available from this source.

        Returns:
            List of category strings
        """
        return list(self.category_urls.keys())

    @abstractmethod
    def _extract_article_from_list_item(
        self, element: Tag, category: str
    ) -> NewsArticle | None:
        """
        Extract an article from a list item element.
        """

    def fetch_html_content(self, url: str) -> BeautifulSoup | None:
        """
        Fetch HTML content from a URL and parse it with BeautifulSoup.

        Args:
            url: The URL to fetch HTML from.

        Returns:
            BeautifulSoup object with the parsed HTML or None if failed.
        """
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                logger.error(
                    f"Failed to fetch URL {url}: Status code {response.status_code}"
                )
                return None

            return BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            logger.error(f"Exception while fetching {url}: {e}")
            return None

    @abstractmethod
    def _extract_article_info(
        self, news_article: NewsArticle, soup: BeautifulSoup
    ) -> NewsArticle:
        """
        Extract article information from a BeautifulSoup object.
        """

    @abstractmethod
    def _select_article_elements(
        self, soup: BeautifulSoup, max_articles: int
    ) -> list[Tag]:
        """
        Select article elements from the HTML.
        """
