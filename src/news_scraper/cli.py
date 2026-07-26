"""Thin CLI around the library API."""

from __future__ import annotations

import json
import logging

import typer

from news_scraper.asyncio_compat import run
from news_scraper.scrape import scrape_news_url
from news_scraper.settings import get_settings

app = typer.Typer(
    name="news-scrape",
    help="Scrape a news URL with self-healing declarative parsers.",
    add_completion=False,
)


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


@app.command("scrape")
def scrape_command(
    url: str = typer.Argument(..., help="News listing or article URL"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    pretty: bool = typer.Option(True, "--pretty/--compact"),
) -> None:
    """Scrape a URL and print articles as JSON."""
    _configure_logging(verbose)
    get_settings()  # load .env early for clearer errors
    result = run(scrape_news_url(url))
    payload = result.model_dump()
    if pretty:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        typer.echo(json.dumps(payload, ensure_ascii=False))


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    url: str | None = typer.Argument(
        None, help="News URL (shortcut for `scrape <url>`)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    if ctx.invoked_subcommand is not None:
        return
    if url is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(code=1)
    scrape_command(url=url, verbose=verbose, pretty=True)


if __name__ == "__main__":
    app()
