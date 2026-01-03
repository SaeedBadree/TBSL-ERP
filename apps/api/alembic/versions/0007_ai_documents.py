"""AI documents for invoice extraction."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0007_ai_documents"
down_revision = "0006_alerts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE aidocumenttype AS ENUM ('INVOICE')")
    op.execute("CREATE TYPE aidocumentstatus AS ENUM ('PENDING', 'PROCESSED', 'FAILED')")

    op.create_table(
        "ai_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("type", postgresql.ENUM("INVOICE", name="aidocumenttype", create_type=False), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=True),
        sa.Column("mime", sa.String(length=128), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("extracted_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", postgresql.ENUM("PENDING", "PROCESSED", "FAILED", name="aidocumentstatus", create_type=False), nullable=False, server_default="PENDING"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("ai_documents")
    op.execute("DROP TYPE IF EXISTS aidocumentstatus")
    op.execute("DROP TYPE IF EXISTS aidocumenttype")

