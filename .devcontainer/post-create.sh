#!/usr/bin/env bash
set -euo pipefail

cd /workspaces/daily-news-1

if [[ ! -f .env && -f .env.example ]]; then
  cp .env.example .env
  echo "Created .env from .env.example — set LLM_API_KEY before live scrapes."
fi

# Force DB host to the compose service (overrides localhost from .env.example).
if grep -q '^DATABASE_URL=' .env 2>/dev/null; then
  sed -i 's|^DATABASE_URL=.*|DATABASE_URL=postgresql+psycopg://news:news@db:5432/news_scraper|' .env
else
  echo 'DATABASE_URL=postgresql+psycopg://news:news@db:5432/news_scraper' >> .env
fi

uv sync

# Linux Chromium + OS deps — no Windows asyncio loop split needed here.
uv run playwright install --with-deps chromium

uv run alembic upgrade head
