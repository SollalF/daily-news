"""
Package for web scrapers that fetch news from various sources.
"""

# Import additional scrapers
from . import cnn, techcrunch

# Import core base classes
from .base import NewsArticle, NewsScraper
