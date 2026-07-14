---
related_code:
  - settings.py
---

# Configuration

All runtime knobs live in `settings.py` (Pydantic settings). Values come from
environment variables and an optional `.env` next to that module.

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
`python -m __main__` instead of editing defaults.
