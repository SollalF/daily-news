from news_scraper.scrape import normalize_url


def test_normalize_url_lowercases_host_and_strips_fragment() -> None:
    assert (
        normalize_url("https://TechCrunch.COM/latest/#top")
        == "https://techcrunch.com/latest/"
    )
