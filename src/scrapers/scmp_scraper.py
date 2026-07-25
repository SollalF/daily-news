"""
Scraper for South China Morning Post (SCMP) news.
This scraper uses the SCMP API for Phase 1 (fetching headlines)
and traditional HTML scraping for Phase 3 (fetching full article content).
"""

import json
from datetime import datetime, timezone
from pprint import pprint
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from logger import logger

from .base import NewsArticle, NewsScraper

# SCMP API details
SCMP_API_BASE_URL = "https://apigw.scmp.com"
SCMP_API_ENDPOINT = "/content-delivery/v2"
# It's good practice to keep API keys and sensitive hashes out of the code.
# However, for this example, we'll use the provided hash.
# In a production system, this might come from config or be part of a more complex auth flow.
SCMP_API_EXTENSIONS = {
    "persistedQuery": {
        "version": 1,
        "sha256Hash": "0d52dd081f53f01fba3fbfe2d020d6a70f5da2f024650de5aed9ecd889c625d1",
    }
}
SCMP_API_OPERATION_NAME = "clientQueryLoaderHomeQuery"
# Minimal set of headers based on user's provided info
SCMP_API_HEADERS = {
    # "accept": "*/*",
    "apikey": "MyYvyg8M9RTaevVlcIRhN5yRIqqVssNY",  # This was in the example, should be treated as sensitive
    "content-type": "application/json",
    "origin": "https://www.scmp.com",
    "referer": "https://www.scmp.com/",
    "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36",
}

CATEGORY_URLS = {
    "default": "/",
    "China": "/news/china",
    "China Military": "/news/china/military",
    "China Diplomacy": "/news/china/diplomacy",
    "China Politics": "/news/china/politics",
    "China Science": "/news/china/science",
    "China Future Tech": "/news/china-future-tech",
    "Hong Kong": "/news/hong-kong",
    "Hong Kong Politics": "/news/hong-kong/politics",
    "Hong Kong Economy": "/news/hong-kong/hong-kong-economy",
    "Hong Kong Health & Environment": "/news/hong-kong/health-environment",
    "Hong Kong Law and Crime": "/news/hong-kong/law-and-crime",
    "Hong Kong Society": "/news/hong-kong/society",
    "Hong Kong Education": "/news/hong-kong/education",
    "Lifestyle": "/lifestyle",
    "Food & Drink": "/lifestyle/food-drink",
    "Health & Wellness": "/lifestyle/health-wellness",
    "Chinese culture": "/lifestyle/chinese-culture",
    "Arts": "/lifestyle/arts",
    "People & Culture": "/news/people-culture",
    "China Personalities": "/news/people-culture/china-personalities",
    "Trending in China": "/news/people-culture/trending-china",
    "Gender & Diversity": "/news/people-culture/gender-diversity",
    "Environment": "/news/people-culture/environment",
    "Social Welfare": "/news/people-culture/social-welfare",
    "Style": "/magazines/style",
    "Luxury": "/magazines/style/luxury",
    "Fashion": "/magazines/style/fashion",
    "Beauty": "/magazines/style/beauty",
    "Lifestyle": "/magazines/style/lifestyle",
    "People": "/magazines/style/people",
}


