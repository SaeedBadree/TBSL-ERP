"""Transactional documents and stock movements."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0003_transactions"
down_revision = "0002_core_schema"
branch_labels = None
depends_on = None


salesinvoicestatus = sa.Enum("draft", "finalized", "posted", name="salesinvoicestatus")
goodsreceiptstatus = sa.Enum("draft", "posted", name="goodsreceiptstatus")
purchaseorderstatus = sa.Enum("open", "closed", "cancelled", name="purchaseorderstatus")
paymentmethod = sa.Enum("cash", "card", "transfer", name="paymentmethod")
movementtype = sa.Enum("SALE", "SALE_RETURN", "PURCHASE_RECEIPT", "PURCHASE_RETURN", name="movementtype")


def upgrade() -> None:
    salesinvoicestatus.create(op.get_bind(), checkfirst=True)
    goodsreceiptstatus.create(op.get_bind(), checkfirst=True)
    purchaseorderstatus.create(op.get_bind(), checkfirst=True)
    paymentmethod.create(op.get_bind(), checkfirst=True)
    movementtype.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "sales_invoices",
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
        sa.Column("invoice_no", sa.String(length=64), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", salesinvoicestatus, nullable=False, server_default="draft"),
        sa.Column("subtotal", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("tax_total", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("discount_total", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("grand_total", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["store_locations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invoice_no", name="uq_sales_invoice_no"),
    )
    op.create_index("ix_sales_invoice_customer", "sales_invoices", ["customer_id"])

    op.create_table(
        "purchase_orders",
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
        sa.Column("po_no", sa.String(length=64), nullable=False),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", purchaseorderstatus, nullable=False, server_default="open"),
        sa.ForeignKeyConstraint(["location_id"], ["store_locations.id"]),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("po_no", name="uq_purchase_order_no"),
    )
    op.create_index("ix_purchase_order_supplier", "purchase_orders", ["supplier_id"])

    op.create_table(
        "goods_receipts",
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
        sa.Column("grn_no", sa.String(length=64), nullable=False),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", goodsreceiptstatus, nullable=False, server_default="draft"),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["location_id"], ["store_locations.id"]),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("grn_no", name="uq_goods_receipt_no"),
    )
    op.create_index("ix_goods_receipt_supplier", "goods_receipts", ["supplier_id"])

    op.create_table(
        "sales_invoice_lines",
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
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("qty", sa.Numeric(14, 3), nullable=False),
        sa.Column("unit_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("discount", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("tax", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("line_total", sa.Numeric(14, 2), nullable=False),
        sa.Column("unit_cost_snapshot", sa.Numeric(14, 2), nullable=True),
        sa.ForeignKeyConstraint(["invoice_id"], ["sales_invoices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sales_invoice_lines_invoice", "sales_invoice_lines", ["invoice_id"])

    op.create_table(
        "goods_receipt_lines",
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
        sa.Column("grn_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("qty", sa.Numeric(14, 3), nullable=False),
        sa.Column("unit_cost", sa.Numeric(14, 2), nullable=False),
        sa.Column("line_total", sa.Numeric(14, 2), nullable=False),
        sa.ForeignKeyConstraint(["grn_id"], ["goods_receipts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_grn_lines_grn", "goods_receipt_lines", ["grn_id"])

    op.create_table(
        "payments",
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
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("method", paymentmethod, nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("reference", sa.String(length=128), nullable=True),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["invoice_id"], ["sales_invoices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payments_invoice", "payments", ["invoice_id"])

    op.create_table(
        "stock_movements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ref_type", sa.String(length=64), nullable=False),
        sa.Column("ref_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("movement_type", movementtype, nullable=False),
        sa.Column("qty_delta", sa.Numeric(14, 3), nullable=False),
        sa.Column("unit_cost", sa.Numeric(14, 2), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["store_locations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ref_type", "ref_id", "movement_type", "item_id", name="uq_stock_movement_idempotent"),
    )
    op.create_index("ix_stock_movement_item", "stock_movements", ["item_id"])
    op.create_index("ix_stock_movement_location", "stock_movements", ["location_id"])


def downgrade() -> None:
    op.drop_index("ix_stock_movement_location", table_name="stock_movements")
    op.drop_index("ix_stock_movement_item", table_name="stock_movements")
    op.drop_table("stock_movements")

    op.drop_index("ix_payments_invoice", table_name="payments")
    op.drop_table("payments")

    op.drop_index("ix_grn_lines_grn", table_name="goods_receipt_lines")
    op.drop_table("goods_receipt_lines")

    op.drop_index("ix_sales_invoice_lines_invoice", table_name="sales_invoice_lines")
    op.drop_table("sales_invoice_lines")

    op.drop_index("ix_goods_receipt_supplier", table_name="goods_receipts")
    op.drop_table("goods_receipts")

    op.drop_index("ix_purchase_order_supplier", table_name="purchase_orders")
    op.drop_table("purchase_orders")

    op.drop_index("ix_sales_invoice_customer", table_name="sales_invoices")
    op.drop_table("sales_invoices")

    movementtype.drop(op.get_bind(), checkfirst=True)
    paymentmethod.drop(op.get_bind(), checkfirst=True)
    purchaseorderstatus.drop(op.get_bind(), checkfirst=True)
    goodsreceiptstatus.drop(op.get_bind(), checkfirst=True)
    salesinvoicestatus.drop(op.get_bind(), checkfirst=True)

