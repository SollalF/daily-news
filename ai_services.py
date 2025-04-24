"""
Module for AI services and API calls.
Centralizes all interactions with OpenAI and other AI services.
"""

import json
from typing import Any, Dict

import openai  # type: ignore

from scrapers.base import NewsArticle
from settings import (
    ARTICLE_SELECTION_TEMPLATE,
    DEFAULT_MODEL,
    DEFAULT_USER_INTERESTS,
    EMAIL_SUMMARY_TEMPLATE,
    OPENAI_API_KEY,
    SYSTEM_MESSAGE,
)

# Configure the OpenAI API
openai.api_key = OPENAI_API_KEY


class AIServiceError(Exception):
    """Base exception for AI service errors."""

    pass


class InvalidSelectionFormatError(AIServiceError):
    """Exception raised when the selection format is invalid."""

    pass


class EmptySelectionError(AIServiceError):
    """Exception raised when no articles were selected."""

    pass


def _validate_selection_result(
    selection_result: dict[str, list[str]], initial_articles: list[NewsArticle]
) -> list[NewsArticle]:
    """
    Validate the selection result from the AI and return the selected articles.

    Args:
        selection_result: The JSON result from the AI
        initial_articles: The initial list of articles

    Returns:
        List of selected articles

    Raises:
        InvalidSelectionFormatError: If the selection format is invalid
        EmptySelectionError: If no articles were selected
    """
    # Check if 'articles' key exists
    if "articles" not in selection_result:
        raise InvalidSelectionFormatError(
            "Invalid response format: 'articles' key not found"
        )

    # Print selected URLs
    print(f"[INFO] Selection results:")
    for url in selection_result["articles"]:
        print(f"    [INFO] URL: {url}")

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


def _call_selection_api(prompt: str) -> dict[str, list[str]]:
    """
    Call the OpenAI API to select articles.

    Args:
        prompt: The formatted prompt for article selection

    Returns:
        The selection result JSON with article URLs

    Raises:
        AIServiceError: If the API call fails or returns invalid data
    """
    try:
        # Make the API call with proper type handling
        response = openai.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )  # type: ignore

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


def select_articles(
    initial_articles: list[NewsArticle],
    user_interests: str = DEFAULT_USER_INTERESTS,
    max_retries: int = 3,
) -> list[NewsArticle]:
    """
    Use AI to select which articles to scrape in detail.

    Args:
        initial_articles: List of articles with basic info
        user_interests: User interests to guide selection, defaults to settings.DEFAULT_USER_INTERESTS
        max_retries: Maximum number of retries for API calls with invalid outputs

    Returns:
        List of selected articles to scrape in detail

    Raises:
        AIServiceError: If there's an error calling the AI service after max retries
    """
    print(f"[INFO] Selecting articles")

    # Build the complete prompt with the template
    prompt = ARTICLE_SELECTION_TEMPLATE.format(
        user_interests=user_interests, articles=json.dumps(initial_articles)
    )

    retries = 0
    error_messages = []

    # Try to get valid article selection with retries
    while retries < max_retries:
        try:
            # Call the API
            selection_result = _call_selection_api(prompt)

            # Validate the selection result
            selected_articles = _validate_selection_result(
                selection_result, initial_articles
            )

            print(f"[INFO] Selected {len(selected_articles)} articles")
            return selected_articles

        except AIServiceError as e:
            error_messages.append(str(e))
            print(f"[ERROR] {str(e)}")
            retries += 1
            print(f"[INFO] Retrying... (Attempt {retries}/{max_retries})")

    # All retries failed
    print(f"[ERROR] Failed after {max_retries} attempts. Errors: {error_messages}")
    raise AIServiceError(
        f"Failed after {max_retries} attempts. Errors: {error_messages}"
    )


def _call_summarization_api(prompt: str) -> str:
    """
    Call the OpenAI API for article summarization.

    Args:
        prompt: The formatted prompt for summarization

    Returns:
        Generated summary text

    Raises:
        AIServiceError: If the API call fails or returns empty content
    """
    try:
        response = openai.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": prompt},
            ],
        )

        summary = response.choices[0].message.content
        if not summary:
            raise AIServiceError("Failed to summarize news: Empty response")

        return summary
    except Exception as e:
        raise AIServiceError(f"Error calling summarization API: {str(e)}")


def summarize_articles(
    articles: list[NewsArticle],
    user_interests: str = DEFAULT_USER_INTERESTS,
) -> str:
    """
    Summarize articles using OpenAI's API.

    Args:
        articles: List of NewsArticle objects
        user_interests: User interests to guide summarization, defaults to settings.DEFAULT_USER_INTERESTS

    Returns:
        Summary of the articles

    Raises:
        AIServiceError: If there's an error calling the AI service
    """
    print(f"[INFO] Summarizing {len(articles)} articles")

    # Build the prompt and call the API
    prompt = EMAIL_SUMMARY_TEMPLATE.format(
        user_interests=user_interests, articles=json.dumps(articles)
    )

    return _call_summarization_api(prompt)


def call_ai_api(
    prompt: str,
    system_message: str = SYSTEM_MESSAGE,
    model: str = DEFAULT_MODEL,
    json_response: bool = False,
    temperature: float = 0.7,
    max_tokens: int | None = None,
) -> Any:
    """
    General purpose function to call the OpenAI API.

    Args:
        prompt: The user prompt to send to the API
        system_message: The system message for context
        model: The model to use for the API call
        json_response: Whether to expect and parse a JSON response
        temperature: Temperature parameter for generation
        max_tokens: Maximum tokens to generate in the response

    Returns:
        The API response content, parsed as JSON if json_response is True

    Raises:
        AIServiceError: If there's an error calling the AI service
    """
    try:
        # Set up the message payload
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ]

        # Set up the API call parameters
        params: Dict[str, Any] = {"model": model, "messages": messages}

        # Add optional parameters
        if json_response:
            params["response_format"] = {"type": "json_object"}
        if temperature != 0.7:
            params["temperature"] = temperature
        if max_tokens is not None:
            params["max_tokens"] = max_tokens

        # Make the API call
        response = openai.chat.completions.create(**params)  # type: ignore

        content = response.choices[0].message.content
        if content is None:
            raise AIServiceError("Received empty response from OpenAI")

        # Parse JSON if requested
        if json_response:
            return json.loads(content)
        return content

    except Exception as e:
        raise AIServiceError(f"Error calling AI API: {str(e)}")
