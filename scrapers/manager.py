"""
Manager for all news scrapers.
Provides a unified interface for fetching news from multiple sources.
"""

from . import base, techcrunch


class ScraperManager:
    """Manager class for coordinating multiple news scrapers."""

    def __init__(self):
        """Initialize the scraper manager with all available scrapers."""
        self.scrapers: dict[str, base.NewsScraper] = {
            "techcrunch": techcrunch.TechCrunchScraper(),
        }

    def get_available_sources(self) -> list[str]:
        """Get list of available news sources."""
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
        if source and source in self.scrapers:
            return {source: self.scrapers[source].get_available_categories()}

        return {
            source_name: scraper.get_available_categories()
            for source_name, scraper in self.scrapers.items()
        }

    def fetch_news(
        self,
        sources: list[str] | None = None,
        categories: list[str] | None = None,
        max_articles_per_source: int = 5,
    ) -> dict[str, dict[str, list[base.NewsArticle]]]:
        """
        Fetch news from multiple sources and categories.

        Args:
            sources: List of sources to fetch from, or None for all sources
            categories: List of categories to fetch, or None for default categories
            max_articles_per_source: Maximum articles per source and category

        Returns:
            Nested dictionary: {source: {category: [articles]}}
        """
        if not sources:
            sources = list(self.scrapers.keys())

        if not categories:
            categories = ["default"]

        results: dict[str, dict[str, list[base.NewsArticle]]] = {}

        for source_name in sources:
            if source_name not in self.scrapers:
                continue

            scraper = self.scrapers[source_name]
            source_results: dict[str, list[base.NewsArticle]] = {}

            for category in categories:
                articles = scraper.fetch_articles(
                    category=category, max_articles=max_articles_per_source
                )

                # Convert NewsArticle objects to dictionaries
                source_results[category] = articles

            if any(source_results.values()):
                results[source_name] = source_results

        return results

    def organize_by_category(
        self, news_data: dict[str, dict[str, list[base.NewsArticle]]]
    ) -> dict[str, list[base.NewsArticle]]:
        """
        Reorganize news data by category instead of by source.

        Args:
            news_data: News data organized by source and category

        Returns:
            Dictionary of news organized by category
        """
        by_category: dict[str, list[base.NewsArticle]] = {}

        for _, categories in news_data.items():
            for category, articles in categories.items():
                if category not in by_category:
                    by_category[category] = []

                by_category[category].extend(articles)

        return by_category


# Allow running the scraper manager standalone for testing
if __name__ == "__main__":
    import sys

    # Create scraper manager
    manager = ScraperManager()

    # Parse command line arguments
    selected_sources = sys.argv[1:] if len(sys.argv) > 1 else None

    # Print available sources
    print(f"Available sources: {', '.join(manager.get_available_sources())}")

    # Print available categories for each source
    available_categories = manager.get_available_categories()
    print("\nAvailable categories by source:")
    for src_name, cats in available_categories.items():
        print(f"  {src_name}: {', '.join(cats)}")

    # Fetch news using specific sources or all sources
    print(f"\nFetching news from {selected_sources or 'all'} sources...")
    news = manager.fetch_news(sources=selected_sources, max_articles_per_source=3)

    # Print results
    for news_source, source_data in news.items():
        print(f"\n=== {news_source.upper()} ===")
        for cat_name, cat_articles in source_data.items():
            print(f"\n  Category: {cat_name} ({len(cat_articles)} articles)")

            for i, article in enumerate(cat_articles, 1):
                print(f"    {i}. {article['title']}")
                print(f"       URL: {article['url']}")
                print(f"       Date: {article['published_date']}")

    # Display combined by category
    print("\n=== ARTICLES BY CATEGORY ===")
    combined_by_category = manager.organize_by_category(news)
    for cat_name, cat_articles in combined_by_category.items():
        print(f"\n  Category: {cat_name} ({len(cat_articles)} articles)")
        for i, article in enumerate(cat_articles[:3], 1):
            print(f"    {i}. {article['title']} [{article['source']}]")
