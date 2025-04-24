"""
Tests for the scraper manager.
"""

from unittest.mock import MagicMock, patch

import pytest

from scrapers.base import NewsArticle, NewsScraper
from scrapers.manager import ScraperManager


@pytest.fixture
def mock_scraper():
    """Create a mock scraper."""
    mock_scraper = MagicMock(spec=NewsScraper)

    # Mock the fetch_articles method
    mock_scraper.fetch_articles.return_value = [
        {
            "title": "Test Article",
            "url": "https://example.com/test",
            "source": "Test Source",
            "description": "Test description",
            "published_date": "2023-10-01",
            "category": "test",
            "image_url": "https://example.com/image.jpg",
            "content": None,
        }
    ]

    # Mock the fetch_article_by_url method
    mock_scraper.fetch_article_by_url.return_value = {
        "title": "Test Article",
        "url": "https://example.com/test",
        "source": "Test Source",
        "description": "Test description",
        "published_date": "2023-10-01",
        "category": "test",
        "image_url": "https://example.com/image.jpg",
        "content": "This is the full content of the test article.",
    }

    # Mock the get_available_categories method
    mock_scraper.get_available_categories.return_value = ["test", "news"]

    return mock_scraper


@pytest.fixture
def manager_with_mock_scrapers(mock_scraper):
    """Create a scraper manager with mock scrapers."""
    with patch.object(ScraperManager, "__init__", lambda self: None):
        manager = ScraperManager()
        manager.scrapers = {"test_source": mock_scraper}
        yield manager


def test_get_available_sources(manager_with_mock_scrapers):
    """Test the get_available_sources method."""
    print("\n[DEBUG] Starting test_get_available_sources...")

    print("[DEBUG] Calling get_available_sources...")
    sources = manager_with_mock_scrapers.get_available_sources()
    print(f"[DEBUG] Available sources: {sources}")

    assert sources == ["test_source"]
    print("[DEBUG] Verified sources match expected output")
    print("[DEBUG] test_get_available_sources completed successfully")


def test_get_available_categories(manager_with_mock_scrapers, mock_scraper):
    """Test the get_available_categories method."""
    print("\n[DEBUG] Starting test_get_available_categories...")

    # Test with no source specified
    print("[DEBUG] Calling get_available_categories with no source specified...")
    categories = manager_with_mock_scrapers.get_available_categories()
    print(f"[DEBUG] Available categories: {categories}")

    assert categories == {"test_source": ["test", "news"]}
    print("[DEBUG] Verified categories match expected output (no source)")

    # Test with a specific source
    print("[DEBUG] Calling get_available_categories with source 'test_source'...")
    categories = manager_with_mock_scrapers.get_available_categories("test_source")
    print(f"[DEBUG] Available categories for test_source: {categories}")

    assert categories == {"test_source": ["test", "news"]}
    print("[DEBUG] Verified categories match expected output (with source)")
    print("[DEBUG] test_get_available_categories completed successfully")


def test_fetch_headlines(manager_with_mock_scrapers, mock_scraper):
    """Test the fetch_headlines method."""
    print("\n[DEBUG] Starting test_fetch_headlines...")

    # Test with default parameters
    print("[DEBUG] Calling fetch_headlines with default parameters...")
    articles = manager_with_mock_scrapers.fetch_headlines()
    print(f"[DEBUG] Fetched {len(articles)} headline articles")

    assert len(articles) == 1
    assert articles[0]["title"] == "Test Article"
    mock_scraper.fetch_articles.assert_called_once()
    print("[DEBUG] Verified articles and mock was called once")
    print("[DEBUG] test_fetch_headlines completed successfully")


