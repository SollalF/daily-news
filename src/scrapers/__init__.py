"""
Package for web scrapers that fetch news from various sources.
"""

# Import in order of dependency
# 1. Base classes/types
from .base import NewsArticle, NewsScraper

# 2. Concrete scraper implementations
from .cnn import CNNScraper

# 3. Manager class (depends on scraper classes being defined)
from .manager import ScraperManager
from .scmp_scraper import SCMPScraper
from .techcrunch import TechCrunchScraper

__all__ = [
    "ScraperManager",
    "NewsArticle",
    "NewsScraper",
    "CNNScraper",
    "TechCrunchScraper",
    "SCMPScraper",
]
