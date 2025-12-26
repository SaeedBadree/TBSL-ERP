"""AI documents for invoice extraction."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0007_ai_documents"
down_revision = "0006_alerts"
branch_labels = None
depends_on = None


aidocumenttype = sa.Enum("INVOICE", name="aidocumenttype")
aidocumentstatus = sa.Enum("PENDING", "PROCESSED", "FAILED", name="aidocumentstatus")


def upgrade() -> None:
    aidocumenttype.create(op.get_bind(), checkfirst=True)
    aidocumentstatus.create(op.get_bind(), checkfirst=True)

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
        sa.Column("type", aidocumenttype, nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=True),
        sa.Column("mime", sa.String(length=128), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("extracted_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", aidocumentstatus, nullable=False, server_default="PENDING"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("ai_documents")
    aidocumentstatus.drop(op.get_bind(), checkfirst=True)
    aidocumenttype.drop(op.get_bind(), checkfirst=True)

