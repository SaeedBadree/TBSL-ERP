"""Reorder rules and webhook delivery."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0005_reorder_webhooks"
down_revision = "0004_auth_api_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE webhookdeliverystatus AS ENUM ('PENDING', 'SUCCESS', 'FAILED')")

    op.create_table(
        "reorder_rules",
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
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("min_level", sa.Numeric(14, 3), nullable=False),
        sa.Column("max_level", sa.Numeric(14, 3), nullable=False),
        sa.Column("reorder_qty", sa.Numeric(14, 3), nullable=False),
        sa.Column("preferred_supplier_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("lead_time_days", sa.Integer(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["store_locations.id"]),
        sa.ForeignKeyConstraint(["preferred_supplier_id"], ["suppliers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("item_id", "location_id", name="uq_reorder_rule_item_location"),
    )
    op.create_index("ix_reorder_rule_item_location", "reorder_rules", ["item_id", "location_id"])

    op.create_table(
        "webhook_endpoints",
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
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("secret", sa.String(length=255), nullable=False),
        sa.Column("events", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_webhook_endpoint_name"),
    )

    op.create_table(
        "webhook_deliveries",
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
        sa.Column("endpoint_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", postgresql.ENUM("PENDING", "SUCCESS", "FAILED", name="webhookdeliverystatus", create_type=False), nullable=False, server_default="PENDING"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["endpoint_id"], ["webhook_endpoints.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_webhook_delivery_status", "webhook_deliveries", ["status"])
    op.create_index("ix_webhook_delivery_next_retry", "webhook_deliveries", ["next_retry_at"])


def downgrade() -> None:
    op.drop_index("ix_webhook_delivery_next_retry", table_name="webhook_deliveries")
    op.drop_index("ix_webhook_delivery_status", table_name="webhook_deliveries")
    op.drop_table("webhook_deliveries")
    op.drop_table("webhook_endpoints")
    op.drop_index("ix_reorder_rule_item_location", table_name="reorder_rules")
    op.drop_table("reorder_rules")
    op.execute("DROP TYPE IF EXISTS webhookdeliverystatus")

