from typing import Any, cast

from self_healing_scraper.models import PageContent, ValidationCheck, ValidationSuite
from self_healing_scraper.runtime.validators import run_validations

from news_scraper.domain import NEWS_DOMAIN
from news_scraper.models import NewsArticle


def _as_items(articles: list[NewsArticle]) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], articles)


def test_validations_pass(
    sample_articles: list[NewsArticle], listing_validations: ValidationSuite
) -> None:
    page = PageContent(url="https://techcrunch.com/latest/", html="<html></html>")
    result = run_validations(
        _as_items(sample_articles), listing_validations, page, domain=NEWS_DOMAIN
    )
    assert result.passed


def test_min_count_fails(sample_articles: list[NewsArticle]) -> None:
    suite = ValidationSuite(checks=[ValidationCheck(type="min_count", value=10)])
    result = run_validations(
        _as_items(sample_articles), suite, None, domain=NEWS_DOMAIN
    )
    assert not result.passed
    assert result.failures[0].check_type == "min_count"


def test_field_min_length_fails(sample_articles: list[NewsArticle]) -> None:
    articles = list(sample_articles)
    articles[0] = {**articles[0], "title": "Hi"}
    suite = ValidationSuite(
        checks=[ValidationCheck(type="field_min_length", field="title", value=5)]
    )
    result = run_validations(_as_items(articles), suite, None, domain=NEWS_DOMAIN)
    assert not result.passed
    assert result.failures[0].check_type == "field_min_length"


def test_date_parseable_via_core(sample_articles: list[NewsArticle]) -> None:
    articles = list(sample_articles)
    articles[0] = {**articles[0], "published_date": "yesterday"}
    suite = ValidationSuite(
        checks=[ValidationCheck(type="date_parseable", field="published_date")]
    )
    result = run_validations(_as_items(articles), suite, None, domain=NEWS_DOMAIN)
    assert not result.passed
    assert result.failures[0].check_type == "date_parseable"


def test_not_equals_banned_title(sample_articles: list[NewsArticle]) -> None:
    articles = list(sample_articles)
    articles[0] = {**articles[0], "title": "Home"}
    suite = ValidationSuite(
        checks=[
            ValidationCheck(type="not_equals", field="title", values=["Home", "Latest"])
        ]
    )
    result = run_validations(_as_items(articles), suite, None, domain=NEWS_DOMAIN)
    assert not result.passed
