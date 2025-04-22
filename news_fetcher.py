"""
Module for fetching daily news from web scrapers.
"""

from typing import TypedDict

import scrapers.base as base  # pyright: ignore[reportImplicitRelativeImport]

# Import our scraper system with relative import
import scrapers.manager as scraper_manager  # pyright: ignore[reportImplicitRelativeImport]


class NewsResult(TypedDict, total=False):
    """Result of news fetching operation."""

    success: bool
    message: str
    news: dict[str, list[base.NewsArticle]]
    error: str


def fetch_top_news(categories: list[str], max_news_per_category: int = 5) -> NewsResult:
    """
    Fetch top news articles using web scrapers.

    Args:
        categories: List of news categories to fetch
        max_news_per_category: Maximum number of news items to fetch per category

    Returns:
        NewsResult dictionary with success status and news data
    """
    all_news = {}

    try:
        # Get news from our web scrapers
        scraper_news = fetch_from_scrapers(categories, max_news_per_category)

        # Combine results from scrapers
        for category in categories:
            if category in scraper_news:
                articles = [
                    base.NewsArticle(**article) for article in scraper_news[category]
                ]
                all_news[category] = articles

        if not all_news:
            return {
                "success": False,
                "message": "Failed to fetch news for any category",
                "error": "NO_RESULTS",
            }

        return {
            "success": True,
            "message": "Successfully fetched news",
            "news": all_news,
        }

    except Exception as e:
        # Log the error for debugging purposes
        print(f"Error fetching news: {str(e)}")
        return {
            "success": False,
            "message": f"Error fetching news: {str(e)}",
            "error": "FETCH_ERROR",
        }


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
        manager = scraper_manager.ScraperManager()

        # Fetch news and organize by category
        news_by_source = manager.fetch_news(
            categories=categories,
            max_articles_per_source=max(
                3, max_news_per_category // len(categories)
            ),  # Divide articles among sources
        )

        # Reorganize by category
        news_by_category = manager.organize_by_category(news_by_source)

        return news_by_category
    except Exception as e:
        # Log the error for debugging purposes
        print(f"Error when fetching from scrapers: {str(e)}")
        return {}


if __name__ == "__main__":
    # Test categories
    categories = ["ai", "amazon", "apps"]
    # Fetch top news for test categories
    result = fetch_top_news(categories)

    # Print the result
    if result.get("success"):
        print("Successfully fetched news:")
        for category, articles in result.get("news", {}).items():
            print(f"\nCategory: {category}")
            for article in articles:
                print(f"Title: {article['title']}, Source: {article['source']}")
    else:
        print(f"Failed to fetch news: {result.get('message')}")