class SCMPScraper(NewsScraper):
    """
    A scraper for fetching news articles from SCMP.
    Phase 1 uses the SCMP API.
    Phase 2 (AI selection) is handled by the manager.
    Phase 3 uses traditional HTML scraping for selected articles.
    """

    def __init__(self) -> None:
        super().__init__(
            base_url="https://www.scmp.com",  # Base URL for actual article pages
            category_urls=CATEGORY_URLS,
            source_name="SCMP",
        )
        # The API URL for "aroundHomeQuery" seems to provide a mix of articles.
        # We might need to investigate if there are other operationNames or parameters for specific categories.
        # For now, we'll assume 'home' fetches from this API.
        self.api_url = f"{SCMP_API_BASE_URL}{SCMP_API_ENDPOINT}"

    def fetch_articles(
        self, category: str = "home", max_articles: int = 10
    ) -> list[NewsArticle]:
        """
        Fetch articles from SCMP API for a given category (currently, only 'home' is supported via API).

        Args:
            category: The category to fetch articles for. Defaults to "home".
            max_articles: The maximum number of articles to fetch.

        Returns:
            A list of NewsArticle objects.
        """
        logger.debug(
            f"Fetching articles for category: {category}, max_articles: {max_articles}"
        )

        if category.lower() != "home":
            logger.warning(
                f"SCMP API scraper currently only supports 'home' category for API fetching. "
                f"Requested: '{category}'. Proceeding with 'home'."
            )

        api_data = self._fetch_api_data()
        logger.debug(f"API data fetched: {api_data}")

        raw_articles = self._select_raw_articles_from_api(api_data, max_articles)
        logger.debug(f"Raw articles selected: {raw_articles}")

        articles: list[NewsArticle] = []
        for raw_article_data in raw_articles:
            article = self._extract_article_from_api_item(
                raw_article_data, category="home"
            )
            if article:
                articles.append(article)
                logger.debug(f"Article extracted: {article}")

        logger.debug(f"Total articles fetched: {len(articles)}")
        return articles

    def _fetch_api_data(self) -> dict[str, Any]:
        # The API has an 'excludeEntityIds' parameter. We'll start with an empty list.
        # This might be used for pagination or avoiding duplicates if we know prior IDs.
        variables = {
            "advertisersQueueName": "homepage_brand_post_int",
            "excludeSsrContentEntityIds": [],  # Keeping this empty as it's likely dynamic
            "isAsiaEdition": False,
            "mostPopularQueueName": "scmp_trending_section_scmp_trending_section_homepage_last_24_hours",
            "multimediaQueueName": "visual_stories_top_int",
            "trendingTopicsQueueName": "related_topic_homepage_int_",
        }

        params = {
            "operationName": SCMP_API_OPERATION_NAME,
            "variables": json.dumps(variables),
            "extensions": json.dumps(SCMP_API_EXTENSIONS),
        }

        # logger.info(
        #     f"Fetching articles from SCMP API ({self.api_url}) with params: {params}"
        # )

        try:
            response = requests.get(
                self.api_url, headers=SCMP_API_HEADERS, params=params, timeout=20
            )
            response.raise_for_status()  # Raise an exception for HTTP errors
            api_data = response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch from SCMP API: {e}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from SCMP API: {e}")
            return {}

        # logger.info(f"SCMP API response:")
        # pprint(api_data)
        return api_data

    def _select_raw_articles_from_api(
        self, api_data: dict[str, Any], max_articles: int
    ) -> list[dict[str, Any]]:
        """
        Selects raw article data items from the SCMP API's JSON response.
        Expected path: response['data']['contents']['edges']
        Each edge contains a 'node' which is the article data.
        """

        try:
            # Navigate to the list of article edges
            edges = api_data.get("data", {}).get("contents", {}).get("edges", [])
            if not isinstance(edges, list):
                # logger.warning(
                #     f"[{self.source_name}] 'edges' is not a list in API response or not found. Data path: data.contents.edges"
                # )
                return []

            raw_articles: list[dict[str, Any]] = []
            for edge in edges:
                if (
                    isinstance(edge, dict)
                    and "node" in edge
                    and isinstance(edge["node"], dict)
                ):
                    raw_articles.append(edge["node"])
                else:
                    # logger.warning(
                    #     f"[{self.source_name}] Invalid or missing 'node' in API edge item: {edge}"
                    # )
                    pass

            logger.info(
                f"[{self.source_name}] Selected {len(raw_articles)} raw articles from API response."
            )
            return raw_articles[:max_articles]

        except AttributeError as e:
            logger.error(
                f"[{self.source_name}] Error accessing data in SCMP API response structure: {e}. Data: {api_data}"
            )
            return []
        except Exception as e:
            logger.error(
                f"[{self.source_name}] Unexpected error in _select_raw_articles_from_api: {e}"
            )
            return []

    def _extract_article_from_api_item(
        self, item_data: dict[str, Any], category: str
    ) -> NewsArticle | None:
        pass

    def fetch_article_by_url(self, url: str) -> NewsArticle | None:
        pass

    def _extract_article_info(
        self, news_article: NewsArticle, soup: BeautifulSoup
    ) -> NewsArticle:
        # This method needs to be implemented to extract article details from HTML (Phase 3)
        # For now, to satisfy the linter that expects a NewsArticle to be returned:
        raise NotImplementedError(
            "_extract_article_info is not yet implemented for SCMPScraper. "
            "This method is intended for Phase 3 HTML scraping."
        )

    def _select_article_elements(
        self, soup: BeautifulSoup, max_articles: int
    ) -> list[Tag]:
        """
        Not used for SCMP's API-based Phase 1. Stub implementation.
        """
        logger.warning(
            "_select_article_elements called on SCMPScraper; this method is for HTML list scraping, not API."
        )
        return []  # Should not be called if fetch_articles is correctly overridden.

    def _extract_article_from_list_item(
        self, element: Tag, category: str
    ) -> NewsArticle | None:
        """
        Not used for SCMP's API-based Phase 1. Stub implementation.
        """
        logger.warning(
            "_extract_article_from_list_item called on SCMPScraper; this method is for HTML list scraping, not API."
        )
        return None  # Should not be called.

    def get_categories_from_api(self) -> dict[str, str]:

        api_data = self._fetch_api_data()

        logger.info(f"SCMP API keys: {api_data['data'].keys()}")

        categories = {}

        for _, value in api_data["data"].items():
            if isinstance(value, dict):
                if value.get("__isBaseWithApplicationAndUrlAlias") == "Section":
                    categories[value["name"]] = value["urlAlias"]
                    for subsection in value["subSections"]["items"]["edges"]:
                        logger.info(
                            f"Subsection: {subsection['node']['name']} - {subsection['node']['urlAlias']}"
                        )
                        categories[subsection["node"]["urlAlias"]] = subsection["node"][
                            "name"
                        ]

        return categories

    def compare_availiable_categories_to_api_categories(self) -> None:

        available_categories = self.get_available_categories()
        api_categories = self.get_categories_from_api()

        logger.info(f"Available categories: {available_categories}")
        logger.info(f"API categories: {api_categories}")

        logger.info(f"Available categories: {available_categories.values()}")
        logger.info(f"API categories: {api_categories.values()}")

        for category in available_categories.values():
            if category not in api_categories.values():
                logger.warning(f"Category {category} not found in API categories.")

        for category in api_categories.values():
            if category not in available_categories.values():
                logger.warning(
                    f"Category {category} not found in available categories."
                )


# Example usage (for testing the scraper directly)
if __name__ == "__main__":
    scraper = SCMPScraper()
    news_articles = scraper.fetch_articles()
    pprint(news_articles)
