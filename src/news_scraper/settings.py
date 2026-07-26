"""Environment-driven settings for the news scraper product."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from self_healing_scraper.settings import Settings as EngineSettings

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
        default="postgresql+psycopg://news:news@localhost:5432/news_scraper",
    )
    llm_api_key: str = ""
    llm_model: str = "gpt-4o"
    llm_base_url: str = ""
    max_repair_attempts: int = 3
    crawl_timeout_ms: int = 30_000
    page_sample_chars: int = 12_000

    def to_engine(self) -> EngineSettings:
        """Project settings subset consumed by self-healing-scraper."""
        return EngineSettings(
            llm_api_key=self.llm_api_key,
            llm_model=self.llm_model,
            llm_base_url=self.llm_base_url,
            max_repair_attempts=self.max_repair_attempts,
            crawl_timeout_ms=self.crawl_timeout_ms,
            page_sample_chars=self.page_sample_chars,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
