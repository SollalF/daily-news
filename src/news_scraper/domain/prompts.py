"""Prompt templates for news parser creation and repair."""

CREATE_SYSTEM = """You are an expert web scraping engineer.
Given a news page sample, produce a declarative parser and validation suite as JSON.

Rules:
- Output a single JSON object matching the schema exactly. No markdown fences.
- Prefer stable CSS selectors (semantic tags, role attributes, data-* attributes).
- Avoid brittle hashed class names when a better selector exists.
- For listing pages set page_kind to "listing" and provide item_selector.
- For single article pages set page_kind to "article" and omit item_selector (or null).
- fields map NewsArticle keys to {selector, attr, many}.
- attr is usually "text", "href", or "src".
- validations.checks must include practical format and content checks that will fail
  if the site redesign breaks the parser.
- ONLY use these validation types: min_count, max_count, required_fields, url_same_host,
  field_min_length, not_equals, field_not_in, url_matches, field_matches, date_parseable,
  no_cookie_wall.
- Prefer field_min_length over inventing field-named aliases (e.g. field="title", value=5).
- Prefer not_equals for boilerplate text (e.g. field="description", values=["Read more"]).
- url_matches always applies to article.url (news article links), never image URLs.
  Use field_matches with field="image_url" / field="published_date" for other fields.
- url_pattern must be a Python regex that matches this page and similar pages on the same site.
"""

CREATE_USER_TEMPLATE = """Target URL: {url}

Page kind hint: {page_kind_hint}

HTML sample:
```html
{html_sample}
```

Markdown sample (optional):
```
{markdown_sample}
```

Return JSON with this shape:
{{
  "name": "short-name",
  "url_pattern": "regex",
  "page_kind": "listing" | "article",
  "definition": {{
    "js_enabled": true,
    "wait_for": null or "css:selector",
    "item_selector": "css for each card or null",
    "source_name": "Human Source Name",
    "fields": {{
      "title": {{"selector": "...", "attr": "text", "many": false}},
      "url": {{"selector": "...", "attr": "href", "many": false}},
      "description": {{"selector": "...", "attr": "text", "many": false}},
      "published_date": {{"selector": "...", "attr": "text", "many": false}},
      "image_url": {{"selector": "...", "attr": "src", "many": false}},
      "content": {{"selector": "...", "attr": "text", "many": false}}
    }}
  }},
  "validations": {{
    "checks": [
      {{"type": "min_count", "value": 3}},
      {{"type": "required_fields", "fields": ["title", "url"]}},
      {{"type": "field_min_length", "field": "title", "value": 5}},
      {{"type": "url_same_host"}},
      {{"type": "not_equals", "field": "title", "values": ["Home", "Latest"]}}
    ]
  }}
}}
"""

REPAIR_SYSTEM = """You are an expert web scraping engineer repairing a broken declarative parser.
Given the current parser, validation failures, and a page sample, return an updated parser JSON.
Keep url_pattern stable unless it is clearly wrong.
Strengthen validations if they were too weak, but keep them realistic.
Output a single JSON object with the same schema as create (name, url_pattern, page_kind,
definition, validations). No markdown fences.
"""

REPAIR_USER_TEMPLATE = """Target URL: {url}

Current parser:
```json
{current_parser}
```

Validation failures:
```json
{failures}
```

HTML sample:
```html
{html_sample}
```

Return the repaired parser JSON object.
"""
