"""URL-regex registry matching (no database required)."""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from typing import cast

from news_scraper.db.models import ParserRecord
from news_scraper.db.repository import ParserRepository


def _parser(pattern: str, version: int = 1, status: str = "active") -> ParserRecord:
    return cast(
        ParserRecord,
        SimpleNamespace(
            id=uuid.uuid4(),
            url_pattern=pattern,
            version=version,
            status=status,
        ),
    )


def test_best_match_prefers_longer_pattern() -> None:
    parsers = [
        _parser(r"https://techcrunch\.com/.*"),
        _parser(r"https://techcrunch\.com/latest/?"),
    ]
    match = ParserRepository._best_match("https://techcrunch.com/latest/", parsers)
    assert match is not None
    assert match.url_pattern == r"https://techcrunch\.com/latest/?"


def test_best_match_returns_none_when_no_match() -> None:
    parsers = [_parser(r"https://cnn\.com/.*")]
    match = ParserRepository._best_match("https://techcrunch.com/latest/", parsers)
    assert match is None


def test_best_match_skips_invalid_regex() -> None:
    parsers = [_parser(r"(unclosed"), _parser(r"https://techcrunch\.com/.*")]
    match = ParserRepository._best_match("https://techcrunch.com/x", parsers)
    assert match is not None
    assert "techcrunch" in match.url_pattern
