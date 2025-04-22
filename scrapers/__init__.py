"""
News scraper implementations for different websites.
"""

from . import base, techcrunch

# Mapping of source names to scraper instances
SCRAPERS = {
    "techcrunch": techcrunch.TechCrunchScraper(),
}
