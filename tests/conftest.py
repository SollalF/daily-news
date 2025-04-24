"""
Test configuration for pytest.
"""

import os
import sys

import pytest

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scrapers.base import NewsArticle


@pytest.fixture
def sample_news_article() -> NewsArticle:
    """Return a sample news article for testing."""
    return {
        "title": "Test Article",
        "url": "https://example.com/test-article",
        "source": "Test Source",
        "description": "This is a test article description.",
        "published_date": "2023-07-01",
        "image_url": "https://example.com/image.jpg",
        "category": "technology",
        "content": "This is the full content of the test article.",
    }


@pytest.fixture
def sample_news_articles() -> list[NewsArticle]:
    """Return a list of sample news articles for testing."""
    return [
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
