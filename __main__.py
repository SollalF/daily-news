# pyright: basic

"""
Main module for generating and sending daily news emails.
Fetches news content and sends it to subscribers.
"""

import sys
import traceback
from http import HTTPStatus

from dotenv import load_dotenv

import ai_services
from email_sender import send_news_email
from logger import logger, setup_logger
from news_fetcher import NewsResult, fetch_top_news
from settings import settings

# Try to load from .env file if it exists, otherwise use system env vars
_ = load_dotenv()

# Initialize the logger
setup_logger()

logger.info("API Keys: %s", settings.email.api_key, settings.ai.api_key)

def main(args):
    """
    Main function to fetch, summarize, and send news emails.

    Args:
        args: Dictionary of arguments including email recipients, categories, and prompt

    Returns:
        Response dictionary with success status and message
    """
    try:
        if "to_emails" in args:
            to_emails = args["to_emails"]
        else:
            raise ValueError(f"Email recipients not found in arguments {args}")

        # Get categories from args or default to DEFAULT_CATEGORIES
        if "categories" in args:
            categories = args["categories"]
            logger.info(f"Using categories: {categories}")
        else:
            categories = settings.news.categories
            logger.info(f"Using default categories: {categories}")

        # Get max news per category from args or default to DEFAULT_MAX_NEWS_PER_CATEGORY
        if "max_news_per_category" in args:
            max_news_per_category = args["max_news_per_category"]
            logger.info(f"Using max news per category: {max_news_per_category}")
        else:
            max_news_per_category = settings.news.max_per_category
            logger.info(f"Using default max news per category: {max_news_per_category}")

        # Get user interests if provided
        if "user_interests" in args:
            user_interests = args["user_interests"]
            logger.info(f"Using user interests: {user_interests}")
        else:
            user_interests = settings.news.user_interests
            logger.info(f"Using default user interests: {user_interests}")

        news_result: NewsResult = fetch_top_news(
            categories, user_interests, max_news_per_category
        )

        if not news_result.get("success"):
            logger.error(f"Failed to fetch news: {news_result.get('error')}")
            return {
                "body": {
                    "success": False,
                    "message": "Failed to fetch news",
                    "error": news_result.get("error"),
                },
                "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR,
            }

        # Get news articles from result, handling optional key safely
        news_articles = news_result.get("news", [])

        # Summarize and send the news
        summarized_news = ai_services.summarize_articles(
            news_articles, user_interests=user_interests
        )

        email_result = send_news_email(
            news_articles,
            to_emails,
            summarized_news,
        )

        logger.info("News summarized and sent successfully")
        response = {
            "body": {
                "success": True,
                "message": "News summarized and sent successfully",
            },
            "statusCode": HTTPStatus.OK,
        }
        return response

    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Error in main function: {str(e)}")
        logger.debug(tb)
        return {
            "body": {
                "success": False,
                "message": f"Error in main function: {str(e)}",
                "traceback": tb,
            },
            "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR,
        }


if __name__ == "__main__":
    if "--test" in sys.argv:
        logger.info("Running in test mode")
        if "--emails" in sys.argv:
            email_index = sys.argv.index("--emails") + 1
            if email_index < len(sys.argv):
                to_emails = sys.argv[email_index].split(",")
            else:
                raise ValueError("No email addresses provided after --emails argument")
        else:
            to_emails = settings.email.recipients

        if "--categories" in sys.argv:
            categories_index = sys.argv.index("--categories") + 1
            if categories_index < len(sys.argv):
                categories = sys.argv[categories_index].split(",")
            else:
                raise ValueError("No categories provided after --categories argument")
        else:
            categories = settings.news.categories

        # Get user interests (primary customization point)
        user_interests = settings.news.user_interests
        if "--interests" in sys.argv:
            interests_index = sys.argv.index("--interests") + 1
            if interests_index < len(sys.argv):
                user_interests = sys.argv[interests_index]
            else:
                raise ValueError("No interests provided after --interests argument")

        # Build the args dict with user interests
        args = {
            "to_emails": to_emails,
            "categories": categories,
            "user_interests": user_interests,
            "max_news_per_category": settings.news.max_per_category,
        }

        _ = main(args)
