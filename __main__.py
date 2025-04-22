# pyright: basic

"""
Main module for generating and sending daily news emails.
Fetches news content and sends it to subscribers.
"""

import json
import os
import sys
import traceback
from http import HTTPStatus

import openai
from dotenv import load_dotenv
from email_sender import send_news_email
from news_fetcher import fetch_top_news

# Try to load from .env file if it exists, otherwise use system env vars
_ = load_dotenv()

# Ensure the API key is set correctly
openai.api_key = os.getenv("OPENAI_API_KEY")

DEFAULT_CATEGORIES = ["latest"]
DEFAULT_MAX_NEWS_PER_CATEGORY = 50
DEFAULT_PROMPT = """
 - Summarize the following articles: {articles}. 
 - Output to HTML format. 
 - I work in AI. If there is an important AI news, especially AI in education, I want to be the first one to know it. 
 - If there are highly important news to me, display a callout at the top with a short summary of these news. 
 - Then prioritise the articles based on my interests.
 - Interests (In order of priority): 
    - GPT 4o image model
    - AI
    - Innovations and news that can help me be more productive as a software engineer and product manager
    - Scandals, security issues, great innovations, . 
 - Ignore: inverstments, business.
 - Do not include a ```html tag in the output.
"""

DEFAULT_EMAIL_RECIPIENTS = ["sollal@solomongp.com"]


def summarize_articles(articles, prompt):
    """
    Summarize articles using OpenAI's API.

    Args:
        articles: List of articles to summarize
        prompt: Prompt to guide the summarization

    Returns:
        Summary of the articles
    """
    if "{articles}" not in prompt:
        prompt += " {articles}"

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": prompt.format(articles=json.dumps(articles)),
            },
        ],
    )
    summary = response.choices[0].message.content

    if not summary:
        raise ValueError("Failed to summarize news")

    return summary


def main(args):
    """
    Main function to fetch, summarize, and send news emails.

    Args:
        args: Dictionary of arguments including email recipients, categories, and prompt

    Returns:
        Response dictionary with success status and message
    """
    try:
        to_emails = args.get("to_emails")

        if not to_emails or to_emails == [""]:
            raise ValueError(f"Email recipients not found in arguments {args}")

        # Get categories from args or default to DEFAULT_CATEGORIES
        categories = args.get("categories", DEFAULT_CATEGORIES)

        # Get max news per category from args or default to DEFAULT_MAX_NEWS_PER_CATEGORY
        max_news_per_category = args.get(
            "max_news_per_category", DEFAULT_MAX_NEWS_PER_CATEGORY
        )

        prompt = args.get("prompt", DEFAULT_PROMPT)

        # Fetch news
        news_result = fetch_top_news(categories, max_news_per_category)

        if not news_result.get("success"):
            return {
                "body": {
                    "success": False,
                    "message": "Failed to fetch news",
                    "error": news_result.get("error"),
                },
                "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR,
            }

        if "news" in news_result:
            # Summarize news articles
            summarized_news = summarize_articles(news_result["news"], prompt)

            # Send summarized news via email
            email_result = send_news_email(
                news_result["news"], to_emails, summarized_news
            )
        else:
            return {
                "body": {
                    "success": False,
                    "message": "No news data available to send",
                },
                "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR,
            }

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

        if "--prompt" in sys.argv:
            prompt_index = sys.argv.index("--prompt") + 1
            if prompt_index < len(sys.argv):
                prompt = sys.argv[prompt_index]
            else:
                raise ValueError("No prompt provided after --prompt argument")
        else:
            prompt = DEFAULT_PROMPT

        _ = main({"to_emails": to_emails, "categories": categories, "prompt": prompt})
