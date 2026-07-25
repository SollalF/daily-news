---
related_code:
  - src/settings.py
---

# Configuration

All runtime knobs live in `src/settings.py` (Pydantic settings). Values come from
environment variables and an optional `.env` at the repo root.

## Required secrets

| Variable           | Purpose                          |
| ------------------ | -------------------------------- |
| `OPENAI_API_KEY`   | GPT article selection + summary  |
| `SENDGRID_API_KEY` | Outbound digest email            |

## Notable defaults

- **Email** — from-address, subject template, default recipients
- **AI** — model (`gpt-4o`), system message, selection / summary prompt templates
- **News** — default categories, max articles per category, user interests

Override categories, interests, and recipients on the CLI when running
`PYTHONPATH=src python -m daily_news` instead of editing defaults.
