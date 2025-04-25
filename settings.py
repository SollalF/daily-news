"""
Central configuration settings for the daily news application.
Contains all configurable parameters, prompts, and default values.
"""

import os
from typing import Any

from pydantic import BaseModel, EmailStr, Field, validator


class EmailSettings(BaseModel):
    """Email-related settings."""

    from_address: EmailStr = Field(
        default="support@goodclass.ai", description="Email sender address"
    )
    subject_template: str = Field(
        default="Daily News Digest - {date}", description="Email subject template"
    )
    recipients: list[EmailStr] = Field(
        default=["sollal@solomongp.com"], description="Default email recipients"
    )


class AISettings(BaseModel):
    """AI service settings."""

    api_key: str = Field(default="", description="OpenAI API key")
    model: str = Field(default="gpt-4o", description="Default OpenAI model")
    system_message: str = Field(
        default="You are a helpful AI assistant.",
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

    @validator("api_key")
    def validate_api_key(cls, v: str) -> str:
        """Validate the API key."""
        if not v and os.environ.get("OPENAI_API_KEY"):
            return os.environ.get("OPENAI_API_KEY", "")
        return v


class NewsSettings(BaseModel):
    """News fetching settings."""

    categories: list[str] = Field(
        default=["latest", "ai", "technology"],
        description="Default news categories to fetch",
    )
    max_per_category: int = Field(
        default=50, description="Maximum number of news articles per category"
    )
    user_interests: str = Field(
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


class Settings(BaseModel):
    """Application settings model."""

    email: EmailSettings = Field(default_factory=EmailSettings)
    ai: AISettings = Field(default_factory=AISettings)
    news: NewsSettings = Field(default_factory=NewsSettings)

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"

        # Map specific fields to environment variables
        field_env_mapping = {"ai.api_key": "OPENAI_API_KEY"}


# Create settings instance
settings = Settings()
