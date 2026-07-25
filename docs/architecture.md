---
related_code:
  - src/daily_news.py
  - src/news_fetcher.py
  - src/ai_services.py
  - src/email_sender.py
---

# Architecture

Daily News Digest runs a five-phase pipeline from CLI / module entry to email.

## Phases

1. **Initial scraping** — `news_fetcher.fetch_initial_article_list` gathers
   headlines and short descriptions via `scrapers.manager.ScraperManager`.
2. **AI selection** — `ai_services.select_articles` picks which URLs deserve a
   full scrape, using user interests from settings or CLI args.
3. **Detailed scraping** — selected URLs are fetched in full through the same
   scraper manager.
4. **Summarization** — `ai_services` asks GPT for a personalized digest.
5. **Email delivery** — `email_sender.send_news_email` sends HTML via SendGrid.

## Entry

`src/daily_news.py` parses CLI flags (`--test`, `--categories`, `--emails`,
`--interests`), loads `settings`, then calls `main()`.

```bash
PYTHONPATH=src python -m daily_news --test
PYTHONPATH=src python -m daily_news --test --categories ai,technology --emails someone@example.com
```
