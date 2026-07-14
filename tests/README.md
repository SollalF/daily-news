---
related_code:
  - tests/
  - scrapers/
  - news_fetcher.py
  - ai_services.py
  - email_sender.py
  - __main__.py
---

# tests

Pytest suite covering scrapers, AI selection/summarization helpers, the news
fetcher pipeline, email sending, and CLI / `main` wiring.

Shared fixtures live in `conftest.py`. Run from the repo root:

```bash
pytest
```
