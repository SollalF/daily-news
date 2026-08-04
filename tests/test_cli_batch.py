"""CLI helpers for batch scrape."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

from typer.testing import CliRunner

from news_scraper.cli import _urls_from_stdin, app, main
from news_scraper.models import BatchScrapeResult, BatchUrlResult


def test_urls_from_stdin_json_array() -> None:
    with patch("news_scraper.cli.sys.stdin") as stdin:
        stdin.read.return_value = json.dumps(
            ["https://a.example/", "https://b.example/"]
        )
        assert _urls_from_stdin() == ["https://a.example/", "https://b.example/"]


def test_urls_from_stdin_object() -> None:
    with patch("news_scraper.cli.sys.stdin") as stdin:
        stdin.read.return_value = json.dumps({"urls": ["https://a.example/"]})
        assert _urls_from_stdin() == ["https://a.example/"]


def test_urls_from_stdin_lines() -> None:
    with patch("news_scraper.cli.sys.stdin") as stdin:
        stdin.read.return_value = "https://a.example/\n\nhttps://b.example/\n"
        assert _urls_from_stdin() == ["https://a.example/", "https://b.example/"]


def test_batch_command_prints_envelope_and_exits_2_on_partial_failure() -> None:
    batch = BatchScrapeResult(
        results=[
            BatchUrlResult(
                url="https://ok.example/",
                ok=True,
                articles=[{"title": "T", "url": "https://ok.example/a"}],
            ),
            BatchUrlResult(
                url="https://bad.example/",
                ok=False,
                error="fetch failed",
            ),
        ]
    )
    runner = CliRunner()
    with (
        patch("news_scraper.cli.get_settings"),
        patch(
            "news_scraper.cli.scrape_news_urls_resilient",
            new=AsyncMock(return_value=batch),
        ),
    ):
        result = runner.invoke(
            app,
            ["batch", "https://ok.example/", "https://bad.example/", "--compact"],
        )

    assert result.exit_code == 2, result.stdout or str(result.exception)
    payload = json.loads(result.stdout)
    assert payload["results"][0]["ok"] is True
    assert payload["results"][1]["error"] == "fetch failed"


def test_batch_command_requires_urls() -> None:
    runner = CliRunner()
    with (
        patch("news_scraper.cli.get_settings"),
        patch("news_scraper.cli._urls_from_stdin", return_value=[]),
    ):
        result = runner.invoke(app, ["batch"])

    assert result.exit_code == 1
    assert "Provide one or more URLs" in result.stderr


def test_url_shortcut_rewrites_to_scrape() -> None:
    with patch("news_scraper.cli.app") as mocked_app:
        main(["https://example.com/latest/", "-v"])
    mocked_app.assert_called_once_with(
        args=["scrape", "https://example.com/latest/", "-v"]
    )


def test_batch_subcommand_not_rewritten() -> None:
    with patch("news_scraper.cli.app") as mocked_app:
        main(["batch", "https://example.com/latest/"])
    mocked_app.assert_called_once_with(args=["batch", "https://example.com/latest/"])
