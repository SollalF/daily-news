"""
Central configuration settings for the daily news application.
Contains all configurable parameters, prompts, and default values.
"""

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Pydantic model for application settings."""

    # Default configuration
    default_categories: list[str] = Field(
        default=["latest", "ai", "technology"],
        description="Default news categories to fetch",
    )
    default_max_news_per_category: int = Field(
        default=50, description="Maximum number of news articles per category"
    )
    default_email_recipients: list[str] = Field(
        default=["sollal@solomongp.com"], description="Default email recipients"
    )

    # API Configuration
    openai_api_key: str = Field(default="", description="OpenAI API key")
    sendgrid_api_key: str = Field(default="", description="SendGrid API key")
    default_model: str = Field(default="gpt-4o", description="Default OpenAI model")

    # Email Configuration
    email_from_address: str = Field(
        default="support@goodclass.ai", description="Email sender address"
    )
    email_subject_template: str = Field(
        default="Daily News Digest - {date}", description="Email subject template"
    )

    # Default user's interests and preferences
    default_user_interests: str = Field(
        default="""
Topics of interest (in order of priority):
1. AI news, especially in education and GPT-4o image model updates
2. Important technological innovations 
3. News that would help a software engineer and product manager be more productive
4. Major scandals or security issues in tech

Please ignore news about investments, business funding, or other less relevant topics.
""",
        description="Default user interests for customizing news selection",
    )

    # OpenAI Prompts
    system_message: str = Field(
        default="""
You are a helpful AI assistant.
""",
        description="System message for OpenAI API",
    )

    article_selection_template: str = Field(
        default="""
Below is a list of news articles with their titles, descriptions, and sources.
Select the most relevant and important articles that should be fetched in more detail.

{user_interests}

Respond with a JSON array of article URLs that should be scraped in detail.
Example format:
{{ 
  "articles": [
    "https://example.com/article1",
    "https://example.com/article2",
    "https://example.com/article3"
  ] 
}}

Here are the articles:
{articles}
""",
        description="Template for article selection prompt",
    )

    email_summary_template: str = Field(
        default="""
- Summarize the following articles: {articles}.
- Output to HTML format.
- If there are highly important news to me, display a callout at the top with a short summary of these news.
- Then prioritize the articles based on my interests. 
- Do not include a ```html tag in the output.
- Always include the link to the original article.

{user_interests}
""",
        description="Template for email summary prompt",
    )

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = ""


# Create settings instance
settings = Settings()

# Export constants for backward compatibility
DEFAULT_CATEGORIES = settings.default_categories
DEFAULT_MAX_NEWS_PER_CATEGORY = settings.default_max_news_per_category
DEFAULT_EMAIL_RECIPIENTS = settings.default_email_recipients
OPENAI_API_KEY = settings.openai_api_key
SENDGRID_API_KEY = settings.sendgrid_api_key
DEFAULT_MODEL = settings.default_model
EMAIL_FROM_ADDRESS = settings.email_from_address
EMAIL_SUBJECT_TEMPLATE = settings.email_subject_template
DEFAULT_USER_INTERESTS = settings.default_user_interests
SYSTEM_MESSAGE = settings.system_message
ARTICLE_SELECTION_TEMPLATE = settings.article_selection_template
EMAIL_SUMMARY_TEMPLATE = settings.email_summary_template
