"""
Manager for all news scrapers.
Provides a unified interface for fetching news from multiple sources.
"""

import logging

from . import base, cnn, techcrunch

# Configure logging
logger = logging.getLogger(__name__)


class ScraperManager:
    """Manager class for coordinating multiple news scrapers."""

    def __init__(self):
        """Initialize the scraper manager with all available scrapers."""
        # Dictionary to hold all scraper instances, keyed by source name
        self.scrapers: dict[str, base.NewsScraper] = {
            "techcrunch": techcrunch.TechCrunchScraper(),
            "cnn": cnn.CNNScraper(),
        }

    def get_available_sources(self) -> list[str]:
        """Get list of available news sources."""
        # Return the keys of the scrapers dictionary, which are the source names
        return list(self.scrapers.keys())

    def get_available_categories(
        self, source: str | None = None
    ) -> dict[str, list[str]]:
        """
        Get available categories for all sources or a specific source.

        Args:
            source: Specific source to get categories for, or None for all sources

        Returns:
            Dictionary mapping source names to available categories
        """
        # If a specific source is provided and exists, return its categories
        if source and source in self.scrapers:
            return {source: self.scrapers[source].get_available_categories()}

        # Otherwise, return categories for all sources
        return {
            source_name: scraper.get_available_categories()
            for source_name, scraper in self.scrapers.items()
        }

    def fetch_headlines(
        self,
        sources: list[str] | None = None,
        categories: list[str] | None = None,
        max_articles_per_source: int = 10,
    ) -> list[base.NewsArticle]:
        """
        Fetch only headlines and basic info (no full content) from sources.

        Args:
            sources: List of sources to fetch from, or None for all sources
            categories: List of categories to fetch, or None for default categories
            max_articles_per_source: Maximum articles per source and category

        Returns:
            List of articles
        """
        # Use all available sources if none are specified
        if not sources:
            sources = list(self.scrapers.keys())

        # Use a default category if none are specified
        if not categories:
            categories = ["default"]

        # Initialize results list
        results: list[base.NewsArticle] = []
        # Track seen URLs to avoid duplicates
        seen_urls: set[str] = set()

        # Iterate over each source
        for source_name in sources:
            if source_name not in self.scrapers:
                logger.warning(f"Source {source_name} not found, skipping...")
                continue

            scraper = self.scrapers[source_name]

            # Fetch articles for each category
            for category in categories:
                # Get headlines without fetching full content
                articles = scraper.fetch_articles(
                    category=category, max_articles=max_articles_per_source
                )

                # Add to our combined list, skipping duplicates
                for article in articles:
                    url = article["url"]
                    if url not in seen_urls:
                        seen_urls.add(url)
                        results.append(article)
                    else:
                        logger.info(f"Skipping duplicate article: {article['title']}")

        return results

    def fetch_detailed_content(
        self, articles: list[base.NewsArticle]
    ) -> list[base.NewsArticle]:
        """
        Fetch detailed content for articles that already have basic info.

        Args:
            articles: List of articles with basic info

        Returns:
            List of articles with full content
        """
        logger.info(f"Fetching detailed content for {len(articles)} articles")
        # Initialize results list
        detailed_articles: list[base.NewsArticle] = []

        # Group articles by source for more efficient processing
        articles_by_source: dict[str, list[base.NewsArticle]] = {}
        for article in articles:
            source = article.get("source", "")
            if source not in articles_by_source:
                articles_by_source[source] = []
            articles_by_source[source].append(article)

        # Iterate over each source and its articles
        for source_name, source_articles in articles_by_source.items():
            # Find the appropriate scraper based on source
            scraper = None
            for scraper_name, scraper_instance in self.scrapers.items():
                if (
                    scraper_name.lower() in source_name.lower()
                    or source_name.lower() in scraper_name.lower()
                ):
                    scraper = scraper_instance
                    break

            if not scraper:
                # If we can't find a matching scraper, keep the original articles
                detailed_articles.extend(source_articles)
                continue

            # Fetch detailed content for each article with the appropriate scraper
            for article in source_articles:
                try:
                    # Use the scraper to fetch full article details
                    detailed: base.NewsArticle = scraper.fetch_article_by_url(
                        article["url"]
                    )
                    detailed_articles.append(detailed)
                except Exception as e:
                    logger.error(
                        f"Error fetching detailed content for {article['url']}: {str(e)}"
                    )
                    # Keep the original article if fetching details fails
                    detailed_articles.append(article)

        return detailed_articles

    def fetch_news(
        self,
        sources: list[str] | None = None,
        categories: list[str] | None = None,
        max_articles_per_source: int = 5,
    ) -> list[base.NewsArticle]:
        """
        Fetch news from multiple sources and categories with full content.
        This is a convenience method that calls fetch_headlines followed by fetch_detailed_content.

        Args:
            sources: List of sources to fetch from, or None for all sources
            categories: List of categories to fetch, or None for default categories
            max_articles_per_source: Maximum articles per source and category

        Returns:
            List of articles with full content
        """
        # First fetch headlines
        headlines = self.fetch_headlines(sources, categories, max_articles_per_source)

        # Then fetch detailed content for those headlines
        return self.fetch_detailed_content(headlines)

    def organize_by_category(
        self, news_data: list[base.NewsArticle]
    ) -> dict[str, list[base.NewsArticle]]:
        """
        Organize news data by category.

        Args:
            news_data: List of articles

        Returns:
            Dictionary of news organized by category
        """
        # Initialize dictionary to hold articles organized by category
        by_category: dict[str, list[base.NewsArticle]] = {}
        # Track seen URLs to avoid duplicates within categories
        seen_urls: set[str] = set()

        # Iterate over each article
        for article in news_data:
            # Extract the category from the article itself
            category = article.get("category")
            url = article["url"]

            # Skip if we've already seen this URL
            if url in seen_urls:
                continue

            seen_urls.add(url)

            # Default to "uncategorized" if no category
            if not category:
                category = "uncategorized"

            # Initialize the category list if it doesn't exist
            if category not in by_category:
                by_category[category] = []

            # Add the article to the appropriate category
            by_category[category].append(article)

        return by_category


# Allow running the scraper manager standalone for testing
if __name__ == "__main__":
    import sys

    # Create scraper manager
    manager = ScraperManager()

    # Parse command line arguments
    selected_sources = sys.argv[1:] if len(sys.argv) > 1 else None

    # Print available sources
    logger.info(f"Available sources: {', '.join(manager.get_available_sources())}")

    # Print available categories for each source
    available_categories = manager.get_available_categories()
    logger.info("Available categories by source:")
    for src_name, cats in available_categories.items():
        logger.info(f"  {src_name}: {', '.join(cats)}")

    # Fetch news using specific sources or all sources
    logger.info(f"Fetching news from {selected_sources or 'all'} sources...")
    news = manager.fetch_headlines(sources=selected_sources, max_articles_per_source=5)

    # Print results
    logger.info(f"Total articles: {len(news)}")
    for i, article in enumerate(news, 1):
        logger.info(f"{i}. {article['title']} [{article['source']}]")
        logger.info(f"   URL: {article['url']}")
        logger.info(f"   Date: {article.get('published_date', 'No date')}")
        logger.info(f"   Category: {article.get('category', 'No category')}")

    # Organize by category and display
    logger.info("=== ARTICLES BY CATEGORY ===")
    by_category = manager.organize_by_category(news)
    for cat_name, cat_articles in by_category.items():
        logger.info(f"Category: {cat_name} ({len(cat_articles)} articles)")
        for i, article in enumerate(cat_articles, 1):
            logger.info(f"  {i}. {article['title']} [{article['source']}]")
