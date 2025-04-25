"""
Module for fetching daily news from web scrapers.
"""

from typing import TypedDict

from dotenv import load_dotenv

# Handle imports for both script and module use cases
import ai_services
from scrapers import base, manager  # type: ignore
from settings import settings

# Try to load from .env file if it exists
_ = load_dotenv()


class NewsResult(TypedDict, total=False):
    """Result of news fetching operation."""

    success: bool
    message: str
    news: list[base.NewsArticle]
    error: str


def fetch_top_news(
    categories: list[str],
    user_interests: str,
    max_news_per_category: int = 5,
) -> NewsResult:
    """
    Fetch top news articles using web scrapers.

    Args:
        categories: List of news categories to fetch
        max_news_per_category: Maximum number of news items to fetch per category

    Returns:
        NewsResult dictionary with success status and news data
    """
    try:
        # Phase 1: Get initial list of articles with just headlines and descriptions
        initial_articles = fetch_initial_article_list(categories, max_news_per_category)

        # If no articles were found, return error
        if not initial_articles:
            return {
                "success": False,
                "message": "Failed to fetch news for any category",
                "error": "NO_RESULTS",
            }

        # Phase 2: Let AI select which articles to scrape in detail
        articles_to_scrape = ai_services.select_articles(
            initial_articles, user_interests=user_interests
        )

        # Phase 3: Fetch detailed content only for selected articles
        detailed_news = fetch_article_details(articles_to_scrape)

        if not detailed_news:
            return {
                "success": False,
                "message": "Failed to fetch detailed news for any article",
                "error": "NO_DETAILED_RESULTS",
            }

        return {
            "success": True,
            "message": "Successfully fetched news",
            "news": detailed_news,
        }

    except Exception as e:
        # Log the error for debugging purposes
        print(f"Error fetching news: {str(e)}")
        return {
            "success": False,
            "message": f"Error fetching news: {str(e)}",
            "error": "FETCH_ERROR",
        }


