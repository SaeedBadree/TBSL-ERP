"""Alerts model."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0006_alerts"
down_revision = "0005_reorder_webhooks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE alerttype AS ENUM ('LOW_STOCK', 'NEGATIVE_STOCK', 'DEAD_STOCK', 'SPIKE_SALES', 'COST_CHANGE', 'SUPPLIER_DELAY')")
    op.execute("CREATE TYPE alertseverity AS ENUM ('INFO', 'WARNING', 'CRITICAL')")
    op.execute("CREATE TYPE alertstatus AS ENUM ('OPEN', 'ACK', 'DONE')")

    op.create_table(
        "alerts",
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
        sa.Column("type", postgresql.ENUM("LOW_STOCK", "NEGATIVE_STOCK", "DEAD_STOCK", "SPIKE_SALES", "COST_CHANGE", "SUPPLIER_DELAY", name="alerttype", create_type=False), nullable=False),
        sa.Column("severity", postgresql.ENUM("INFO", "WARNING", "CRITICAL", name="alertseverity", create_type=False), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", postgresql.ENUM("OPEN", "ACK", "DONE", name="alertstatus", create_type=False), nullable=False, server_default="OPEN"),
        sa.Column("ack_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ack_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alert_status", "alerts", ["status"])
    op.create_index("ix_alert_type", "alerts", ["type"])
    op.create_index("ix_alert_location", "alerts", ["location_id"])


def downgrade() -> None:
    op.drop_index("ix_alert_location", table_name="alerts")
    op.drop_index("ix_alert_type", table_name="alerts")
    op.drop_index("ix_alert_status", table_name="alerts")
    op.drop_table("alerts")
    op.execute("DROP TYPE IF EXISTS alertstatus")
    op.execute("DROP TYPE IF EXISTS alertseverity")
    op.execute("DROP TYPE IF EXISTS alerttype")

