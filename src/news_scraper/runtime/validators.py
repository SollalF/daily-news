"""Runtime validation suite for scrape outputs."""

from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import urlparse

from news_scraper.models import (
    NewsArticle,
    PageContent,
    ValidationCheck,
    ValidationFailure,
    ValidationResult,
    ValidationSuite,
)

COOKIE_WALL_SNIPPETS = (
    "accept all cookies",
    "we use cookies",
    "enable javascript",
    "please enable cookies",
    "subscribe to continue",
    "sign in to continue reading",
)


def run_validations(
    articles: list[NewsArticle],
    suite: ValidationSuite,
    page: PageContent | None = None,
) -> ValidationResult:
    failures: list[ValidationFailure] = []
    for check in suite.checks:
        failure = _run_check(check, articles, page)
        if failure:
            failures.append(failure)
    return ValidationResult(passed=not failures, failures=failures)


KNOWN_CHECKS = frozenset(
    {
        "min_count",
        "max_count",
        "required_fields",
        "url_same_host",
        "title_min_length",
        "content_min_length",
        "field_min_length",
        "not_equals",
        "field_not_in",
        "url_matches",
        "field_matches",
        "date_parseable",
        "no_cookie_wall",
        "description_not_boilerplate",
    }
)


def _run_check(
    check: ValidationCheck,
    articles: list[NewsArticle],
    page: PageContent | None,
) -> ValidationFailure | None:
    handlers = {
        "min_count": _check_min_count,
        "max_count": _check_max_count,
        "required_fields": _check_required_fields,
        "url_same_host": _check_url_same_host,
        "title_min_length": _check_title_min_length,
        "content_min_length": _check_content_min_length,
        "field_min_length": _check_field_min_length,
        "not_equals": _check_not_equals,
        "field_not_in": _check_not_equals,
        "url_matches": _check_url_matches,
        "field_matches": _check_field_matches,
        "date_parseable": _check_date_parseable,
        "no_cookie_wall": _check_no_cookie_wall,
        "description_not_boilerplate": _check_description_not_boilerplate,
    }
    handler = handlers.get(check.type)
    if handler is None:
        # Ignore invented check types so AI creativity does not hard-fail a scrape.
        return None
    return handler(check, articles, page)


def _check_min_count(
    check: ValidationCheck, articles: list[NewsArticle], page: PageContent | None
) -> ValidationFailure | None:
    minimum = int(check.value if check.value is not None else 1)
    if len(articles) < minimum:
        return ValidationFailure(
            check_type=check.type,
            message=check.message
            or f"Expected at least {minimum} articles, got {len(articles)}",
            details={"count": len(articles), "minimum": minimum},
        )
    return None


def _check_max_count(
    check: ValidationCheck, articles: list[NewsArticle], page: PageContent | None
) -> ValidationFailure | None:
    maximum = int(check.value if check.value is not None else 500)
    if len(articles) > maximum:
        return ValidationFailure(
            check_type=check.type,
            message=check.message
            or f"Expected at most {maximum} articles, got {len(articles)}",
            details={"count": len(articles), "maximum": maximum},
        )
    return None


def _check_required_fields(
    check: ValidationCheck, articles: list[NewsArticle], page: PageContent | None
) -> ValidationFailure | None:
    fields = check.fields or ["title", "url"]
    missing: list[dict[str, str]] = []
    for index, article in enumerate(articles):
        for field in fields:
            value = article.get(field)  # type: ignore[literal-required]
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append({"index": str(index), "field": field})
    if missing:
        return ValidationFailure(
            check_type=check.type,
            message=check.message or "Required fields missing on one or more articles",
            details={"missing": missing[:20]},
        )
    return None


def _check_url_same_host(
    check: ValidationCheck, articles: list[NewsArticle], page: PageContent | None
) -> ValidationFailure | None:
    if page is None:
        return None
    host = _normalize_host(urlparse(page.url).netloc)
    bad = [
        article.get("url", "")
        for article in articles
        if _normalize_host(urlparse(article.get("url", "")).netloc) != host
    ]
    if bad:
        return ValidationFailure(
            check_type=check.type,
            message=check.message or "Article URLs must share the page host",
            details={"bad_urls": bad[:10], "host": host},
        )
    return None


def _check_title_min_length(
    check: ValidationCheck, articles: list[NewsArticle], page: PageContent | None
) -> ValidationFailure | None:
    minimum = int(check.value if check.value is not None else 5)
    short = [
        article.get("title", "")
        for article in articles
        if len((article.get("title") or "").strip()) < minimum
    ]
    if short:
        return ValidationFailure(
            check_type=check.type,
            message=check.message or f"Titles shorter than {minimum} characters",
            details={"titles": short[:10]},
        )
    return None


