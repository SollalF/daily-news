"""AI-assisted parser repair."""

from __future__ import annotations

import json

from news_scraper.agent.llm import complete_json
from news_scraper.agent.normalize import normalize_generated_payload
from news_scraper.agent.prompts import REPAIR_SYSTEM, REPAIR_USER_TEMPLATE
from news_scraper.models import (
    GeneratedParser,
    PageContent,
    ParserDefinition,
    ValidationResult,
    ValidationSuite,
)
from news_scraper.settings import Settings, get_settings


async def repair_parser(
    *,
    page: PageContent,
    name: str,
    url_pattern: str,
    page_kind: str,
    definition: ParserDefinition,
    validations: ValidationSuite,
    validation_result: ValidationResult,
    settings: Settings | None = None,
) -> GeneratedParser:
    cfg = settings or get_settings()
    current = {
        "name": name,
        "url_pattern": url_pattern,
        "page_kind": page_kind,
        "definition": definition.model_dump(),
        "validations": validations.model_dump(),
    }
    payload = await complete_json(
        system=REPAIR_SYSTEM,
        user=REPAIR_USER_TEMPLATE.format(
            url=page.url,
            current_parser=json.dumps(current, indent=2),
            failures=validation_result.model_dump_json(indent=2),
            html_sample=page.html[: cfg.page_sample_chars],
        ),
        settings=cfg,
    )
    # Preserve identity fields if the model omits them.
    payload.setdefault("name", name)
    payload.setdefault("url_pattern", url_pattern)
    payload.setdefault("page_kind", page_kind)
    return GeneratedParser.model_validate(normalize_generated_payload(payload))
