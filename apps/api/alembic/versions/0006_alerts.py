"""Alerts model."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0006_alerts"
down_revision = "0005_reorder_webhooks"
branch_labels = None
depends_on = None


alerttype = sa.Enum(
    "LOW_STOCK",
    "NEGATIVE_STOCK",
    "DEAD_STOCK",
    "SPIKE_SALES",
    "COST_CHANGE",
    "SUPPLIER_DELAY",
    name="alerttype",
)
alertseverity = sa.Enum("INFO", "WARNING", "CRITICAL", name="alertseverity")
alertstatus = sa.Enum("OPEN", "ACK", "DONE", name="alertstatus")


def upgrade() -> None:
    alerttype.create(op.get_bind(), checkfirst=True)
    alertseverity.create(op.get_bind(), checkfirst=True)
    alertstatus.create(op.get_bind(), checkfirst=True)

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
        sa.Column("type", alerttype, nullable=False),
        sa.Column("severity", alertseverity, nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", alertstatus, nullable=False, server_default="OPEN"),
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
    alertstatus.drop(op.get_bind(), checkfirst=True)
    alertseverity.drop(op.get_bind(), checkfirst=True)
    alerttype.drop(op.get_bind(), checkfirst=True)