def _check_content_min_length(
    check: ValidationCheck, articles: list[NewsArticle], page: PageContent | None
) -> ValidationFailure | None:
    minimum = int(check.value if check.value is not None else 40)
    short = [
        article.get("url", "")
        for article in articles
        if len((article.get("content") or "").strip()) < minimum
    ]
    if short:
        return ValidationFailure(
            check_type=check.type,
            message=check.message or f"Content shorter than {minimum} characters",
            details={"urls": short[:10]},
        )
    return None


def _check_field_min_length(
    check: ValidationCheck, articles: list[NewsArticle], page: PageContent | None
) -> ValidationFailure | None:
    field = check.field or "title"
    minimum = int(check.value if check.value is not None else 1)
    short = []
    for article in articles:
        value = article.get(field)  # type: ignore[literal-required]
        text = value if isinstance(value, str) else ""
        if len(text.strip()) < minimum:
            short.append(article.get("url", ""))
    if short:
        return ValidationFailure(
            check_type=check.type,
            message=check.message or f"Field '{field}' shorter than {minimum}",
            details={"field": field, "urls": short[:10]},
        )
    return None


def _check_not_equals(
    check: ValidationCheck, articles: list[NewsArticle], page: PageContent | None
) -> ValidationFailure | None:
    field = check.field or "title"
    banned = {v.strip().lower() for v in (check.values or []) if v}
    if not banned:
        return None
    hits = []
    for article in articles:
        value = article.get(field)  # type: ignore[literal-required]
        if isinstance(value, str) and value.strip().lower() in banned:
            hits.append(value)
    if hits:
        return ValidationFailure(
            check_type=check.type,
            message=check.message or f"Field '{field}' matched banned values",
            details={"hits": hits[:10]},
        )
    return None


def _check_url_matches(
    check: ValidationCheck, articles: list[NewsArticle], page: PageContent | None
) -> ValidationFailure | None:
    # Force field=url so models cannot accidentally pattern-match image URLs here.
    scoped = check.model_copy(update={"field": "url"})
    return _check_field_matches(scoped, articles, page)


def _check_field_matches(
    check: ValidationCheck, articles: list[NewsArticle], page: PageContent | None
) -> ValidationFailure | None:
    pattern = check.pattern
    if not pattern:
        return None
    field = check.field or "url"
    compiled = re.compile(pattern)
    bad = []
    for article in articles:
        value = article.get(field)  # type: ignore[literal-required]
        text = value if isinstance(value, str) else ""
        if text and not compiled.search(text):
            bad.append(text)
    if bad:
        return ValidationFailure(
            check_type=check.type,
            message=check.message or f"Field '{field}' did not match expected pattern",
            details={"values": bad[:10], "pattern": pattern, "field": field},
        )
    return None


def _check_date_parseable(
    check: ValidationCheck, articles: list[NewsArticle], page: PageContent | None
) -> ValidationFailure | None:
    field = check.field or "published_date"
    bad = []
    for article in articles:
        value = article.get(field)  # type: ignore[literal-required]
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


def _check_no_cookie_wall(
    check: ValidationCheck, articles: list[NewsArticle], page: PageContent | None
) -> ValidationFailure | None:
    texts: list[str] = []
    if page and page.html:
        texts.append(page.html.lower()[:5000])
    for article in articles:
        texts.append((article.get("content") or "").lower())
        texts.append((article.get("description") or "").lower())
    blob = "\n".join(texts)
    for snippet in COOKIE_WALL_SNIPPETS:
        if snippet in blob and not articles:
            return ValidationFailure(
                check_type=check.type,
                message=check.message or f"Possible cookie/paywall text: {snippet}",
            )
    # If we have articles but every content looks like a wall, fail.
    if articles:
        wall_hits = 0
        for article in articles:
            content = (
                article.get("content") or article.get("description") or ""
            ).lower()
            if any(snippet in content for snippet in COOKIE_WALL_SNIPPETS):
                wall_hits += 1
        if wall_hits and wall_hits == len(articles):
            return ValidationFailure(
                check_type=check.type,
                message=check.message
                or "All articles look like cookie/paywall content",
            )
    return None


def _check_description_not_boilerplate(
    check: ValidationCheck, articles: list[NewsArticle], page: PageContent | None
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
        article.get("description", "")
        for article in articles
        if (article.get("description") or "").strip().lower() in banned
    ]
    if hits:
        return ValidationFailure(
            check_type=check.type,
            message=check.message or "Description looks like boilerplate",
            details={"hits": hits[:10]},
        )
    return None


def _normalize_host(host: str) -> str:
    host = host.lower()
    return host[4:] if host.startswith("www.") else host


def _looks_like_date(value: str) -> bool:
    value = value.strip()
    # ISO-ish or common news formats
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
