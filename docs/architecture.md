---
related_code:
  - __main__.py
  - news_fetcher.py
  - ai_services.py
  - email_sender.py
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

`__main__.py` parses CLI flags (`--test`, `--categories`, `--emails`,
`--interests`), loads `settings`, then calls `main()`.

```bash
python -m __main__ --test
python -m __main__ --test --categories ai,technology --emails someone@example.com
```
