"""
TechCrunch scraper implementation.
"""

import sys
from datetime import datetime

from bs4 import BeautifulSoup, Tag

# For Python 3.11, we need typing_extensions for @override
from typing_extensions import override

from . import base


class TechCrunchScraper(base.NewsScraper):
    """Scraper for TechCrunch website."""

    def __init__(self):
        """Initialize the TechCrunch scraper."""
        super().__init__(
            source_name="TechCrunch",
            base_url="https://techcrunch.com",
            category_urls={
                "default": "/latest ",
                "latest": "/latest ",
                "ai": "/category/artificial-intelligence",
                "amazon": "/tag/amazon",
                "apps": "/category/apps",
                "biotech-health": "/category/biotech-health",
                "climate": "/category/climate",
                "cloud": "/tag/cloud-computing",
                "commerce": "/category/commerce",
                "crypto": "/category/cryptocurrency",
                "enterprise": "/category/enterprise",
                "electric vehicles": "/tag/evs",
                "fintech": "/category/fintech",
                "fundraising": "/category/fundraising",
                "gadgets": "/category/gadgets",
                "gaming": "/category/gaming",
                "google": "/tag/google",
                "government": "/category/government-policy",
                "hardware": "/category/hardware",
                "instagram": "/tag/instagram",
                "layoffs": "/tag/layoffs",
                "media entertainment": "/category/media-entertainment",
                "meta": "/tag/meta",
                "microsoft": "/tag/microsoft",
                "privacy": "/category/privacy",
                "robotics": "/category/robots",
                "social": "/category/social",
                "space": "/category/space",
                "startups": "/category/startups",
                "tiktok": "/tags/tiktok",
                "transportation": "/category/transportation",
                "venture": "/category/venture",
            },
        )

    @override
    def _extract_article_from_list_item(
        self, element: Tag, category: str
    ) -> base.NewsArticle | None:
        """
        Extract article information from a list item element.

        Args:
            element: The BeautifulSoup element containing article information.
            category: The category the article belongs to.

        Returns:
            NewsArticle object or None if extraction failed.
        """
        # Extract title and URL
        title_elem = element.select_one("h3.loop-card__title a.loop-card__title-link")
        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        article_url = str(title_elem.get("href", ""))

        # Ensure article_url is valid
        if not article_url:
            return None

        # Extract description
        desc_elem = element.select_one("div.post-block__content")
        description = (
            desc_elem.get_text(strip=True) if desc_elem else "No description available."
        )

        # Extract image URL
        img_elem = element.select_one("figure.loop-card__figure img")
        image_url = img_elem.get("src") if img_elem else None

        # Extract published date
        time_elem = element.select_one("time")
        published_date = datetime.now()
        if time_elem and time_elem.has_attr("datetime"):
            published_date = datetime.fromisoformat(str(time_elem["datetime"]))

        # Extract category
        cat_elem = element.select_one(
            "div.loop-card__cat-group a.loop-card__cat, div.loop-card__cat-group span.loop-card__cat"
        )
        card_category = cat_elem.get_text(strip=True) if cat_elem else category

        return base.NewsArticle(
            title=title,
            url=str(article_url),
            description=description,
            published_date=(
                published_date.strftime("%Y-%m-%d %H:%M:%S") if published_date else None
            ),
            source=self.source_name,
            image_url=str(image_url) if image_url is not None else None,
            category=card_category,
            content=None,  # Don't fetch content at this stage
        )

    @override
    def _select_article_elements(
        self, soup: BeautifulSoup, max_articles: int
    ) -> list[Tag]:
        """
        Select article elements from TechCrunch's HTML structure.

        Args:
            soup: BeautifulSoup object containing the HTML
            max_articles: Maximum number of articles to select

        Returns:
            List of BeautifulSoup Tag objects representing article elements
        """
        article_elements = soup.select("li.wp-block-post")
        print(
            f"[INFO] Found {len(article_elements)} article elements. Extracting up to {max_articles}"
        )
        return article_elements[:max_articles]

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """
        Extract the title from an article page.

        Args:
            soup: BeautifulSoup object containing the article HTML.

        Returns:
            The article title as a string.
        """
        # First try to get the title from the h1.article-hero__title element
        title_elem = soup.select_one("h1.article-hero__title")
        if title_elem:
            return title_elem.get_text(strip=True)

        # Fallback to the original method
        data_title_elem = soup.select_one("main[data-title-observer]")
        title = (
            data_title_elem.get("data-title-observer", "No title found")
            if data_title_elem
            else "No title found"
        )
        return str(title) if title else "No title found"

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """
        Extract the description from an article page.

        Args:
            soup: BeautifulSoup object containing the article HTML.

        Returns:
            The article description as a string.
        """
        desc_elem = soup.select_one("p#speakable-summary")
        if desc_elem:
            return desc_elem.get_text(strip=True)

        p_elem = soup.select_one("div.entry-content p")
        return p_elem.get_text(strip=True) if p_elem else "No description available."

    def _extract_published_date(self, soup: BeautifulSoup) -> str | None:
        """
        Extract the published date from an article page.

        Args:
            soup: BeautifulSoup object containing the article HTML.

        Returns:
            The published date as a formatted string or None if extraction failed.
        """
        time_elem = soup.select_one("time.article__timestamp")
        if time_elem and time_elem.has_attr("datetime"):
            try:
                date = datetime.fromisoformat(str(time_elem["datetime"]))
                return date.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass
        return None

    def _extract_image_url(self, soup: BeautifulSoup) -> str | None:
        """
        Extract the image URL from an article page.

        Args:
            soup: BeautifulSoup object containing the article HTML.

        Returns:
            The image URL as a string or None if extraction failed.
        """
        img_elem = soup.select_one("figure.article__featured-image img")
        return str(img_elem.get("src")) if img_elem and img_elem.get("src") else None

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """
        Extract the content from an article page.

        Args:
            soup: BeautifulSoup object containing the article HTML.

        Returns:
            The article content as a string.
        """
        content_elem = soup.select_one("div.entry-content")
        return (
            content_elem.get_text(strip=True)
            if content_elem
            else "No content available."
        )

    @override
    def _extract_article_info(
        self, news_article: base.NewsArticle, soup: BeautifulSoup
    ) -> base.NewsArticle:
        """
        Extract all article information from a soup object in one go.

        Args:
            news_article: Partially populated NewsArticle object
            soup: BeautifulSoup object containing the article HTML

        Returns:
            A NewsArticle object with all extracted information
        """
        news_article["title"] = self._extract_title(soup)
        news_article["description"] = self._extract_description(soup)
        news_article["published_date"] = self._extract_published_date(soup)
        news_article["image_url"] = self._extract_image_url(soup)
        news_article["content"] = self._extract_content(soup)

        return news_article

    @override
    def fetch_article_by_url(self, url: str) -> base.NewsArticle:
        """
        Fetch a single news article from TechCrunch by its URL.

        Args:
            url: The URL of the news article to fetch.
            category: Optional category for the article.

        Returns:
            A NewsArticle object representing the article at the given URL.
        """
        soup = self.fetch_html_content(url)
        if not soup:
            raise ValueError(f"Failed to fetch article from URL: {url}")

        # Create an empty article object with just the URL and source
        article = base.NewsArticle(
            title="",
            url=url,
            description=None,
            published_date=None,
            source=self.source_name,
            image_url=None,
            content=None,
            category=None,
        )

        # Extract all article info at once using the helper method
        return self._extract_article_info(article, soup)


# Allow running this scraper standalone for testing
if __name__ == "__main__":
    # Create scraper
    scraper = TechCrunchScraper()

    # Get command line arguments or use defaults
    selected_category = sys.argv[1] if len(sys.argv) > 1 else "technology"
    article_limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    # Print available categories
    print(f"Available categories: {', '.join(scraper.get_available_categories())}")
    print(f"Fetching up to {article_limit} articles from category: {selected_category}")

    # Fetch and print articles
    fetched_articles = scraper.fetch_articles(selected_category, article_limit)

    if not fetched_articles:
        print("No articles found.")
    else:
        print(f"Found {len(fetched_articles)} articles:")
        for i, fetched_article in enumerate(fetched_articles, 1):
            print(f"\n{i}. {fetched_article['title']}")
            print(f"   URL: {fetched_article['url']}")
            print(f"   Date: {fetched_article['published_date']}")
            print(f"   Content: {fetched_article['content']}")
            if fetched_article["description"]:
                print(f"   Description: {fetched_article['description']}")
