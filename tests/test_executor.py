"""News product still relies on the engine CSS executor for extraction."""

from self_healing_scraper.models import PageContent, ParserDefinition
from self_healing_scraper.runtime.executor import execute_parser


def test_execute_listing_parser(
    listing_page: PageContent, listing_definition: ParserDefinition
) -> None:
    items = execute_parser(listing_page, listing_definition, "listing")
    assert len(items) == 3
    assert items[0]["title"] == "Alpha Story"
    assert items[0]["url"] == "https://techcrunch.com/2026/07/25/alpha/"
    assert items[0]["source"] == "TechCrunch"
    assert items[1]["title"] == "Beta Story"
