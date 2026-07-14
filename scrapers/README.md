---
related_code:
  - scrapers/base.py
  - scrapers/manager.py
  - scrapers/__init__.py
---

# scrapers package

Nested package docs for the scraper subsystem (discovered via `**/*.md`).

## Built-in sources

| Key           | Class               | Module              |
| ------------- | ------------------- | ------------------- |
| `techcrunch`  | `TechCrunchScraper` | `techcrunch.py`     |
| `cnn`         | `CNNScraper`        | `cnn.py`            |
| `scmp`        | `SCMPScraper`       | `scmp_scraper.py`   |

`ScraperManager` constructs these in `__init__` and exposes
`fetch_headlines` / detailed-content helpers used by `news_fetcher`.

## Adding a source

1. Add `scrapers/<source>_scraper.py` implementing `NewsScraper`.
2. Import the module from `scrapers/__init__.py` if needed for package exports.
3. Register an instance in `ScraperManager.scrapers` with a stable source key.

## SCMP API key

`SCMPScraper` sends an `apikey` header expected by SCMP’s content API. If
requests start returning 401/403, refresh the key from browser Network traffic
to `apigw.scmp.com` (see root README).
