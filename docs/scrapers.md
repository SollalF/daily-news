---
related_code:
  - scrapers/
---

# Scrapers

News sources are pluggable classes under `scrapers/`, coordinated by
`ScraperManager`.

## Layout

| Path                     | Role                                              |
| ------------------------ | ------------------------------------------------- |
| `scrapers/base.py`       | `NewsArticle` TypedDict and `NewsScraper` ABC     |
| `scrapers/manager.py`    | Registry + `fetch_headlines` / detailed fetch API |
| `scrapers/techcrunch.py` | TechCrunch HTML scraper                           |
| `scrapers/cnn.py`        | CNN HTML scraper                                  |
| `scrapers/scmp_scraper.py` | SCMP content API scraper                        |

## Contract

Concrete scrapers implement:

- `_select_article_elements` — list-page article nodes
- `_extract_article_from_list_item` — Phase 1 title / URL / description
- `fetch_article_by_url` — full article fetch
- `_extract_article_info` — Phase 3 body and metadata

See the package-local [scrapers/README.md](../scrapers/README.md) for how to
add a source.