def test_fetch_detailed_content(manager_with_mock_scrapers, mock_scraper):
    """Test the fetch_detailed_content method."""
    print("\n[DEBUG] Starting test_fetch_detailed_content...")

    # Set up test data - mock articles with source matching our mock scraper
    test_articles = [
        {
            "title": "Test Article 1",
            "url": "https://example.com/test1",
            "source": "test_source",  # Match the key in manager.scrapers
            "description": "This is test article 1",
            "published_date": "2023-10-01",
            "category": "test",
            "image_url": "https://example.com/image1.jpg",
            "content": None,
        },
        {
            "title": "Test Article 2",
            "url": "https://example.com/test2",
            "source": "test_source",  # Match the key in manager.scrapers
            "description": "This is test article 2",
            "published_date": "2023-10-02",
            "category": "test",
            "image_url": "https://example.com/image2.jpg",
            "content": None,
        },
    ]

    print(
        f"[DEBUG] Created {len(test_articles)} test articles with source='test_source'"
    )

    # Test the method
    print("[DEBUG] Calling fetch_detailed_content...")
    detailed_articles = manager_with_mock_scrapers.fetch_detailed_content(test_articles)
    print(f"[DEBUG] Fetched {len(detailed_articles)} detailed articles")

    # Verify results
    assert len(detailed_articles) == len(test_articles)
    mock_scraper.fetch_article_by_url.assert_called()
    print(
        f"[DEBUG] Verified result count matches input count: {len(detailed_articles)}"
    )
    print(
        f"[DEBUG] Verified fetch_article_by_url was called {mock_scraper.fetch_article_by_url.call_count} times"
    )
    print("[DEBUG] test_fetch_detailed_content completed successfully")


def test_fetch_news(manager_with_mock_scrapers):
    """Test the fetch_news method."""
    print("\n[DEBUG] Starting test_fetch_news...")

    # Mock the fetch_headlines and fetch_detailed_content methods
    with patch.object(manager_with_mock_scrapers, "fetch_headlines") as mock_headlines:
        with patch.object(
            manager_with_mock_scrapers, "fetch_detailed_content"
        ) as mock_detailed:
            # Set up the mocks
            mock_headlines.return_value = [
                {"title": "Test Article", "url": "https://example.com/test"}
            ]
            mock_detailed.return_value = [
                {
                    "title": "Test Article",
                    "url": "https://example.com/test",
                    "content": "Full content",
                }
            ]
            print(
                "[DEBUG] Configured mocks for fetch_headlines and fetch_detailed_content"
            )

            # Call the method
            print("[DEBUG] Calling fetch_news...")
            result = manager_with_mock_scrapers.fetch_news()
            print(f"[DEBUG] Fetched {len(result)} news articles")

            # Verify results
            assert len(result) == 1
            assert result[0]["content"] == "Full content"
            mock_headlines.assert_called_once()
            mock_detailed.assert_called_once()
            print("[DEBUG] Verified results and mock calls")
            print("[DEBUG] test_fetch_news completed successfully")


def test_organize_by_category(manager_with_mock_scrapers):
    """Test the organize_by_category method."""
    print("\n[DEBUG] Starting test_organize_by_category...")

    # Create sample news articles directly in the test
    test_articles = [
        {
            "title": "AI Breakthrough",
            "url": "https://example.com/ai-breakthrough",
            "source": "Tech News",
            "description": "A new AI model has achieved state-of-the-art results.",
            "published_date": "2023-10-01",
            "image_url": "https://example.com/ai.jpg",
            "category": "ai",
            "content": "A new AI model has achieved state-of-the-art results.",
        },
        {
            "title": "New Programming Language",
            "url": "https://example.com/new-language",
            "source": "Dev Weekly",
            "description": "A new programming language promises better performance.",
            "published_date": "2023-10-02",
            "image_url": "https://example.com/lang.jpg",
            "category": "technology",
            "content": "A new programming language promises better performance.",
        },
        {
            "title": "Tech Company Layoffs",
            "url": "https://example.com/layoffs",
            "source": "Business Tech",
            "description": "Major tech company announces layoffs.",
            "published_date": "2023-10-03",
            "image_url": "https://example.com/business.jpg",
            "category": "business",
            "content": "Major tech company announces layoffs.",
        },
    ]

    print(f"[DEBUG] Input: {len(test_articles)} articles")

    # Call the method
    print("[DEBUG] Calling organize_by_category...")
    categorized = manager_with_mock_scrapers.organize_by_category(test_articles)
    print(f"[DEBUG] Result: {len(categorized)} categories: {list(categorized.keys())}")

    # Verify results
    assert "ai" in categorized
    assert "technology" in categorized
    assert "business" in categorized
    assert len(categorized["ai"]) == 1
    assert categorized["ai"][0]["title"] == "AI Breakthrough"

    # Print detailed results
    for category, articles in categorized.items():
        print(f"[DEBUG] Category '{category}': {len(articles)} articles")
        for i, article in enumerate(articles):
            print(f"[DEBUG]   - Article {i+1}: {article['title']}")

    print("[DEBUG] Verified all expected categories and article assignments")
    print("[DEBUG] test_organize_by_category completed successfully")
