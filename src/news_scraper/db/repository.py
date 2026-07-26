"""Persistence helpers for parsers and scrape runs."""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from news_scraper.db.models import ParserRecord, ScrapeRunRecord
from news_scraper.models import (
    GeneratedParser,
    NewsArticle,
    ParserDefinition,
    ParserStatus,
    ValidationSuite,
)


class ParserRepository:
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
        match = self._best_match(url, active)
        if match:
            return match
        drafts = await self.list_candidates([ParserStatus.DRAFT.value])
        return self._best_match(url, drafts)

    @staticmethod
    def definition_of(record: ParserRecord) -> ParserDefinition:
        """Rehydrate a stored JSON definition into a domain model."""
        return ParserDefinition.model_validate(record.definition)

    @staticmethod
    def validations_of(record: ParserRecord) -> ValidationSuite:
        """Rehydrate a stored JSON validation suite into a domain model."""
        return ValidationSuite.model_validate(record.validations)

    @staticmethod
    def _best_match(url: str, parsers: list[ParserRecord]) -> ParserRecord | None:
        matches: list[tuple[int, ParserRecord]] = []
        for parser in parsers:
            try:
                compiled = re.compile(parser.url_pattern)
            except re.error:
                continue
            if compiled.search(url):
                matches.append((len(parser.url_pattern), parser))
        if not matches:
            return None
        matches.sort(key=lambda item: (-item[0], -item[1].version))
        return matches[0][1]

    async def create_from_generated(
        self, generated: GeneratedParser, status: ParserStatus = ParserStatus.DRAFT
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
        record: ParserRecord,
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
        if name is not None:
            record.name = name
        if url_pattern is not None:
            record.url_pattern = url_pattern
        if page_kind is not None:
            record.page_kind = page_kind
        if definition is not None:
            record.definition = definition.model_dump()
        if validations is not None:
            record.validations = validations.model_dump()
        if status is not None:
            record.status = status.value
        if bump_version:
            record.version += 1
        if last_error is not None:
            record.last_error = last_error
        if mark_success:
            record.last_success_at = datetime.now(UTC)
            record.last_error = None
            record.status = ParserStatus.ACTIVE.value
        record.updated_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def save_run(
        self,
        *,
        url: str,
        parser_id: uuid.UUID | None,
        parser_version: int | None,
        success: bool,
        articles: list[NewsArticle] | None = None,
        validation_errors: list[dict[str, Any]] | None = None,
        page_sample: str | None = None,
        error_message: str | None = None,
    ) -> ScrapeRunRecord:
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
