"""
Tests for the email sender module.
"""

import os

import pytest
from dotenv import load_dotenv

import email_sender

# Load environment variables for API keys
_ = load_dotenv()

# Skip tests if no SendGrid API key is available
pytestmark = pytest.mark.skipif(
    not os.getenv("SENDGRID_API_KEY"),
    reason="SendGrid API key not found in environment variables",
)


def test_create_email_html(sample_news_articles):
    """Test the create_email_html function."""
    print("\n[DEBUG] Starting test_create_email_html...")

    # Set up test data
    date = "2023-10-15"
    summary = "This is a test summary."
    print(f"[DEBUG] Test data: date={date}, summary={summary}")
    print(f"[DEBUG] Input: {len(sample_news_articles)} articles")

    # Call the function
    print("[DEBUG] Calling create_email_html...")
    html = email_sender.create_email_html(sample_news_articles, date, summary)
    print(f"[DEBUG] Generated HTML length: {len(html)} characters")

    # Verify the result contains key elements
    assert date in html
    assert summary in html
    assert "Daily News Digest" in html
    assert "AI Breakthrough" in html
    assert "New Programming Language" in html
    assert "Tech Company Layoffs" in html
    print("[DEBUG] Verified all key elements are present in HTML")
    print("[DEBUG] test_create_email_html completed successfully")


def test_send_news_email(sample_news_articles):
    """Test the send_news_email function with real API call."""
    print("\n[DEBUG] Starting test_send_news_email...")

    # Only run if we have API credentials and a real recipient email
    if not os.getenv("SENDGRID_API_KEY"):
        print("[DEBUG] Skipping test: No SendGrid API key available")
        pytest.skip("No SendGrid API key available")

    # Replace this with a real test email address
    # For safety, default to not sending if no test email is specified
    test_email = os.getenv("TEST_EMAIL")
    if not test_email:
        print("[DEBUG] Skipping test: No test email address available")
        pytest.skip("No test email address available")

    # Set up test data
    to_emails = [test_email]
    news_summary = "This is a test summary for integration testing."
    print(
        f"[DEBUG] Test data: recipient={test_email}, summary length={len(news_summary)}"
    )
    print(f"[DEBUG] Input: {len(sample_news_articles)} articles")

    # Call the function
    print("[DEBUG] Calling send_news_email to send actual email...")
    result = email_sender.send_news_email(sample_news_articles, to_emails, news_summary)
    print(f"[DEBUG] Email send result: statusCode={result.get('statusCode')}")

    # Verify the result
    assert "statusCode" in result
    assert "body" in result
    print("[DEBUG] Verified result has required fields")

    # Note: This might actually send an email, so use carefully
    print(f"[DEBUG] Email send result full details: {result}")
    print("[DEBUG] test_send_news_email completed successfully")
