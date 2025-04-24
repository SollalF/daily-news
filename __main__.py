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
from news_fetcher import NewsResult, fetch_top_news
from settings import (
    DEFAULT_CATEGORIES,
    DEFAULT_EMAIL_RECIPIENTS,
    DEFAULT_MAX_NEWS_PER_CATEGORY,
    DEFAULT_USER_INTERESTS,
)

# Try to load from .env file if it exists, otherwise use system env vars
_ = load_dotenv()


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
            print(f"[INFO] Using categories: {categories}")
        else:
            categories = DEFAULT_CATEGORIES
            print(f"[INFO] Using default categories: {categories}")

        # Get max news per category from args or default to DEFAULT_MAX_NEWS_PER_CATEGORY
        if "max_news_per_category" in args:
            max_news_per_category = args["max_news_per_category"]
            print(f"[INFO] Using max news per category: {max_news_per_category}")
        else:
            max_news_per_category = DEFAULT_MAX_NEWS_PER_CATEGORY
            print(
                f"[INFO] Using default max news per category: {max_news_per_category}"
            )

        # Get user interests if provided
        if "user_interests" in args:
            user_interests = args["user_interests"]
            print(f"[INFO] Using user interests: {user_interests}")
        else:
            user_interests = DEFAULT_USER_INTERESTS
            print(f"[INFO] Using default user interests: {user_interests}")

        news_result: NewsResult = fetch_top_news(
            categories, user_interests, max_news_per_category
        )

        if not news_result.get("success"):
            return {
                "body": {
                    "success": False,
                    "message": "Failed to fetch news",
                    "error": news_result.get("error"),
                },
                "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR,
            }

        # Summarize and send the news
        summarized_news = ai_services.summarize_articles(
            news_result["news"], user_interests=user_interests
        )

        email_result = send_news_email(
            news_result["news"],
            to_emails,
            summarized_news,
        )

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
        print(f"Error in main function: {str(e)}")
        print(tb)
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
        if "--emails" in sys.argv:
            email_index = sys.argv.index("--emails") + 1
            if email_index < len(sys.argv):
                to_emails = sys.argv[email_index].split(",")
            else:
                raise ValueError("No email addresses provided after --emails argument")
        else:
            to_emails = DEFAULT_EMAIL_RECIPIENTS

        if "--categories" in sys.argv:
            categories_index = sys.argv.index("--categories") + 1
            if categories_index < len(sys.argv):
                categories = sys.argv[categories_index].split(",")
            else:
                raise ValueError("No categories provided after --categories argument")
        else:
            categories = DEFAULT_CATEGORIES

        # Get user interests (primary customization point)
        user_interests = DEFAULT_USER_INTERESTS
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
            "max_news_per_category": DEFAULT_MAX_NEWS_PER_CATEGORY,
        }

        _ = main(args)
