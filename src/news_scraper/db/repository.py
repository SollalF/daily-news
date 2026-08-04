"""Persistence helpers for parsers and scrape runs (ParserStore for the engine)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, cast

from self_healing_scraper.models import (
    GeneratedParser,
    ParserDefinition,
    ParserStatus,
    ValidationSuite,
)
from self_healing_scraper.store import ParserRecordLike, best_parser_match
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from news_scraper.db.models import ParserRecord, ScrapeRunRecord
from news_scraper.models import NewsArticle


class ParserRepository:
    """SQLAlchemy-backed ParserStore used by scrape_news_url."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_candidates(
        self, statuses: list[str] | None = None
    ) -> list[ParserRecord]:
        stmt = select(ParserRecord)
        if statuses:
            stmt = stmt.where(ParserRecord.status.in_(statuses))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_url(self, url: str) -> ParserRecord | None:
        """Return the most specific active (or draft) parser matching the URL."""
        # Prefer active parsers; fall back to newest draft for in-progress creation.
        active = await self.list_candidates([ParserStatus.ACTIVE.value])
        match = best_parser_match(url, active)
        if match:
            return match
        drafts = await self.list_candidates([ParserStatus.DRAFT.value])
        return best_parser_match(url, drafts)

    @staticmethod
    def definition_of(record: ParserRecordLike) -> ParserDefinition:
        """Rehydrate a stored JSON definition into a domain model."""
        orm = cast(ParserRecord, record)
        return ParserDefinition.model_validate(orm.definition)

    @staticmethod
    def validations_of(record: ParserRecordLike) -> ValidationSuite:
        """Rehydrate a stored JSON validation suite into a domain model."""
        from self_healing_scraper.runtime.validators import migrate_legacy_checks

        orm = cast(ParserRecord, record)
        return migrate_legacy_checks(ValidationSuite.model_validate(orm.validations))

    async def create_from_generated(
        self,
        generated: GeneratedParser,
        *,
        status: ParserStatus = ParserStatus.DRAFT,
    ) -> ParserRecord:
        record = ParserRecord(
            name=generated.name,
            url_pattern=generated.url_pattern,
            page_kind=generated.page_kind,
            definition=generated.definition.model_dump(),
            validations=generated.validations.model_dump(),
            version=1,
            status=status.value,
        )
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def update_parser(
        self,
        record: ParserRecordLike,
        *,
        name: str | None = None,
        url_pattern: str | None = None,
        page_kind: str | None = None,
        definition: ParserDefinition | None = None,
        validations: ValidationSuite | None = None,
        status: ParserStatus | None = None,
        bump_version: bool = False,
        last_error: str | None = None,
        mark_success: bool = False,
    ) -> ParserRecord:
        orm = cast(ParserRecord, record)
        if name is not None:
            orm.name = name
        if url_pattern is not None:
            orm.url_pattern = url_pattern
        if page_kind is not None:
            orm.page_kind = page_kind
        if definition is not None:
            orm.definition = definition.model_dump()
        if validations is not None:
            orm.validations = validations.model_dump()
        if status is not None:
            orm.status = status.value
        if bump_version:
            orm.version += 1
        if last_error is not None:
            orm.last_error = last_error
        if mark_success:
            orm.last_success_at = datetime.now(UTC)
            orm.last_error = None
            orm.status = ParserStatus.ACTIVE.value
        orm.updated_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(orm)
        return orm

    async def save_run(
        self,
        *,
        url: str,
        parser_id: uuid.UUID | None,
        parser_version: int | None,
        success: bool,
        items: list[dict[str, Any]] | None = None,
        validation_errors: list[dict[str, Any]] | None = None,
        page_sample: str | None = None,
        error_message: str | None = None,
    ) -> ScrapeRunRecord:
        articles = cast(list[NewsArticle] | None, list(items) if items else None)
        run = ScrapeRunRecord(
            url=url,
            parser_id=parser_id,
            parser_version=parser_version,
            success=success,
            article_count=len(articles or []),
            articles=list(articles) if articles else None,
            validation_errors=validation_errors,
            page_sample=page_sample,
            error_message=error_message,
        )
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def get_by_id(self, parser_id: uuid.UUID) -> ParserRecord | None:
        return await self.session.get(ParserRecord, parser_id)
