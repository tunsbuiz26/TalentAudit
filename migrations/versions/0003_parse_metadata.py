"""Add parser metadata, retaining existing documents as PENDING.

Revision ID: 0003_parse_metadata
Revises: 0002_documents
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_parse_metadata"
down_revision: str | None = "0002_documents"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column(
            "parser_status", sa.String(20), nullable=False, server_default="PENDING"
        ),
    )
    op.add_column("documents", sa.Column("document_language", sa.String(5)))
    op.add_column("documents", sa.Column("page_count", sa.Integer()))
    op.add_column("documents", sa.Column("parse_error_code", sa.String(50)))


def downgrade() -> None:
    for name in (
        "parse_error_code",
        "page_count",
        "document_language",
        "parser_status",
    ):
        op.drop_column("documents", name)
