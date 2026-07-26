"""Apply declarative parser definitions to fetched HTML."""

from __future__ import annotations

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from news_scraper.models import (
    FieldExtractor,
    NewsArticle,
    PageContent,
    PageKind,
    ParserDefinition,
)


def execute_parser(
    page: PageContent,
    definition: ParserDefinition,
    page_kind: str,
) -> list[NewsArticle]:
    soup = BeautifulSoup(page.html or "", "html.parser")
    source = definition.source_name or _guess_source(page.url)

    if page_kind == PageKind.ARTICLE.value or not definition.item_selector:
        article = _extract_from_root(soup, page.url, definition, source)
        return (
            [article] if article and article.get("title") and article.get("url") else []
        )

    items = soup.select(definition.item_selector)
    articles: list[NewsArticle] = []
    for item in items:
        article = _extract_from_element(item, page.url, definition, source)
        if article and article.get("title") and article.get("url"):
            articles.append(article)
    return articles


def _extract_from_root(
    soup: BeautifulSoup,
    page_url: str,
    definition: ParserDefinition,
    source: str,
) -> NewsArticle | None:
    return _build_article(soup, page_url, definition, source, default_url=page_url)


def _extract_from_element(
    element: Tag,
    page_url: str,
    definition: ParserDefinition,
    source: str,
) -> NewsArticle | None:
    return _build_article(element, page_url, definition, source, default_url=None)


def _build_article(
    root: BeautifulSoup | Tag,
    page_url: str,
    definition: ParserDefinition,
    source: str,
    default_url: str | None,
) -> NewsArticle | None:
    data: dict[str, str | None] = {}
    for field_name, extractor in definition.fields.items():
        data[field_name] = _extract_field(root, extractor, page_url)

    title = data.get("title")
    url = data.get("url") or default_url
    if not title or not url:
        return None

    article: NewsArticle = {
        "title": title.strip(),
        "url": url,
        "description": _optional(data.get("description")),
        "published_date": _optional(data.get("published_date")),
        "source": source,
        "image_url": _optional(data.get("image_url")),
        "category": _optional(data.get("category")),
        "content": _optional(data.get("content")),
        "authors": _optional(data.get("authors")),
        "tags": _optional(data.get("tags")),
        "metadata": None,
    }
    return article


def _extract_field(
    root: BeautifulSoup | Tag, extractor: FieldExtractor, page_url: str
) -> str | None:
    nodes = root.select(extractor.selector)
    if not nodes:
        return None

    if extractor.many:
        values = [_node_value(node, extractor.attr, page_url) for node in nodes]
        cleaned = [v for v in values if v]
        return ", ".join(cleaned) if cleaned else None

    return _node_value(nodes[0], extractor.attr, page_url)


def _node_value(node: Tag, attr: str, page_url: str) -> str | None:
    if attr in {"text", "string"}:
        text = node.get_text(" ", strip=True)
        return text or None
    raw = node.get(attr)
    if raw is None:
        return None
    if isinstance(raw, list):
        raw = " ".join(str(part) for part in raw)
    value = str(raw).strip()
    if not value:
        return None
    if attr in {"href", "src"}:
        return urljoin(page_url, value)
    return value


def _optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _guess_source(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host or "unknown"
