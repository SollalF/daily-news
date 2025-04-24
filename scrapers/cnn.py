"""
CNN scraper implementation.
"""

import sys
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from bs4.element import PageElement

# For Python 3.11, we need typing_extensions for @override
from typing_extensions import override

from . import base

BASE_URL = "https://www.cnn.com"

CATEGORY_URLS = {
    "default": "/world",
    "latest": "/world",  # Map latest to world for consistency with other scrapers
    "world": "/world",
    "us": "/us",
    "technology": "/business/tech",
    "general": "/weather",  # Map weather to general
}


class CNNScraper(base.NewsScraper):
    """Scraper for CNN website."""

    def __init__(
        self,
        base_url: str = BASE_URL,
        category_urls: dict[str, str] = CATEGORY_URLS,
    ):
        """Initialize the CNN scraper."""
        super().__init__(base_url, category_urls, "CNN")

    def _safe_find_link(self, element: PageElement | None) -> str:
        """
        Safely find a link element and extract its href attribute.

        Args:
            element: BeautifulSoup element to search in

        Returns:
            URL string or empty string if not found
        """
        if not element or not isinstance(element, Tag):
            return ""

        # Direct link if element is an anchor
        if element.name == "a" and element.has_attr("href"):
            return str(element["href"])

        # Special case for container__headline-text which is often a span inside a link
        if element.name == "span":
            # Check if element has the class we're looking for
            element_classes = element.get("class")
            if (
                isinstance(element_classes, list)
                and "container__headline-text" in element_classes
            ):
                # Check for parent or ancestor anchor
                parent = element.parent
                while parent and parent.name != "a" and parent.name != "body":
                    parent = parent.parent

                if parent and parent.name == "a" and parent.has_attr("href"):
                    return str(parent["href"])

        # Try to find a nested link
        link_elem = element.find("a")
        if link_elem and isinstance(link_elem, Tag) and link_elem.has_attr("href"):
            return str(link_elem["href"])

        return ""

    @override
    def _select_article_elements(
        self, soup: BeautifulSoup, max_articles: int
    ) -> list[Tag]:
        """
        Select article elements from CNN's HTML structure.

        Args:
            soup: BeautifulSoup object containing the HTML
            max_articles: Maximum number of articles to select

        Returns:
            List of BeautifulSoup Tag objects representing article elements
        """
        # CSS selectors targeting article containers on CNN's main sections and landing pages
        article_selectors = [
            "div.container__item",
            "div.card",
            "div.column--idx-0 article",
            "div.column--idx-1 article",
            "div.card-container",
            "article.card",
            "div.headline-container",
        ]

        # Join selectors with commas for a single select call
        selector_string = ", ".join(article_selectors)
        article_elements = soup.select(selector_string)

        print(
            f"[INFO] Found {len(article_elements)} article elements. Extracting up to {max_articles}"
        )

        # Return only what we need based on max_articles
        return article_elements[:max_articles]

    def _get_attr_safe(
        self, element: PageElement | None, attr_name: str, default: str = ""
    ) -> str:
        """
        Safely get an attribute from a BeautifulSoup element.

        Args:
            element: BeautifulSoup element
            attr_name: Name of the attribute to get
            default: Default value if attribute doesn't exist

        Returns:
            Attribute value as string or default
        """
        if element and isinstance(element, Tag) and element.has_attr(attr_name):
            return str(element[attr_name])
        return default

    @override
    def fetch_article_by_url(self, url: str) -> base.NewsArticle:
        """
        Fetch a single news article from CNN by its URL.

        Args:
            url: The URL of the news article to fetch.

        Returns:
            A NewsArticle object representing the article at the given URL.
        """
        # Use the base class method to fetch HTML content
        soup = self.fetch_html_content(url)
        if not soup:
            raise ValueError(f"Failed to fetch article: {url}")

        # Create an empty article object with just source and URL
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

        # Extract article info using the helper methods
        return self._extract_article_info(article, soup)

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """
        Extract the title from an article page.

        Args:
            soup: BeautifulSoup object containing the article HTML

        Returns:
            The article title as a string
        """
        title_elem = soup.select_one(
            "h1.headline_live-story__text, "
            + "h1.pg-headline, h1.headline, "
            + "meta[property='og:title']"
        )

        if title_elem:
            if title_elem.name == "meta":
                title = title_elem.get("content", "No title found")
            else:
                title = title_elem.get_text(strip=True)
        else:
            title = "No title found"

        return str(title) or "No title found"

    def _extract_url(self, soup: BeautifulSoup) -> str:
        """
        Extract the canonical URL from an article page.

        Args:
            soup: BeautifulSoup object containing the article HTML

        Returns:
            The article URL as a string
        """
        url_elem = soup.select_one("link[rel='canonical'], meta[property='og:url']")
        return self._get_attr_safe(
            url_elem, "href" if url_elem and url_elem.name == "link" else "content"
        )

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """
        Extract the description from an article page.

        Args:
            soup: BeautifulSoup object containing the article HTML

        Returns:
            The article description as a string
        """
        desc_elem = soup.select_one(
            "meta[property='og:description'], meta[name='description']"
        )
        description = self._get_attr_safe(desc_elem, "content")

        if not description:
            # Try different paragraph selectors
            p_elem = soup.select_one(
                "div.headline_live-story__sub-text, "
                + "div.article__content p, .paragraph, .zn-body__paragraph, "
                + ".speakable-paragraph"
            )
            description = (
                p_elem.get_text(strip=True) if p_elem else "No description available."
            )

        return description

    def _extract_published_date(self, soup: BeautifulSoup) -> str | None:
        """
        Extract the published date from an article page.

        Args:
            soup: BeautifulSoup object containing the article HTML

        Returns:
            The published date as a formatted string or None if extraction failed
        """
        time_elem = soup.select_one(
            "div.timestamp, "
            + "meta[property='article:published_time'], "
            + "meta[name='pubdate'], time.update-time"
        )

        published_date = None
        if time_elem:
            date_str = ""
            if time_elem.name == "time" or time_elem.name == "div":
                date_str = self._get_attr_safe(time_elem, "datetime")
                if not date_str and time_elem.name == "div":
                    date_str = time_elem.get_text(strip=True)
            else:
                date_str = self._get_attr_safe(time_elem, "content")

            try:
                if date_str:
                    if "Z" in date_str:
                        date_str = date_str.replace("Z", "+00:00")
                    published_date = datetime.fromisoformat(date_str)
            except (ValueError, AttributeError):
                # If standard parsing fails, try more formats
                try:
                    if "EDT" in date_str or "EST" in date_str:
                        # Example: "12:48 AM EDT, Tue April 22, 2025"
                        date_str = date_str.replace("Updated", "").strip()
                        published_date = datetime.strptime(
                            date_str, "%I:%M %p %Z, %a %B %d, %Y"
                        )
                except (ValueError, AttributeError):
                    published_date = None

        return published_date.strftime("%Y-%m-%d %H:%M:%S") if published_date else None

    def _extract_image_url(self, soup: BeautifulSoup) -> str | None:
        """
        Extract the image URL from an article page.

        Args:
            soup: BeautifulSoup object containing the article HTML

        Returns:
            The image URL as a string or None if extraction failed
        """
        img_elem = soup.select_one("meta[property='og:image']")
        return self._get_attr_safe(img_elem, "content") or None

    def _extract_byline(self, soup: BeautifulSoup) -> str | None:
        """
        Extract the author/byline from an article page.

        Args:
            soup: BeautifulSoup object containing the article HTML

        Returns:
            The byline as a string or None if extraction failed
        """
        byline_elem = soup.select_one(
            "div.byline__names, div.headline_live-story__byline-sub-text"
        )
        return byline_elem.get_text(strip=True) if byline_elem else None

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """
        Extract the content from an article page.

        Args:
            soup: BeautifulSoup object containing the article HTML

        Returns:
            The article content as a string
        """
        content_paragraphs = soup.select(
            "div.live-story-post__content .paragraph, "
            + "div.article__content p, .zn-body__paragraph, .paragraph, "
            + ".article-content .speakable-paragraph, .article-content p, "
            + ".article__main p, .article-content .paragraph"
        )

        # Remove any ads or irrelevant blocks
        content_texts: list[str] = []
        for p in content_paragraphs:
            if p.parent and p.parent.has_attr("class"):
                parent_classes = " ".join(p.parent["class"])
                if "ad" in parent_classes.lower() or "promo" in parent_classes.lower():
                    continue
            content_texts.append(p.get_text(strip=True))

        return "\n\n".join(content_texts) if content_texts else "No content available."

    @override
    def _extract_article_info(
        self, news_article: base.NewsArticle, soup: BeautifulSoup
    ) -> base.NewsArticle:
        """
        Extract article information from a BeautifulSoup object.

        Args:
            news_article: Partially populated NewsArticle object
            soup: BeautifulSoup object containing the article HTML

        Returns:
            A NewsArticle object with all extracted information
        """
        # Use the helper methods to extract article info
        news_article["title"] = self._extract_title(soup)

        # Only update URL if it's not already set or is empty
        url = self._extract_url(soup)
        if url and not news_article["url"]:
            news_article["url"] = url

        news_article["description"] = self._extract_description(soup)
        news_article["published_date"] = self._extract_published_date(soup)
        news_article["image_url"] = self._extract_image_url(soup)
        news_article["content"] = self._extract_content(soup)

        return news_article

    @override
    def _extract_article_from_list_item(
        self, element: Tag, category: str
    ) -> base.NewsArticle | None:
        """
        Extract article information from a list item element.

        Args:
            element: The BeautifulSoup element containing article information
            category: The category the article belongs to

        Returns:
            NewsArticle object or None if extraction failed
        """
        # Find title and URL with updated selectors
        title_elem = element.select_one(
            "span.container__headline-text, "
            + "h3.headline a, span.headline a, h3.container__headline-text, "
            + "h4.container__headline-text, h3 a, h2 a, .headline a, "
            + "h3.container__headline"
        )
        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)

        # Extract URL safely
        article_url_str = self._safe_find_link(title_elem)

        # CNN sometimes uses relative URLs
        if article_url_str and not article_url_str.startswith("http"):
            article_url_str = urljoin(self.base_url, article_url_str)

        # Skip if no URL or video content
        if not article_url_str or "/videos/" in article_url_str:
            return None

        # Get description if available (but don't fetch full article)
        desc_elem = element.select_one(
            ".cd__description, .cd__headline-text, .headline__text"
        )
        description = desc_elem.get_text(strip=True) if desc_elem else None

        # Try to extract image
        img_elem = element.select_one("img.media__image")
        image_url = self._get_attr_safe(img_elem, "src") if img_elem else None

        # For CNN front page, sometimes images are in data-src-large attribute
        if not image_url and img_elem:
            image_url = self._get_attr_safe(img_elem, "data-src-large")

        # Return basic article info without fetching full content
        return base.NewsArticle(
            title=title,
            url=article_url_str,
            description=description,
            published_date=None,  # We don't have this in list view
            source=self.source_name,
            image_url=image_url,
            category=category,
            content=None,  # Don't fetch content at this stage
        )


# Allow running this scraper standalone for testing
if __name__ == "__main__":
    # Create scraper
    scraper = CNNScraper()

    # Get command line arguments or use defaults
    selected_category_str = sys.argv[1] if len(sys.argv) > 1 else "world"
    article_limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    # Use the category string directly
    selected_category = selected_category_str

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
            if fetched_article["description"]:
                print(f"   Description: {fetched_article['description'][:150]}...")
            if fetched_article["content"]:
                content_preview = (
                    fetched_article["content"][:150] + "..."
                    if len(fetched_article["content"]) > 150
                    else fetched_article["content"]
                )
                print(f"   Content preview: {content_preview}")
