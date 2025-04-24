"""
Tests for the news fetcher module.
"""

import os

import pytest
from dotenv import load_dotenv

import news_fetcher
from scrapers.base import NewsArticle

# Load environment variables for API keys
_ = load_dotenv()


def test_fetch_initial_article_list():
    """Test the fetch_initial_article_list function with real data."""
    print("\n[DEBUG] Starting test_fetch_initial_article_list...")

    # Call the function
    print(
        "[DEBUG] Calling fetch_initial_article_list with category: technology, max: 5"
    )
    articles = news_fetcher.fetch_initial_article_list(["technology"], 5)
    print(f"[DEBUG] Fetched {len(articles)} initial articles")

    # Verify the result
    assert isinstance(articles, list)
    assert len(articles) > 0
    print(f"[DEBUG] Verification: Got {len(articles)} articles")

    # Check article structure
    for i, article in enumerate(articles):
        assert "title" in article
        assert "url" in article
        assert "source" in article
        print(
            f"[DEBUG] Article {i+1} structure verified: {article['title']} from {article['source']}"
        )

    print("[DEBUG] test_fetch_initial_article_list completed successfully")


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OpenAI API key not found in environment variables",
)
def test_fetch_article_details(sample_news_articles):
    """Test the fetch_article_details function with real data."""
    print("\n[DEBUG] Starting test_fetch_article_details...")

    # Create an article that we know the scraper can handle
    # Using a known website that our scrapers support
    tech_article: NewsArticle = {
        "title": "Test Article",
        "url": "https://techcrunch.com/",  # Just use the homepage as a test
        "source": "TechCrunch",
        "description": "Test description",
        "category": "technology",
        "published_date": None,
        "image_url": None,
        "content": None,
    }
    print(
        f"[DEBUG] Created test article: {tech_article['title']} from {tech_article['source']}"
    )

    # Call the function
    print("[DEBUG] Calling fetch_article_details...")
    detailed_articles = news_fetcher.fetch_article_details([tech_article])
    print(f"[DEBUG] Fetched {len(detailed_articles)} detailed articles")

    # Verify the result
    assert isinstance(detailed_articles, list)
    assert len(detailed_articles) > 0
    print(f"[DEBUG] Verification: Got {len(detailed_articles)} detailed articles")

    # The content might not be exactly the article content since we're using the homepage,
    # but it should fetch something
    assert "content" in detailed_articles[0]
    content_length = (
        len(detailed_articles[0]["content"]) if detailed_articles[0]["content"] else 0
    )
    print(f"[DEBUG] Verified article has content field (length: {content_length})")

    print("[DEBUG] test_fetch_article_details completed successfully")


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OpenAI API key not found in environment variables",
)
def test_fetch_top_news():
    """Test the fetch_top_news function with real data."""
    print("\n[DEBUG] Starting test_fetch_top_news...")

    # Call the function
    print("[DEBUG] Calling fetch_top_news with category: technology, max: 3")
    result = news_fetcher.fetch_top_news(["technology"], 3)
    print(
        f"[DEBUG] fetch_top_news result status: {'success' if result.get('success') else 'failure'}"
    )

    # Verify the result structure
    assert isinstance(result, dict)
    assert "success" in result
    print(
        f"[DEBUG] Verification: Result is a dict with 'success' key: {result['success']}"
    )

    # If successful, check the news data
    if result["success"]:
        assert "news" in result
        assert isinstance(result["news"], list)
        assert len(result["news"]) > 0
        print(f"[DEBUG] Got {len(result['news'])} news articles")

        # Check article structure
        for i, article in enumerate(result["news"]):
            assert "title" in article
            assert "url" in article
            assert "source" in article
            # Should have content if successful
            assert "content" in article
            print(
                f"[DEBUG] Article {i+1} structure verified: {article['title']} from {article['source']}"
            )
    else:
        print(
            f"[DEBUG] News fetch failed with message: {result.get('message', 'No message')}"
        )

    print("[DEBUG] test_fetch_top_news completed successfully")