def fetch_initial_article_list(
    categories: list[str], max_news_per_category: int = 20
) -> list[base.NewsArticle]:
    """
    Fetch initial list of articles with just basic information.

    Args:
        categories: List of categories to fetch
        max_news_per_category: Maximum articles per category

    Returns:
        List of articles with basic info
    """

    try:
        # Create scraper manager
        scraper_manager = manager.ScraperManager()

        # Fetch news from scrapers
        all_articles = scraper_manager.fetch_headlines(
            categories=categories,
            max_articles_per_source=max(5, max_news_per_category // len(categories)),
        )

        return all_articles
    except Exception as e:
        # Log the error for debugging purposes
        print(f"Error when fetching initial article list: {str(e)}")
        return []


def fetch_article_details(
    selected_articles: list[base.NewsArticle],
) -> list[base.NewsArticle]:
    """
    Fetch detailed content for selected articles.

    Args:
        selected_articles: List of selected articles

    Returns:
        List of detailed articles with NewsArticle type
    """
    print(f"[INFO] Fetching detailed content for {len(selected_articles)} articles")

    detailed_articles: list[base.NewsArticle] = []

    # Create scraper manager
    scraper_manager = manager.ScraperManager()

    for article in selected_articles:
        try:
            # Extract the source from the article
            source = article.get("source", "")

            # Find the appropriate scraper based on source
            scraper = None
            for scraper_name, scraper_instance in scraper_manager.scrapers.items():
                if (
                    scraper_name.lower() in source.lower()
                    or source.lower() in scraper_name.lower()
                ):
                    scraper = scraper_instance
                    break

            if scraper:
                # Fetch detailed content
                detailed_article = scraper.fetch_article_by_url(article["url"])
                if detailed_article:
                    # Ensure it's a NewsArticle type
                    detailed_articles.append(detailed_article)
            else:
                # If we can't find a matching scraper, just use the original article
                # The article is already a NewsArticle, so we can append it directly
                print(f"No scraper found for {article['url']}, using original article")
                detailed_articles.append(article)

        except Exception as e:
            print(f"Error fetching detailed content for {article['url']}: {str(e)}")
            # Keep the original article if we can't get more details
            detailed_articles.append(article)

    print(f"[INFO] Fetched {len(detailed_articles)} detailed articles")

    return detailed_articles


# def fetch_from_newsapi(
#     categories: list[str], max_news_per_category: int = 5
# ) -> dict[str, list[dict[str, Any]]]:
#     """
#     Fetch news from NewsAPI.

#     Args:
#         categories: List of categories to fetch
#         max_news_per_category: Maximum articles per category

#     Returns:
#         Dictionary mapping categories to article lists
#     """
#     # Get API key from environment
#     api_key = os.getenv("NEWS_API_KEY")
#     if not api_key:
#         print("NewsAPI key not found, skipping API fetch")
#         return {}

#     api_categories = {
#         "general": "general",
#         "technology": "technology",
#         "business": "business",
#         "health": "health",
#         "science": "science",
#     }

#     results = {}

#     for category in categories:
#         api_category = api_categories.get(category, "general")

#         url = "https://newsapi.org/v2/top-headlines"
#         params = {
#             "apiKey": api_key,
#             "category": api_category,
#             "language": "en",
#             "pageSize": max_news_per_category,
#         }

#         try:
#             response = requests.get(url, params=params, timeout=10)

#             if response.status_code == 200:
#                 data: dict[str, Any] = response.json()
#                 articles = data.get("articles", [])

#                 # Process articles to standardize format
#                 processed_articles = []
#                 for article in articles:
#                     # Format publish date
#                     published_at = article.get("publishedAt")
#                     if published_at:
#                         try:
#                             date_obj = datetime.fromisoformat(
#                                 published_at.replace("Z", "+00:00")
#                             )
#                             formatted_date = date_obj.strftime("%B %d, %Y")
#                         except (ValueError, TypeError):
#                             formatted_date = published_at
#                     else:
#                         formatted_date = "Unknown"

#                     processed_articles.append(
#                         {
#                             "title": article.get("title", ""),
#                             "description": article.get("description", ""),
#                             "url": article.get("url", ""),
#                             "source": article.get("source", {}).get("name", "Unknown"),
#                             "published_date": formatted_date,
#                             "image_url": article.get("urlToImage", ""),
#                         }
#                     )

#                 results[category] = processed_articles
#             else:
#                 print(
#                     f"Error fetching {category} news from API: Status code {response.status_code}"
#                 )
#         except Exception as e:
#             print(f"Error when fetching from NewsAPI for {category}: {str(e)}")

#     return results


def fetch_from_scrapers(
    categories: list[str], max_news_per_category: int = 5
) -> dict[str, list[base.NewsArticle]]:
    """
    Fetch news using web scrapers.

    Args:
        categories: List of categories to fetch
        max_news_per_category: Maximum articles per category

    Returns:
        Dictionary mapping categories to article lists
    """
    try:
        # Create scraper manager
        scraper_manager = manager.ScraperManager()

        # Fetch news and organize by category
        news_by_source = scraper_manager.fetch_news(
            categories=categories,
            max_articles_per_source=max(
                3, max_news_per_category // len(categories)
            ),  # Divide articles among sources
        )

        # Reorganize by category
        news_by_category = scraper_manager.organize_by_category(news_by_source)

        return news_by_category
    except Exception as e:
        # Log the error for debugging purposes
        print(f"Error when fetching from scrapers: {str(e)}")
        return {}


if __name__ == "__main__":
    # Test categories
    categories = ["ai", "amazon", "apps"]
    # Fetch top news for test categories
    result = fetch_top_news(categories, user_interests=settings.news.user_interests)

    # Print the result
    if result.get("success"):
        print("Successfully fetched news:")
        for article in result.get("news", []):
            print(f"Title: {article['title']}, Source: {article['source']}")
    else:
        print(f"Failed to fetch news: {result.get('message')}")
