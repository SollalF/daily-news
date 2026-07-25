---
related_code:
  - src/scrapers/
---

# Scrapers

News sources are pluggable classes under `src/scrapers/`, coordinated by
`ScraperManager`.

## Layout

| Path                         | Role                                              |
| ---------------------------- | ------------------------------------------------- |
| `src/scrapers/base.py`       | `NewsArticle` TypedDict and `NewsScraper` ABC     |
| `src/scrapers/manager.py`    | Registry + `fetch_headlines` / detailed fetch API |
| `src/scrapers/techcrunch.py` | TechCrunch HTML scraper                           |
| `src/scrapers/cnn.py`        | CNN HTML scraper                                  |
| `src/scrapers/scmp_scraper.py` | SCMP content API scraper                        |

## Flow

`news_fetcher` asks the manager for headlines (phase 1), then for full article
bodies for AI-selected URLs (phase 3). Each concrete scraper owns site-specific
CSS/API parsing.

## Extending

See the package-local [scrapers/README.md](../src/scrapers/README.md) for how to
add a source and refresh the SCMP API key.
