"""
Module for AI services and API calls.
Centralizes all interactions with OpenAI and other AI services.
"""

import json

from openai import OpenAI  # Updated import

from logger import logger
from scrapers.base import NewsArticle
from settings import settings, Settings

class AIServiceError(Exception):
    """Base exception for AI service errors."""

    pass

class InvalidSelectionFormatError(AIServiceError):
    """Exception raised when the selection format is invalid."""

    pass

class EmptySelectionError(AIServiceError):
    """Exception raised when no articles were selected."""

    pass

class AIService:
    """Service for AI-related operations."""

    def __init__(self, settings_obj: Settings = settings):
        """Initialize the AI service with settings."""
        self.settings = settings_obj
        # Initialize the OpenAI client with the API key
        self.client = OpenAI(api_key=settings_obj.ai.api_key)
        self.model = settings_obj.ai.model
        self.system_message = settings_obj.ai.system_message

        logger.info(
            "AI service initialized:\n  Model: %s\n  System message: %s\n  API key: %s",
            self.model,
            self.system_message,
            settings_obj.ai.api_key,
        )

    def select_articles(
        self,
        initial_articles: list[NewsArticle],
        user_interests: str | None = None,
        max_retries: int = 3,
    ) -> list[NewsArticle]:
        """
        Use AI to select which articles to scrape in detail.

        Args:
            initial_articles: List of articles with basic info
            user_interests: User interests to guide selection
            max_retries: Maximum number of retries for API calls

        Returns:
            List of selected articles to scrape in detail

        Raises:
            AIServiceError: If there's an error calling the AI service
        """
        if user_interests is None:
            user_interests = self.settings.news.user_interests

        logger.info(
            "Selecting articles from %d initial articles", len(initial_articles)
        )

        # Build the complete prompt with the template
        prompt = self.settings.ai.article_selection_template.format(
            user_interests=user_interests, articles=json.dumps(initial_articles)
        )

        retries = 0
        error_messages = []

        # Try to get valid article selection with retries
        while retries < max_retries:
            try:
                # Call the API
                selection_result = self._call_selection_api(prompt)

                # Validate the selection result
                selected_articles = self._validate_selection_result(
                    selection_result, initial_articles
                )

                logger.info("Selected %d articles", len(selected_articles))
                return selected_articles

            except AIServiceError as e:
                error_messages.append(str(e))
                logger.error("Error in article selection: %s", str(e))
                retries += 1
                logger.info("Retrying... (Attempt %d/%d)", retries, max_retries)

        # All retries failed
        logger.error(
            "Failed after %d attempts. Errors: %s", max_retries, error_messages
        )
        raise AIServiceError(
            f"Failed after {max_retries} attempts. Errors: {error_messages}"
        )

    def summarize_articles(
        self,
        articles: list[NewsArticle],
        user_interests: str | None = None,
    ) -> str:
        """
        Summarize articles using OpenAI's API.

        Args:
            articles: List of NewsArticle objects
            user_interests: User interests to guide summarization

        Returns:
            Summary of the articles

        Raises:
            AIServiceError: If there's an error calling the AI service
        """
        if user_interests is None:
            user_interests = self.settings.news.user_interests

        logger.info("Summarizing %d articles", len(articles))

        # Build the prompt and call the API
        prompt = self.settings.ai.email_summary_template.format(
            user_interests=user_interests, articles=json.dumps(articles)
        )

        return self._call_summarization_api(prompt)

    def _call_selection_api(self, prompt: str) -> dict[str, list[str]]:
        """Call the OpenAI API to select articles."""
        try:
            # Make the API call with proper type handling
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_message},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if content is None:
                raise AIServiceError("Received empty response from OpenAI")

            # Parse JSON response
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise AIServiceError(f"Invalid JSON response from OpenAI: {str(e)}")

        except Exception as e:
            # Re-raise as AIServiceError if not already an instance
            if not isinstance(e, AIServiceError):
                raise AIServiceError(f"Error calling OpenAI API: {str(e)}") from e
            raise

    def _call_summarization_api(self, prompt: str) -> str:
        """Call the OpenAI API for article summarization."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_message},
                    {"role": "user", "content": prompt},
                ],
            )

            summary = response.choices[0].message.content
            if not summary:
                raise AIServiceError("Failed to summarize news: Empty response")

            return summary
        except Exception as e:
            raise AIServiceError(f"Error calling summarization API: {str(e)}")

    def _validate_selection_result(
        self,
        selection_result: dict[str, list[str]],
        initial_articles: list[NewsArticle],
    ) -> list[NewsArticle]:
        """Validate the selection result from the AI and return the selected articles."""
        # Check if 'articles' key exists
        if "articles" not in selection_result:
            raise InvalidSelectionFormatError(
                "Invalid response format: 'articles' key not found"
            )

        # Log selected URLs
        logger.info("Selection results: %d URLs", len(selection_result["articles"]))
        for url in selection_result["articles"]:
            logger.debug("Selected URL: %s", url)

        # Filter articles by URL
        selected_articles = [
            article
            for article in initial_articles
            if article["url"] in selection_result["articles"]
        ]

        # Check if any articles were selected
        if not selected_articles:
            raise EmptySelectionError(
                "No articles were selected or URLs don't match any in the initial list"
            )

        return selected_articles


# Create a default instance for backward compatibility
ai_service = AIService(settings)


# Backward compatibility functions
def select_articles(
    initial_articles: list[NewsArticle],
    user_interests: str = settings.news.user_interests,
    max_retries: int = 3,
) -> list[NewsArticle]:
    """Legacy function for backward compatibility."""
    return ai_service.select_articles(initial_articles, user_interests, max_retries)


def summarize_articles(
    articles: list[NewsArticle],
    user_interests: str = settings.news.user_interests,
) -> str:
    """Legacy function for backward compatibility."""
    return ai_service.summarize_articles(articles, user_interests)
