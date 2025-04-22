"""
TechCrunch scraper implementation.
"""

import sys
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# For Python 3.11, we need typing_extensions for @override
from typing_extensions import override

from . import base


class TechCrunchScraper(base.NewsScraper):
    """Scraper for TechCrunch website."""

    def __init__(self):
        """Initialize the TechCrunch scraper."""
        super().__init__(source_name="TechCrunch")
        self.base_url: str = "https://techcrunch.com"
        self.category_urls: dict[str, str] = {
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
        }

    @override
    def get_available_categories(self) -> list[str]:
        """Get available categories for TechCrunch."""
        return list(self.category_urls.keys())

    @override
    def fetch_articles(
        self, category: str = "default", max_articles: int = 5
    ) -> list[base.NewsArticle]:
        # Log the category and number of articles being fetched
        print(
            f"[INFO] Fetching articles for category: {category}, max articles: {max_articles}"
        )

        # Use the right category URL or default to technology news
        if category not in self.category_urls:
            print(f"[INFO] Category '{category}' not found. Defaulting to 'default'")
            category = "default"

        category_path = self.category_urls[category]
        url = (
            self.base_url
            if category_path == ""
            else urljoin(self.base_url, category_path)
        )
        print(f"[INFO] Fetching URL: {url}")

        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(
                f"[ERROR] Failed to fetch TechCrunch {category} news: Status code {response.status_code}"
            )
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        article_elements = soup.select("li.wp-block-post")
        print(
            f"[INFO] Found {len(article_elements)} article elements. Extracting up to {max_articles}"
        )

        articles: list[base.NewsArticle] = []

        for _, element in enumerate(article_elements[:max_articles], start=1):
            # Title and URL
            title_elem = element.select_one(
                "h3.loop-card__title a.loop-card__title-link"
            )
            if not title_elem:
                continue
            title = title_elem.get_text(strip=True)
            article_url = str(title_elem.get("href", ""))

            # Ensure article_url is not None
            if not article_url:
                continue

            # Fetch full article content
            full_article = self.fetch_article_by_url(article_url)

            # Description (fallback if not present)
            desc_elem = element.select_one("div.post-block__content")
            description = (
                desc_elem.get_text(strip=True)
                if desc_elem
                else "No description available."
            )

            # Image
            img_elem = element.select_one("figure.loop-card__figure img")
            image_url = img_elem.get("src") if img_elem else None

            # Published date
            time_elem = element.select_one("time")
            published_date = datetime.now()
            if time_elem and time_elem.has_attr("datetime"):
                published_date = datetime.fromisoformat(str(time_elem["datetime"]))

            # Category
            cat_elem = element.select_one(
                "div.loop-card__cat-group a.loop-card__cat, div.loop-card__cat-group span.loop-card__cat"
            )
            card_category = cat_elem.get_text(strip=True) if cat_elem else category

            articles.append(
                {
                    "title": title,
                    "url": str(article_url) if article_url is not None else "",
                    "description": description,
                    "published_date": (
                        published_date.strftime("%Y-%m-%d %H:%M:%S")
                        if published_date
                        else None
                    ),
                    "source": self.source_name,
                    "image_url": str(image_url) if image_url is not None else None,
                    "category": card_category,
                    "content": full_article.get(
                        "content"
                    ),  # Add content from full article
                }
            )

        print(f"[INFO] Total articles fetched: {len(articles)}")
        return articles

    @override
    def fetch_article_by_url(self, url: str) -> base.NewsArticle:
        """
        Fetch a single news article from TechCrunch by its URL.

        Args:
            url: The URL of the news article to fetch.

        Returns:
            A NewsArticle object representing the article at the given URL.
        """
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            raise ValueError(
                f"Failed to fetch article: Status code {response.status_code}"
            )

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract title
        title_elem = soup.select_one("main[data-title-observer]")
        title = (
            title_elem.get("data-title-observer", "No title found")
            if title_elem
            else "No title found"
        )

        # Extract description (first paragraph or meta description)
        desc_elem = soup.select_one("p#speakable-summary")
        if desc_elem:
            description = desc_elem.get_text(strip=True)
        else:
            p_elem = soup.select_one("div.entry-content p")
            description = (
                p_elem.get_text(strip=True) if p_elem else "No description available."
            )

        # Extract published date
        time_elem = soup.select_one("time.article__timestamp")
        published_date = None
        if time_elem and time_elem.has_attr("datetime"):
            try:
                published_date = datetime.fromisoformat(str(time_elem["datetime"]))
            except Exception:
                published_date = None

        # Extract image URL
        img_elem = soup.select_one("figure.article__featured-image img")
        image_url = (
            str(img_elem.get("src")) if img_elem and img_elem.get("src") else None
        )

        # Extract category (first category link)
        cat_elem = soup.select_one("a.article__section")
        category = cat_elem.get_text(strip=True) if cat_elem else "technology"

        # Extract content
        content_elem = soup.select_one("div.entry-content")
        content = (
            content_elem.get_text(strip=True)
            if content_elem
            else "No content available."
        )

        title = str(title) if title else "No title found"

        return base.NewsArticle(
            title=title,
            url=url,
            description=description,
            published_date=(
                published_date.strftime("%Y-%m-%d %H:%M:%S") if published_date else None
            ),
            source=self.source_name,
            image_url=image_url,
            category=category,
            content=content,  # Add content field with parsed content
        )


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
