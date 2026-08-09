# news-scraper

Self-healing, database-backed **news** scraper built on [`self-healing-scraper`](https://github.com/SollalF/self-healing-scraper). Pass a URL; the product looks up a declarative parser by URL regex, creates one with AI if missing, runs it against a Crawl4AI-rendered page (SSR + SPA), validates the output with news-aware checks, and repairs the parser when checks fail.

## Quick start

### Dev Container (recommended on Windows)

Runs Linux + Postgres + Playwright in Docker (avoids Windows host quirks with
async Postgres + browser scraping).

1. In Cursor/VS Code: **Dev Containers: Reopen in Container**.
2. After `postCreate` finishes, set `LLM_API_KEY` in `.env` and scrape:

```bash
uv run python news_scrape.py https://techcrunch.com/latest/
```

`DATABASE_URL` inside the container points at the compose `db` service.
`self-healing-scraper` is installed from PyPI via `uv sync` (no sibling checkout required).

### Host machine

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

### Tests

```bash
PYTHONPATH=src uv run pytest -m "not live"
PYTHONPATH=src uv run pytest -m live   # Postgres + LLM_API_KEY + network
```

## Public API

```python
from news_scraper import scrape_news_url, scrape_news_urls, scrape_news_urls_resilient

result = await scrape_news_url("https://techcrunch.com/latest/")
# result.articles -> list[NewsArticle]
# result.parser_id / parser_version / created_parser / repaired / from_cache

batch = await scrape_news_urls_resilient(
    ["https://techcrunch.com/latest/", "https://example.com/tech/"]
)
# batch.results[i].ok / .articles / .error — never aborts the whole run
```

### Already-scraped articles are served from Postgres

An article URL that already has a successful row in `scrape_runs` is returned
straight from the database: no fetch, no parser execution, no LLM. The stored
articles never expire, and the newest successful run wins.

- Only article pages qualify. Listings always re-scrape, since they gain new
  items constantly. Override with `CACHED_PAGE_KINDS`.
- A reused result has `from_cache: true` and `attempts: 0`, and does not add a
  new `scrape_runs` row.
- Pass `force_refresh=True` (or `--force-refresh` on the CLI) to re-scrape
  regardless.

```bash
uv run python news_scrape.py https://techcrunch.com/2026/08/01/story/ --force-refresh
```

This matters most for the runbook's step 3: re-running the same top-N article
URLs costs nothing after the first scrape.

### Batch CLI (agent-friendly)

Scrape many listing or article URLs in one process. Per-URL failures become
`ok: false` entries instead of crashing the job.

```bash
# args
uv run python news_scrape.py batch \
  https://techcrunch.com/latest/ \
  https://example.com/tech/ \
  --compact

# or stdin JSON array / {"urls": [...]} / newline-separated URLs
printf '%s\n' '["https://techcrunch.com/latest/"]' \
  | uv run python news_scrape.py batch --compact
```

Exit codes: `0` all URLs succeeded, `2` at least one failed (JSON still printed),
`1` usage error.

Envelope shape:

```json
{
  "results": [
    {
      "url": "https://techcrunch.com/latest/",
      "ok": true,
      "articles": [
        {
          "title": "...",
          "url": "https://techcrunch.com/2026/08/01/story/",
          "description": "...",
          "published_date": "...",
          "source": "TechCrunch"
        }
      ],
      "parser_id": "...",
      "parser_version": 1,
      "created_parser": false,
      "repaired": false,
      "attempts": 1,
      "from_cache": false,
      "error": null
    },
    {
      "url": "https://broken.example/",
      "ok": false,
      "articles": [],
      "error": "Validation failed after 3 repairs: ..."
    }
  ]
}
```

## Newsletter agent runbook (OpenClaw)

daily-news only scrapes. Cron, source list, ranking prompt, and WhatsApp
formatting stay in the agent. Two Python calls per day:

1. **Listings** — batch-scrape your configured source URLs (home / section /
   emergency pages). Flatten successful `articles`; surface any `ok: false`
   errors in the daily message for diagnosis.
2. **Rank** — use your configurable agent prompt (e.g. focus on AI / Hong Kong)
   on title, description, source, and date. Pick top N article URLs.
3. **Articles** — batch-scrape those article URLs with the same CLI.
4. **WhatsApp** — format a short message with titles and hyperlinks (use listing
   blurbs if an article scrape fails).

```bash
# call 1 — sources you configure in the agent
uv run python news_scrape.py batch SOURCE_URL_1 SOURCE_URL_2 --compact

# call 2 — top N chosen by the agent
uv run python news_scrape.py batch ARTICLE_URL_1 ARTICLE_URL_2 --compact
```

Prefer clean section feeds over noisy homepages. Cold sources may create parsers
on first run (`LLM_API_KEY` required); later runs reuse Postgres parsers.

## How it works

1. Normalize the URL and find an active parser whose `url_pattern` regex matches (longest match wins).
2. For article pages, return the newest successful `scrape_runs` row if one exists — no fetch, no LLM.
3. Otherwise fetch HTML via the engine (Crawl4AI / Playwright).
4. If no parser exists, ask the AI for a declarative `definition` + `validations` suite; store in Postgres.
5. Execute CSS extractors → `NewsArticle` list.
6. Run runtime validations (core checks via the engine).
7. On failure, pass parser + page sample + errors back to the AI, bump version, retry (default 3).

Parsers are JSON configs (selectors, wait rules, field maps), not executable Python. Persistence (Postgres / Alembic) lives in this product; the engine only sees a `ParserStore`.

## Configuration

| Env | Default | Purpose |
|-----|---------|---------|
| `DATABASE_URL` | local Docker Postgres URL | SQLAlchemy async URL (`postgresql+psycopg://...`) |
| `LLM_API_KEY` | — | Required to create/repair parsers |
| `LLM_MODEL` | `gpt-4o` | Model for parser agent |
| `LLM_BASE_URL` | — | OpenAI-compatible API base (must match the key; see `.env.example`) |
| `MAX_REPAIR_ATTEMPTS` | `3` | Self-heal loop limit |
| `CRAWL_TIMEOUT_MS` | `30000` | Page load timeout |
| `PAGE_SAMPLE_CHARS` | `12000` | HTML sample size sent to the AI |
| `CACHED_PAGE_KINDS` | `["article"]` | Page kinds served from a stored run instead of re-scraped |

Same schema works against Neon, Supabase, RDS, etc. by changing `DATABASE_URL`.

## Layout

```
src/news_scraper/
  scrape.py           # thin façade → self-healing-scraper (+ resilient batch)
  cli.py              # news-scrape scrape|batch
  domain/             # news prompts + validators
  db/                 # SQLAlchemy + ParserRepository (ParserStore)
alembic/              # migrations
tests/
docker-compose.yml    # host-only Postgres
.devcontainer/        # Linux app + Postgres Dev Container
```
