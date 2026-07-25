---
related_code:
  - tests/
  - src/scrapers/
  - src/news_fetcher.py
  - src/ai_services.py
  - src/email_sender.py
  - src/daily_news.py
---

# tests

Pytest suite covering scrapers, AI selection/summarization helpers, the news
fetcher pipeline, email sending, and CLI / `main` wiring.

Shared fixtures live in `conftest.py`. Run from the repo root:

```bash
pytest
```
