"""
Tests for the news scrapers.
"""

import json
import os

import pytest
from dotenv import load_dotenv

from scrapers.cnn import CNNScraper
from scrapers.manager import ScraperManager
from scrapers.techcrunch import TechCrunchScraper

# Load environment variables for API keys if needed
_ = load_dotenv()


def test_techcrunch_scraper():
    """Test the TechCrunch scraper with real data."""
    from scrapers.techcrunch import TechCrunchScraper

    print("\n[DEBUG] Starting TechCrunch scraper test...")

    # Create an output directory if it doesn't exist
    output_dir = "test_results"
    os.makedirs(output_dir, exist_ok=True)
    print(f"[DEBUG] Created output directory: {output_dir}")

    scraper = TechCrunchScraper()
    print("[DEBUG] Initialized TechCrunchScraper")

    # Test fetching articles
    print("[DEBUG] Fetching TechCrunch articles (max: 3)...")
    articles = scraper.fetch_articles(category="latest", max_articles=3)
    print(f"[DEBUG] Fetched {len(articles)} TechCrunch articles")

    # Write the articles to a JSON file for inspection
    output_file = os.path.join(output_dir, "techcrunch_articles.json")
    with open(output_file, "w") as f:
        # Convert any non-serializable objects to strings
        serializable_articles = []
        for article in articles:
            serializable_article = {}
            for key, value in article.items():
                if isinstance(value, (str, int, float, bool, type(None))):
                    serializable_article[key] = value
                else:
                    serializable_article[key] = str(value)
            serializable_articles.append(serializable_article)

        json.dump(serializable_articles, f, indent=2)
    print(f"[DEBUG] Saved TechCrunch articles to {output_file}")

    # Verify we got some articles
    assert len(articles) > 0
    print(f"[DEBUG] Verification: Got {len(articles)} articles")

    # Check article structure
    for i, article in enumerate(articles):
        assert "title" in article
        assert "url" in article
        assert "source" in article
        assert article["source"] == "TechCrunch"
        print(f"[DEBUG] Article {i+1} structure verified: {article['title']}")

    # Test fetching an article by URL if we have at least one
    if articles:
        print(f"[DEBUG] Fetching detailed article from URL: {articles[0]['url']}")
        detailed_article = scraper.fetch_article_by_url(articles[0]["url"])
        print("[DEBUG] Successfully fetched detailed article")

        # Write the detailed article to a JSON file
        output_file = os.path.join(output_dir, "techcrunch_detailed_article.json")
        with open(output_file, "w") as f:
            # Convert to serializable format
            serializable_article = {}
            for key, value in detailed_article.items():
                if isinstance(value, (str, int, float, bool, type(None))):
                    serializable_article[key] = value
                else:
                    serializable_article[key] = str(value)

            json.dump(serializable_article, f, indent=2)
        print(f"[DEBUG] Saved detailed article to {output_file}")

        # Verify the detailed article has content
        assert "content" in detailed_article
        assert detailed_article["content"] is not None
        assert len(detailed_article["content"]) > 100  # Should have substantial content
        print(
            f"[DEBUG] Verified detailed article content (length: {len(detailed_article['content'])})"
        )
    print("[DEBUG] TechCrunch scraper test completed successfully")


