"""
Central configuration settings for the daily news application.
Contains all configurable parameters, prompts, and default values.
"""

import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the directory where this settings.py file is located
SETTINGS_DIR = Path(__file__).parent.resolve()
ENV_FILE_PATH = SETTINGS_DIR / ".env"


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
- If there is a picture in the article, include it.

{user_interests}
""",
        description="Template for email summary prompt",
    )

    @field_validator("api_key")
    @classmethod
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


class LoggingSettings(BaseModel):
    """Logging configuration settings."""

    level: Literal["debug", "info", "warning", "error", "critical"] = Field(
        default="info", description="Default logging level"
    )
    log_file: str | None = Field(
        default="logs/daily-news.log",
        description="Path to log file (None for console only)",
    )
    format: str = Field(
        default="%(levelname)s - %(message)s",
        description="Log message format",
    )
    max_file_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum size of log file before rotation (in bytes)",
    )
    backup_count: int = Field(
        default=3, description="Number of backup log files to keep"
    )


class Settings(BaseSettings):
    """Application settings model."""

    # Environment variables
    SENDGRID_API_KEY: str = Field(..., description="SendGrid API key")
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")

    email: EmailSettings = Field(default_factory=EmailSettings)
    ai: AISettings = Field(default_factory=AISettings)
    news: NewsSettings = Field(default_factory=NewsSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        # Map specific fields to environment variables
        env_prefix="",
        extra="ignore",
    )

    @model_validator(mode="after")
    def map_openai_api_key(self):
        """Map OPENAI_API_KEY to ai.api_key if not already set."""
        if not self.ai.api_key and self.OPENAI_API_KEY:
            self.ai.api_key = self.OPENAI_API_KEY
        return self


# Create settings instance
settings = Settings()
