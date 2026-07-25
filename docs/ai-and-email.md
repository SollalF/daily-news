---
related_code:
  - src/ai_services.py
  - src/email_sender.py
---

# AI and email

## AI (`src/ai_services.py`)

- **`select_articles`** — sends titles/descriptions to the model; expects a JSON
  list of URLs to scrape in detail.
- **`summarize_articles`** — builds the HTML digest from full articles and user
  interests.

Prompts and model name come from `settings.ai`.

## Email (`src/email_sender.py`)

- **`send_news_email`** — wraps SendGrid `Mail` + `SendGridAPIClient`.
- Subject/from/recipients default from `settings.email`.
