---
related_code:
  - ai_services.py
  - email_sender.py
---

# AI and email

## AI (`ai_services.py`)

`AIService` wraps the OpenAI client:

- **`select_articles`** — from Phase 1 headlines, returns URLs to scrape in
  detail (JSON list shaped by `settings.ai.article_selection_template`).
- **Summarization** — builds the digest string included in the outbound email.

Errors surface as `AIServiceError` subclasses when the model returns an empty
or malformed selection.

## Email (`email_sender.py`)

`send_news_email(news_data, to_emails, news_summary)` builds an HTML message
with SendGrid and returns `{ statusCode, body }`. Subject and from-address come
from `settings.email`.
