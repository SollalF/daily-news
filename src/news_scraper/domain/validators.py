"""News-specific validation checks registered into NEWS_DOMAIN."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, cast

from self_healing_scraper.domain import CheckFn
from self_healing_scraper.models import (
    PageContent,
    ValidationCheck,
    ValidationFailure,
)

NEWS_KNOWN_CHECKS = frozenset(
    {
        "title_min_length",
        "content_min_length",
        "date_parseable",
        "description_not_boilerplate",
    }
)


def check_title_min_length(
    check: ValidationCheck,
    items: list[dict[str, Any]],
    page: PageContent | None,
) -> ValidationFailure | None:
    minimum = int(check.value if check.value is not None else 5)
    short = [
        str(item.get("title", ""))
        for item in items
        if len(str(item.get("title") or "").strip()) < minimum
    ]
    if short:
        return ValidationFailure(
            check_type=check.type,
            message=check.message or f"Titles shorter than {minimum} characters",
            details={"titles": short[:10]},
        )
    return None


def check_content_min_length(
    check: ValidationCheck,
    items: list[dict[str, Any]],
    page: PageContent | None,
) -> ValidationFailure | None:
    minimum = int(check.value if check.value is not None else 40)
    short = [
        str(item.get("url", ""))
        for item in items
        if len(str(item.get("content") or "").strip()) < minimum
    ]
    if short:
        return ValidationFailure(
            check_type=check.type,
            message=check.message or f"Content shorter than {minimum} characters",
            details={"urls": short[:10]},
        )
    return None


def check_date_parseable(
    check: ValidationCheck,
    items: list[dict[str, Any]],
    page: PageContent | None,
) -> ValidationFailure | None:
    field = check.field or "published_date"
    bad = []
    for item in items:
        value = item.get(field)
        if value is None or value == "":
            continue
        if not _looks_like_date(str(value)):
            bad.append(str(value))
    if bad:
        return ValidationFailure(
            check_type=check.type,
            message=check.message or f"Field '{field}' is not a parseable date",
            details={"values": bad[:10]},
        )
    return None


def check_description_not_boilerplate(
    check: ValidationCheck,
    items: list[dict[str, Any]],
    page: PageContent | None,
) -> ValidationFailure | None:
    banned = {
        "no description available.",
        "no description available",
        "read more",
        "subscribe",
    }
    extra = {v.strip().lower() for v in (check.values or [])}
    banned |= extra
    hits = [
        str(item.get("description", ""))
        for item in items
        if str(item.get("description") or "").strip().lower() in banned
    ]
    if hits:
        return ValidationFailure(
            check_type=check.type,
            message=check.message or "Description looks like boilerplate",
            details={"hits": hits[:10]},
        )
    return None


def _looks_like_date(value: str) -> bool:
    value = value.strip()
    candidates = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%b %d, %Y",
        "%B %d, %Y",
        "%d %b %Y",
        "%d %B %Y",
    ]
    for fmt in candidates:
        try:
            datetime.strptime(value[:26], fmt)
            return True
        except ValueError:
            continue
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}", value))


NEWS_EXTRA_VALIDATORS: dict[str, CheckFn] = {
    "title_min_length": cast(CheckFn, check_title_min_length),
    "content_min_length": cast(CheckFn, check_content_min_length),
    "date_parseable": cast(CheckFn, check_date_parseable),
    "description_not_boilerplate": cast(CheckFn, check_description_not_boilerplate),
}