def test_cnn_scraper():
    """Test the CNN scraper with real data."""
    from scrapers.cnn import CNNScraper

    print("\n[DEBUG] Starting CNN scraper test...")

    # Create an output directory if it doesn't exist
    output_dir = "test_results"
    os.makedirs(output_dir, exist_ok=True)
    print(f"[DEBUG] Created output directory: {output_dir}")

    scraper = CNNScraper()
    print("[DEBUG] Initialized CNNScraper")

    # Test fetching articles
    print("[DEBUG] Fetching CNN articles (max: 3)...")
    articles = scraper.fetch_articles(category="latest", max_articles=3)
    print(f"[DEBUG] Fetched {len(articles)} CNN articles")

    # Write the articles to a JSON file for inspection
    output_file = os.path.join(output_dir, "cnn_articles.json")
    with open(output_file, "w") as f:
        # Convert any non-serializable objects to strings
        serializable_articles = []
        for article in articles:
            serializable_article = {}
            for key, value in article.items():
                if isinstance(value, (str, int, float, bool, type(None))):
                    serializable_article[key] = value
                else:
                    serializable_article[key] = str(value)
            serializable_articles.append(serializable_article)

        json.dump(serializable_articles, f, indent=2)
    print(f"[DEBUG] Saved CNN articles to {output_file}")

    # Verify we got some articles
    assert len(articles) > 0
    print(f"[DEBUG] Verification: Got {len(articles)} articles")

    # Check article structure
    for i, article in enumerate(articles):
        assert "title" in article
        assert "url" in article
        assert "source" in article
        assert article["source"] == "CNN"
        print(f"[DEBUG] Article {i+1} structure verified: {article['title']}")

    # Test fetching an article by URL if we have at least one
    if articles:
        print(f"[DEBUG] Fetching detailed article from URL: {articles[0]['url']}")
        detailed_article = scraper.fetch_article_by_url(articles[0]["url"])
        print("[DEBUG] Successfully fetched detailed article")

        # Write the detailed article to a JSON file
        output_file = os.path.join(output_dir, "cnn_detailed_article.json")
        with open(output_file, "w") as f:
            # Convert to serializable format
            serializable_article = {}
            for key, value in detailed_article.items():
                if isinstance(value, (str, int, float, bool, type(None))):
                    serializable_article[key] = value
                else:
                    serializable_article[key] = str(value)

            json.dump(serializable_article, f, indent=2)
        print(f"[DEBUG] Saved detailed article to {output_file}")

        # Verify the detailed article has content
        assert "content" in detailed_article
        assert detailed_article["content"] is not None
        print(f"[DEBUG] Verified detailed article content")
    print("[DEBUG] CNN scraper test completed successfully")


def test_scraper_manager():
    """Test the scraper manager with real data."""
    from scrapers.manager import ScraperManager

    print("\n[DEBUG] Starting scraper manager test...")

    # Create an output directory if it doesn't exist
    output_dir = "test_results"
    os.makedirs(output_dir, exist_ok=True)
    print(f"[DEBUG] Created output directory: {output_dir}")

    manager = ScraperManager()
    print("[DEBUG] Initialized ScraperManager")

    # Test getting available sources
    print("[DEBUG] Getting available sources...")
    sources = manager.get_available_sources()
    print(f"[DEBUG] Available sources: {sources}")

    # Test getting available categories
    print("[DEBUG] Getting available categories...")
    categories = manager.get_available_categories()
    print(f"[DEBUG] Available categories: {categories}")

    # Write sources and categories to a JSON file
    output_file = os.path.join(output_dir, "scraper_manager_info.json")
    with open(output_file, "w") as f:
        json.dump(
            {
                "sources": sources,
                "categories": {source: cats for source, cats in categories.items()},
            },
            f,
            indent=2,
        )
    print(f"[DEBUG] Saved scraper manager info to {output_file}")

    assert "techcrunch" in sources
    assert "cnn" in sources
    assert len(categories["techcrunch"]) > 0
    assert len(categories["cnn"]) > 0
    print("[DEBUG] Verified sources and categories")

    # Test fetching headlines
    print("[DEBUG] Fetching headlines (max 2 per source)...")
    articles = manager.fetch_headlines(max_articles_per_source=2)
    print(f"[DEBUG] Fetched {len(articles)} headline articles")

    # Write articles to a JSON file
    output_file = os.path.join(output_dir, "scraper_manager_articles.json")
    with open(output_file, "w") as f:
        # Convert to serializable format
        serializable_articles = []
        for article in articles:
            serializable_article = {}
            for key, value in article.items():
                if isinstance(value, (str, int, float, bool, type(None))):
                    serializable_article[key] = value
                else:
                    serializable_article[key] = str(value)
            serializable_articles.append(serializable_article)

        json.dump(serializable_articles, f, indent=2)
    print(f"[DEBUG] Saved headline articles to {output_file}")

    assert len(articles) > 0
    print(f"[DEBUG] Verification: Got {len(articles)} headline articles")

    # Test organizing by category
    print("[DEBUG] Organizing articles by category...")
    by_category = manager.organize_by_category(articles)
    print(f"[DEBUG] Categories found in articles: {list(by_category.keys())}")

    # Print number of articles in each category
    for category, category_articles in by_category.items():
        print(f"[DEBUG] Category '{category}': {len(category_articles)} articles")

    print("[DEBUG] Scraper manager test completed successfully")
