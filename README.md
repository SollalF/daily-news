# news-scraper

Self-healing, database-backed **news** scraper built on [`self-healing-scraper`](https://github.com/SollalF/self-healing-scraper). Pass a URL; the product looks up a declarative parser by URL regex, creates one with AI if missing, runs it against a Crawl4AI-rendered page (SSR + SPA), validates the output with news-aware checks, and repairs the parser when checks fail.

## Quick start

```bash
# 1. Dependencies
uv sync
uv run playwright install chromium   # used by Crawl4AI via the engine
# or: uv run crawl4ai-setup

# 2. Postgres (local)
docker compose up -d
cp .env.example .env
# set LLM_API_KEY in .env (and LLM_BASE_URL / LLM_MODEL if not using OpenAI)

# 3. Schema
uv run alembic upgrade head
# (or let scrape_news_url create tables via init_db)

# 4. Library
PYTHONPATH=src uv run python -c "
import asyncio
from news_scraper import scrape_news_url
print(asyncio.run(scrape_news_url('https://techcrunch.com/latest/')))
"

# 5. CLI convenience
PYTHONPATH=src uv run python news_scrape.py https://techcrunch.com/latest/
# or: PYTHONPATH=src uv run python -m news_scraper https://techcrunch.com/latest/
```

### Local engine development

To develop against a local checkout of the engine:

```toml
# in pyproject.toml [tool.uv.sources]
self-healing-scraper = { path = "../self-healing-scraper", editable = true }
```

Then `uv sync` again.

### Tests

```bash
PYTHONPATH=src uv run pytest -m "not live"
PYTHONPATH=src uv run pytest -m live   # Postgres + LLM_API_KEY + network
```

## Public API

```python
from news_scraper import scrape_news_url, scrape_news_urls

result = await scrape_news_url("https://techcrunch.com/latest/")
# result.articles -> list[NewsArticle]
# result.parser_id / parser_version / created_parser / repaired
```

## How it works

1. Normalize URL and fetch HTML via the engine (Crawl4AI / Playwright).
2. Find an active parser whose `url_pattern` regex matches (longest match wins).
3. If none exists, ask the AI for a declarative `definition` + `validations` suite; store in Postgres.
4. Execute CSS extractors → `NewsArticle` list.
5. Run runtime validations (core + news-specific checks).
6. On failure, pass parser + page sample + errors back to the AI, bump version, retry (default 3).

Parsers are JSON configs (selectors, wait rules, field maps), not executable Python. Persistence (Postgres / Alembic) lives in this product; the engine only sees a `ParserStore`.

## Configuration

| Env | Default | Purpose |
|-----|---------|---------|
| `DATABASE_URL` | local Docker Postgres URL | SQLAlchemy async URL (`postgresql+psycopg://...`) |
| `LLM_API_KEY` | — | Required to create/repair parsers |
| `LLM_MODEL` | `gpt-4o` | Model for parser agent |
| `LLM_BASE_URL` | — | OpenAI-compatible API base (e.g. `https://api.moonshot.ai/v1` for Kimi) |
| `MAX_REPAIR_ATTEMPTS` | `3` | Self-heal loop limit |
| `CRAWL_TIMEOUT_MS` | `30000` | Page load timeout |
| `PAGE_SAMPLE_CHARS` | `12000` | HTML sample size sent to the AI |

Same schema works against Neon, Supabase, RDS, etc. by changing `DATABASE_URL`.

## Layout

```
src/news_scraper/
  scrape.py           # thin façade → self-healing-scraper
  domain/             # news prompts + validators
  db/                 # SQLAlchemy + ParserRepository (ParserStore)
alembic/              # migrations
tests/
docker-compose.yml    # local Postgres
```
