"""Environment-driven settings for the news scraper product."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from self_healing_scraper.settings import Settings as EngineSettings

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Loads ``.env`` / process env, including knobs passed through to the engine."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
        default="postgresql+psycopg://news:news@localhost:5432/news_scraper",
    )
    # Keep in sync with self_healing_scraper.settings.Settings
    llm_api_key: str = ""
    llm_model: str = "gpt-4o"
    llm_base_url: str = ""
    max_repair_attempts: int = 3
    crawl_timeout_ms: int = 30_000
    page_sample_chars: int = 12_000
    cached_page_kinds: frozenset[str] = frozenset({"article"})

    def to_engine(self) -> EngineSettings:
        """Project the app settings into a parameter-only engine Settings."""
        return EngineSettings.model_validate(
            {name: getattr(self, name) for name in EngineSettings.model_fields}
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
