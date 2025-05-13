# Daily News Digest

A system for automatically collecting, summarizing, and emailing news articles.

## Overview

This system fetches news articles from multiple sources, uses AI to summarize them, and sends the digest via email. It's designed to focus on news most relevant to the user's interests and can be deployed in various environments, including as a serverless function.

## Features

- **Two-Phase News Fetching**: Efficiently collects headlines and descriptions, then uses AI to select articles for full scraping.
  - _Rationale_: Manages LLM context window limitations and reduces token costs by deferring full content parsing.
  - _Limitation_: Potential scaling issues with a large number of articles.
- **AI-Powered Summarization**: Leverages GPT-4o for personalized news digests.
  - _Benefit_: Provides a main headline for a quick overview.
  - _Issue_: AI summaries may occasionally contain inaccuracies (hallucinations).
- **Multiple News Sources**: Scrapes from various platforms, including TechCrunch and CNN.
- **Category Filtering**: Organizes news based on website categories (e.g., AI, technology).
  - _Limitation_: Direct mapping can be restrictive for overlapping topics (e.g., AI, technology, apps) categorized differently across sites.
- **Customizable Prompts**: Allows users to tailor the AI summarization prompt.
- **Email Delivery**: Sends formatted HTML emails using SendGrid.

## How it Works

1.  **Phase 1: Initial Scraping**:
    - Fetches headlines, URLs, and short descriptions from news source category or search result pages.
    - Focuses on readily available information on listing pages.
    - Defers full article content download to save bandwidth and processing time.
2.  **Phase 2: AI Selection**:
    - Employs OpenAI to analyze headlines and descriptions.
    - Selects articles based on user-defined interests (e.g., AI, tech innovations).
3.  **Phase 3: Detailed Scraping**:
    - Fetches full content only for the AI-selected articles.
    - Optimizes bandwidth and processing by scraping only necessary content.
4.  **Phase 4: Summarization**:
    - Sends selected articles to GPT-4o for summarization.
    - Creates a personalized digest highlighting key information.
5.  **Phase 5: Email Delivery**:
    - Formats the summary into an HTML email.
    - Sends the digest to specified recipients via SendGrid.

## Usage

### Basic Run

```bash
python -m __main__ --test
```

### Custom Run

```bash
python -m __main__ --test --categories ai,technology --emails someone@example.com --interests "AI in education, GPT-4o updates"
```

## Configuration

Key settings are configured via environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key for summarization.
- `SENDGRID_API_KEY`: Your SendGrid API key for email delivery.

## Scraper System Design

The news scraping functionality is modular and easily extensible, utilizing a base scraper class and a scraper manager.

- **`scrapers/base.py`**:

  - Defines `NewsArticle`: A `TypedDict` standardizing the structure for fetched news articles (title, URL, description, content, etc.).
  - Defines `NewsScraper(ABC)`: An abstract base class for individual news source scrapers, providing a common interface and shared functionalities (e.g., HTML fetching via `requests`, parsing with `BeautifulSoup`).
  - Concrete scrapers must implement source-specific abstract methods:
    - `_select_article_elements()`: Finds article entries on a category page.
    - `_extract_article_from_list_item()`: Parses basic article info (headline, URL, short description) for Phase 1.
    - `fetch_article_by_url()`: Fetches a single, complete article by its URL.
    - `_extract_article_info()`: Parses full content and details from an individual article page for Phase 3.

- **`scrapers/<source_name>.py`** (e.g., `scrapers/techcrunch.py`, `scrapers/cnn.py`):

  - Each file implements a scraper class inheriting from `NewsScraper`.
  - Contains unique selectors and parsing logic tailored to the specific news website's HTML structure.

- **`scrapers/manager.py`**:
  - Defines `ScraperManager`: A central registry and coordinator for all scrapers.
  - Initializes and stores instances of concrete scrapers (e.g., `TechCrunchScraper()`, `CNNScraper()`) in a dictionary, keyed by a source identifier (e.g., "techcrunch").
  - Provides methods like `fetch_headlines()` (Phase 1) and `fetch_detailed_content()` (Phase 3), delegating work to the appropriate scraper.

### Adding a New News Source

To integrate a new news source (e.g., "NewSite"):

1.  **Create Scraper Module**: Add `scrapers/newsite_scraper.py`.
2.  **Implement Scraper Class**: In `newsite_scraper.py`, define `NewSiteScraper(NewsScraper)`.
    - Implement all `NewsScraper` abstract methods with logic specific to NewSite's website structure.
3.  **Register in `__init__.py`**: In `scrapers/__init__.py`, add `from . import newsite_scraper` to make the module accessible.
4.  **Register in Manager**: In `scrapers/manager.py`:
    - Import the new class: `from .newsite_scraper import NewSiteScraper`.
    - Add an instance to `self.scrapers` in `ScraperManager.__init__`: `"newsite": NewSiteScraper()`. (Use a consistent key for the source).

The `ScraperManager` and main application logic will then automatically support the new source.

## Future Improvements

This section outlines potential enhancements:

### Data Processing and Efficiency

- **Persistent Storage**: Implement a database (e.g., SQLite, PostgreSQL) to store processed article information.
  - Benefits: Avoid reprocessing, save API calls, track article history.
- **Individual Article Summarization**: Summarize selected articles individually (cost permitting).
  - Potential: Reduce AI hallucinations, but increases LLM API costs.

### AI and Personalization

- **Advanced Article Selection**: Explore methods beyond current LLM capabilities for two-phase fetching:
  - Recommendation algorithms (user history, feedback).
  - Retrieval Augmented Generation (RAG) for context-aware selection.
- **Enhanced Category Matching**: Improve category filtering beyond direct website mapping:
  - Fuzzy matching or semantic similarity for user-defined interests, especially for nuanced topics.

### Scraping Capabilities

- **Support for Single Page Applications (SPAs)**: Integrate browser automation (Selenium, Playwright) for JavaScript-driven content.
- **Handling Pagination and Infinite Scrolling**: Enhance scrapers to:
  - Detect and follow "next page" links.
  - Simulate scrolling for sites with infinite scrolling.
