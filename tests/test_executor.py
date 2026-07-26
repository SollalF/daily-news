from news_scraper.models import PageContent, ParserDefinition
from news_scraper.runtime.executor import execute_parser


def test_execute_listing_parser(
    listing_page: PageContent, listing_definition: ParserDefinition
) -> None:
    articles = execute_parser(listing_page, listing_definition, "listing")
    assert len(articles) == 3
    assert articles[0]["title"] == "Alpha Story"
    assert articles[0]["url"] == "https://techcrunch.com/2026/07/25/alpha/"
    assert articles[0]["source"] == "TechCrunch"
    assert articles[1]["title"] == "Beta Story"


def test_execute_article_parser() -> None:
    html = """
    <html><body>
      <article>
        <h1 class="headline">Solo Piece</h1>
        <div class="body">Lots of article body text for readers.</div>
      </article>
    </body></html>
    """
    page = PageContent(url="https://example.com/a/1", html=html, success=True)
    definition = ParserDefinition(
        item_selector=None,
        source_name="Example",
        fields={
            "title": {"selector": "h1.headline", "attr": "text", "many": False},
            "content": {"selector": "div.body", "attr": "text", "many": False},
        },
    )
    articles = execute_parser(page, definition, "article")
    assert len(articles) == 1
    assert articles[0]["title"] == "Solo Piece"
    assert articles[0]["url"] == "https://example.com/a/1"
    assert "article body" in (articles[0].get("content") or "")
