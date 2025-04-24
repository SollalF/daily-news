"""
Tests for the daily_news.py module.
"""

import os
import sys
from http import HTTPStatus
from unittest.mock import MagicMock, patch

import pytest

# Add the parent directory to the Python path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the main function from the daily_news module
from daily_news import main


@pytest.fixture
def mock_dependencies():
    """Set up mocks for all dependencies used in the main function."""
    # Patch the EMAIL_SUMMARY_TEMPLATE to avoid the {articles} error
    with patch(
        "daily_news.EMAIL_SUMMARY_TEMPLATE",
        "Mocked summary template for {user_interests}",
    ), patch(
        "daily_news.ARTICLE_SELECTION_TEMPLATE",
        "Mocked selection template for {user_interests}",
    ), patch(
        "daily_news.fetch_top_news"
    ) as mock_fetch_top_news, patch(
        "daily_news.ai_services.select_articles"
    ) as mock_select_articles, patch(
        "daily_news.ai_services.summarize_articles"
    ) as mock_summarize_articles, patch(
        "daily_news.send_news_email"
    ) as mock_send_news_email:

        # Configure mock return values - news data should be a list of article dictionaries
        test_articles = [
            {
                "title": "Test Article 1",
                "url": "https://example.com/test1",
                "source": "Test Source",
                "description": "Test description 1",
                "category": "technology",
            },
            {
                "title": "Test Article 2",
                "url": "https://example.com/test2",
                "source": "Test Source",
                "description": "Test description 2",
                "category": "business",
            },
        ]

        mock_fetch_top_news.return_value = {
            "success": True,
            "news": test_articles,
        }
        mock_select_articles.return_value = test_articles
        mock_summarize_articles.return_value = "Summarized content"
        mock_send_news_email.return_value = {"success": True}

        yield {
            "fetch_top_news": mock_fetch_top_news,
            "select_articles": mock_select_articles,
            "summarize_articles": mock_summarize_articles,
            "send_news_email": mock_send_news_email,
            "test_articles": test_articles,
        }


class TestMain:
    """Test cases for the main function."""

    def test_main_missing_email(self, mock_dependencies):
        """Test main function with missing email recipients."""
        # This test is the only one that worked in previous runs, so let's keep it
        # for reference and add debug information

        print("\nRunning test_main_missing_email")

        args = {"to_emails": [], "categories": ["technology"]}

        try:
            result = main(args)
            print(f"Result: {result}")

            # Verify error handling
            assert result["statusCode"] == HTTPStatus.INTERNAL_SERVER_ERROR
            assert result["body"]["success"] is False
            assert "Email recipients not found" in result["body"]["message"]

            # Verify dependencies were not called
            mock_dependencies["fetch_top_news"].assert_not_called()
            mock_dependencies["select_articles"].assert_not_called()
            mock_dependencies["summarize_articles"].assert_not_called()
            mock_dependencies["send_news_email"].assert_not_called()
        except Exception as e:
            print(f"Exception: {str(e)}")
            raise

    def test_main_success(self, mock_dependencies):
        """Test main function with valid arguments."""
        print("\nRunning test_main_success")

        args = {
            "to_emails": ["test@example.com"],
            "categories": ["technology", "business"],
            "max_news_per_category": 5,
            "user_interests": "AI, Programming",
        }

        try:
            result = main(args)
            print(f"Result: {result}")

            if result["statusCode"] != HTTPStatus.OK:
                print(
                    f"Error - expected status code {HTTPStatus.OK}, got {result['statusCode']}"
                )
                if "traceback" in result["body"]:
                    print(f"Traceback: {result['body']['traceback']}")

            # Verify the result
            assert result["statusCode"] == HTTPStatus.OK
            assert result["body"]["success"] is True
            assert "News summarized and sent successfully" in result["body"]["message"]

            # Verify all dependencies were called
            mock_dependencies["fetch_top_news"].assert_called_once()
            mock_dependencies["select_articles"].assert_called_once()
            mock_dependencies["summarize_articles"].assert_called_once()
            mock_dependencies["send_news_email"].assert_called_once()

            # Print the call arguments for debugging
            print(
                f"fetch_top_news call args: {mock_dependencies['fetch_top_news'].call_args}"
            )
            print(
                f"select_articles call args: {mock_dependencies['select_articles'].call_args}"
            )
            print(
                f"summarize_articles call args: {mock_dependencies['summarize_articles'].call_args}"
            )
            print(
                f"send_news_email call args: {mock_dependencies['send_news_email'].call_args}"
            )

        except Exception as e:
            print(f"Exception: {str(e)}")
            print(
                f"Mock fetch_top_news call count: {mock_dependencies['fetch_top_news'].call_count}"
            )
            print(
                f"Mock fetch_top_news return value: {mock_dependencies['fetch_top_news'].return_value}"
            )
            if mock_dependencies["select_articles"].call_count > 0:
                print(
                    f"Mock select_articles call args: {mock_dependencies['select_articles'].call_args}"
                )
            raise

    def test_main_news_fetch_failure(self, mock_dependencies):
        """Test main function when news fetching fails."""
        print("\nRunning test_main_news_fetch_failure")

        # Configure the mock to return a failure
        mock_dependencies["fetch_top_news"].return_value = {
            "success": False,
            "error": "API error",
        }

        args = {"to_emails": ["test@example.com"], "categories": ["technology"]}

        try:
            result = main(args)
            print(f"Result: {result}")

            # Verify error handling
            assert result["statusCode"] == HTTPStatus.INTERNAL_SERVER_ERROR
            assert result["body"]["success"] is False
            assert "Failed to fetch news" in result["body"]["message"]

            # Verify only fetch_top_news was called
            mock_dependencies["fetch_top_news"].assert_called_once()
            mock_dependencies["select_articles"].assert_not_called()
            mock_dependencies["summarize_articles"].assert_not_called()
            mock_dependencies["send_news_email"].assert_not_called()
        except Exception as e:
            print(f"Exception: {str(e)}")
            print(
                f"Mock fetch_top_news call count: {mock_dependencies['fetch_top_news'].call_count}"
            )
            print(
                f"Mock fetch_top_news return value: {mock_dependencies['fetch_top_news'].return_value}"
            )
            raise
