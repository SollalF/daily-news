"""initial parsers and scrape_runs tables

Revision ID: 001
Revises:
Create Date: 2026-07-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "parsers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("url_pattern", sa.String(length=1024), nullable=False),
        sa.Column("page_kind", sa.String(length=32), nullable=False),
        sa.Column("definition", postgresql.JSONB(), nullable=False),
        sa.Column("validations", postgresql.JSONB(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="draft"
        ),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_parsers_url_pattern", "parsers", ["url_pattern"])

    op.create_table(
        "scrape_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("parser_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("parser_version", sa.Integer(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("article_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("articles", postgresql.JSONB(), nullable=True),
        sa.Column("validation_errors", postgresql.JSONB(), nullable=True),
        sa.Column("page_sample", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_scrape_runs_url", "scrape_runs", ["url"])
    op.create_index("ix_scrape_runs_parser_id", "scrape_runs", ["parser_id"])


def downgrade() -> None:
    op.drop_index("ix_scrape_runs_parser_id", table_name="scrape_runs")
    op.drop_index("ix_scrape_runs_url", table_name="scrape_runs")
    op.drop_table("scrape_runs")
    op.drop_index("ix_parsers_url_pattern", table_name="parsers")
    op.drop_table("parsers")
