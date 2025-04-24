"""
Tests for the AI services module.
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest
from dotenv import load_dotenv

import ai_services
from scrapers.base import NewsArticle


def test_select_articles(sample_news_articles):
    """Test the select_articles function."""
    print("\n[DEBUG] Starting test_select_articles...")
    print(f"[DEBUG] Input: {len(sample_news_articles)} articles")

    # Call the function with real data
    print("[DEBUG] Calling select_articles...")
    result = ai_services.select_articles(sample_news_articles, "Test prompt")
    print(f"[DEBUG] select_articles returned {len(result)} articles")

    # Verify the result
    assert len(result) > 0
    assert all(isinstance(article, dict) for article in result)
    assert all("url" in article for article in result)
    assert all("title" in article for article in result)
    print(f"[DEBUG] Verified result contains valid articles")
    print("[DEBUG] test_select_articles completed successfully")


def test_select_articles_fallback(sample_news_articles):
    """Test the select_articles function with fallback behavior."""
    print("\n[DEBUG] Starting test_select_articles_fallback...")
    print(f"[DEBUG] Input: {len(sample_news_articles)} articles")

    # Force fallback by temporarily setting invalid API key
    with patch("openai.api_key", "invalid_key"):
        # Call the function
        print("[DEBUG] Calling select_articles with invalid API key...")
        result = ai_services.select_articles(sample_news_articles, "Test prompt")
        print(f"[DEBUG] select_articles fallback returned {len(result)} articles")

        # Verify fallback behavior
        assert len(result) == 1  # 25% of 3 articles rounded up to 1
        assert result[0] in sample_news_articles
        print(f"[DEBUG] Verified fallback result: {result[0]['title']}")
        print("[DEBUG] test_select_articles_fallback completed successfully")


def test_summarize_articles(sample_news_articles):
    """Test the summarize_articles function."""
    print("\n[DEBUG] Starting test_summarize_articles...")
    print(f"[DEBUG] Input: {len(sample_news_articles)} articles")

    # Call the function with real data
    print("[DEBUG] Calling summarize_articles...")
    result = ai_services.summarize_articles(sample_news_articles, "Test prompt")
    print(f"[DEBUG] Received summary: {result}")

    # Verify the result
    assert isinstance(result, str)
    assert len(result) > 0
    print("[DEBUG] Verified result is a non-empty string")
    print("[DEBUG] test_summarize_articles completed successfully")


def test_summarize_articles_error(sample_news_articles):
    """Test the summarize_articles function with an error."""
    print("\n[DEBUG] Starting test_summarize_articles_error...")
    print(f"[DEBUG] Input: {len(sample_news_articles)} articles")

    # Force an error by temporarily setting invalid API key
    with patch("openai.api_key", "invalid_key"):
        # Call the function and expect an exception
        print("[DEBUG] Calling summarize_articles with invalid API key...")
        with pytest.raises(ai_services.AIServiceError) as excinfo:
            ai_services.summarize_articles(sample_news_articles, "Test prompt")

        print(f"[DEBUG] Caught expected AIServiceError: {str(excinfo.value)}")
        print("[DEBUG] test_summarize_articles_error completed successfully")


def test_call_ai_api():
    """Test the call_ai_api function."""
    print("\n[DEBUG] Starting test_call_ai_api...")

    # Call the function with real data
    print("[DEBUG] Calling call_ai_api...")
    result = ai_services.call_ai_api("Give a one-word response: Hello")
    print(f"[DEBUG] Received response: {result}")

    # Verify the result
    assert isinstance(result, str)
    assert len(result) > 0
    print("[DEBUG] Verified result is a non-empty string")
    print("[DEBUG] test_call_ai_api completed successfully")


def test_call_ai_api_json():
    """Test the call_ai_api function with JSON response."""
    print("\n[DEBUG] Starting test_call_ai_api_json...")

    # Call the function with real data
    print("[DEBUG] Calling call_ai_api with json_response=True...")
    result = ai_services.call_ai_api(
        "Return a JSON object with a key named 'greeting' and value 'hello'",
        json_response=True,
    )
    print(f"[DEBUG] Received parsed JSON: {result}")

    # Verify the result
    assert isinstance(result, dict)
    assert "greeting" in result
    print("[DEBUG] Verified result is a valid JSON object")
    print("[DEBUG] test_call_ai_api_json completed successfully")
