"""Domain models for articles, parsers, and validation results."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class PageKind(StrEnum):
    LISTING = "listing"
    ARTICLE = "article"


class ParserStatus(StrEnum):
    ACTIVE = "active"
    DRAFT = "draft"
    FAILED = "failed"


class FieldExtractor(BaseModel):
    """How to pull one field from a DOM node or page."""

    selector: str
    attr: str = "text"
    many: bool = False


class ParserDefinition(BaseModel):
    """Declarative extraction config stored in the database."""

    js_enabled: bool = True
    wait_for: str | None = None
    item_selector: str | None = None
    fields: dict[str, FieldExtractor] = Field(default_factory=dict)
    source_name: str | None = None


class ValidationCheck(BaseModel):
    type: str
    value: Any | None = None
    field: str | None = None
    fields: list[str] | None = None
    values: list[str] | None = None
    pattern: str | None = None
    message: str | None = None


class ValidationSuite(BaseModel):
    checks: list[ValidationCheck] = Field(default_factory=list)


class NewsArticle(TypedDict, total=False):
    title: str
    url: str
    description: str | None
    published_date: str | None
    source: str
    image_url: str | None
    category: str | None
    content: str | None
    authors: str | None
    tags: str | None
    metadata: dict[str, Any] | None


class ValidationFailure(BaseModel):
    check_type: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    passed: bool
    failures: list[ValidationFailure] = Field(default_factory=list)


class PageContent(BaseModel):
    url: str
    html: str
    markdown: str | None = None
    success: bool = True
    error_message: str | None = None


class GeneratedParser(BaseModel):
    name: str
    url_pattern: str
    page_kind: Literal["listing", "article"]
    definition: ParserDefinition
    validations: ValidationSuite


class ScrapeResult(BaseModel):
    url: str
    articles: list[NewsArticle]
    parser_id: str | None = None
    parser_version: int | None = None
    created_parser: bool = False
    repaired: bool = False
    attempts: int = 1
