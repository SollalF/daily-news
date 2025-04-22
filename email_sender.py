"""
Module for sending daily news emails using SendGrid API.
"""

import os
from datetime import datetime
from typing import TypedDict

import pytz
import scrapers.base as base  # pyright: ignore[reportImplicitRelativeImport]
from python_http_client.client import Response
from sendgrid import SendGridAPIClient  # pyright: ignore[reportMissingTypeStubs]
from sendgrid.helpers.mail import Mail  # pyright: ignore[reportMissingTypeStubs]


class EmailResponse(TypedDict):
    """Response type for email sending operations."""

    statusCode: int
    body: str


def send_news_email(
    news_data: dict[str, list[base.NewsArticle]],
    to_emails: list[str],
    news_summary: str,
) -> EmailResponse:
    """
    Send daily news digest via email using SendGrid

    Args:
        news_data: Dictionary of news articles by category
        to_emails: List of recipient email addresses
        news_summary: Summary of the news to include in the email

    Returns:
        EmailResponse with status code and result message
    """
    key = os.getenv("SENDGRID_API_KEY")
    if not key:
        raise ValueError("SendGrid API key not found in environment variables")

    # Create message
    hk_tz = pytz.timezone("Asia/Hong_Kong")
    current_date = datetime.now(hk_tz).strftime("%Y-%m-%d")

    # Create HTML content for email
    html_content = create_email_html(news_data, current_date, news_summary)

    sg: SendGridAPIClient = SendGridAPIClient(key)
    message: Mail = Mail(
        from_email="support@goodclass.ai",
        to_emails=to_emails,
        subject=f"Daily News Digest - {current_date}",
        html_content=html_content,
    )
    response: Response = sg.send(message)

    # Log the response status for debugging purposes
    print(f"Email sent with status code: {response.status_code}")

    return {
        "statusCode": response.status_code,
        "body": ("success" if response.status_code == 202 else "email failed to send"),
    }


def create_email_html(
    news_data: dict[str, list[base.NewsArticle]], date: str, summary: str
) -> str:
    """
    Create HTML content for news email.

    Args:
        news_data: Dictionary of news articles by category
        date: Current date string
        summary: Summary of the news to include in the email

    Returns:
        Formatted HTML content for email
    """
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333;">Daily News Digest - {date}</h2>
        <p style="color: #555; line-height: 1.5;">{summary}</p>
        <p style="color: #555; line-height: 1.5;">Here are today's top news stories:</p>
    """

    # Add news by category
    for category, articles in news_data.items():
        if not articles:
            continue

        # Add category heading
        html += f"""
        <h3 style="color: #333; text-transform: capitalize; margin-top: 25px; border-bottom: 1px solid #eee; padding-bottom: 8px;">
            {category} News
        </h3>
        """

        # Add articles
        for article in articles:
            html += f"""
            <div style="margin-bottom: 20px;">
                <h4 style="margin-bottom: 5px;">
                    <a href="{article['url']}" style="color: #0066cc; text-decoration: none;">
                        {article['title']}
                    </a>
                </h4>
                <p style="color: #777; font-size: 12px; margin-top: 0;">
                    {article['source']} • {article['published_date']}
                </p>
                <p style="color: #555; margin-top: 8px;">
                    {(article['content'][:100] if article['content'] else 'No content available.')}
                </p>
            </div>
            """

    # Add footer
    html += """
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #999; font-size: 12px;">
            <p>This is an automated daily news digest by goodclass.ai.</p>
            <p>To unsubscribe from these emails, please contact your administrator.</p>
        </div>
    </div>
    """

    return html


if __name__ == "__main__":
    from dotenv import load_dotenv

    _ = load_dotenv()

    # Sample data for testing
    sample_news_data: dict[str, list[base.NewsArticle]] = {
        "technology": [
            {
                "title": "AI Breakthrough",
                "url": "https://example.com/ai-breakthrough",
                "source": "Tech News",
                "published_date": "2023-10-01",
                "description": "A new AI model has achieved state-of-the-art results.",
                "image_url": "https://example.com/ai-breakthrough.jpg",
                "category": "technology",
                "content": "A new AI model has achieved state-of-the-art results.",
            }
        ],
        "sports": [
            {
                "title": "Local Team Wins Championship",
                "url": "https://example.com/local-team-wins",
                "source": "Sports Daily",
                "published_date": "2023-10-01",
                "description": "The local team has won the championship in a thrilling final.",
                "image_url": "https://example.com/local-team-wins.jpg",
                "category": "sports",
                "content": "The local team has won the championship in a thrilling final.",
            }
        ],
    }

    # Read email recipients from environment variable
    email_recipients = ["sollal@solomongp.com"]

    # Call the function with sample data
    response = send_news_email(
        sample_news_data, email_recipients, "This is a summary of the news"
    )
    print("Email send response:", response)
