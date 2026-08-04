"""Thin CLI around the library API."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from collections.abc import Sequence
from typing import Annotated

import typer

from news_scraper.scrape import scrape_news_url, scrape_news_urls_resilient
from news_scraper.settings import get_settings

app = typer.Typer(
    name="news-scrape",
    help="Scrape a news URL with self-healing declarative parsers.",
    add_completion=False,
    no_args_is_help=True,
)

_SUBCOMMANDS = frozenset({"scrape", "batch"})


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _echo_json(payload: object, *, pretty: bool) -> None:
    if pretty:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        typer.echo(json.dumps(payload, ensure_ascii=False))


def _urls_from_stdin() -> list[str]:
    """Read URLs from stdin: JSON array, {\"urls\": [...]}, or newline-separated."""
    raw = sys.stdin.read().strip()
    if not raw:
        return []
    if raw.startswith("[") or raw.startswith("{"):
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
        if isinstance(parsed, dict) and "urls" in parsed:
            return [str(item) for item in parsed["urls"]]
        raise typer.BadParameter(
            "stdin JSON must be a URL array or an object with a 'urls' key"
        )
    return [line.strip() for line in raw.splitlines() if line.strip()]


@app.command("scrape")
def scrape_command(
    url: str = typer.Argument(..., help="News listing or article URL"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    pretty: bool = typer.Option(True, "--pretty/--compact"),
) -> None:
    """Scrape a URL and print articles as JSON."""
    _configure_logging(verbose)
    get_settings()  # load .env early for clearer errors
    result = asyncio.run(scrape_news_url(url))
    _echo_json(result.model_dump(), pretty=pretty)


@app.command("batch")
def batch_command(
    urls: Annotated[
        list[str] | None,
        typer.Argument(help="News listing or article URLs (omit to read from stdin)"),
    ] = None,
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    pretty: bool = typer.Option(True, "--pretty/--compact"),
) -> None:
    """Scrape many URLs; print one JSON envelope with per-URL success/error."""
    _configure_logging(verbose)
    get_settings()
    resolved = list(urls or [])
    if not resolved:
        resolved = _urls_from_stdin()
    if not resolved:
        typer.echo(
            "Provide one or more URLs as arguments, or pipe a JSON array / "
            "newline-separated list on stdin.",
            err=True,
        )
        raise typer.Exit(code=1)

    batch = asyncio.run(scrape_news_urls_resilient(resolved))
    _echo_json(batch.model_dump(), pretty=pretty)
    if any(not item.ok for item in batch.results):
        raise typer.Exit(code=2)


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entry: ``news-scrape <url>`` is a shortcut for ``scrape <url>``."""
    args = list(sys.argv[1:] if argv is None else argv)
    if args and not args[0].startswith("-") and args[0] not in _SUBCOMMANDS:
        args = ["scrape", *args]
    app(args=args)


if __name__ == "__main__":
    main()
