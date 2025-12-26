from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SalesInvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    FINALIZED = "finalized"
    POSTED = "posted"


class GoodsReceiptStatus(str, enum.Enum):
    DRAFT = "draft"
    POSTED = "posted"


class PurchaseOrderStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CARD = "card"
    TRANSFER = "transfer"


class MovementType(str, enum.Enum):
    SALE = "SALE"
    SALE_RETURN = "SALE_RETURN"
    PURCHASE_RECEIPT = "PURCHASE_RECEIPT"
    PURCHASE_RETURN = "PURCHASE_RETURN"


class StaffRole(str, enum.Enum):
    CASHIER = "CASHIER"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"
    AUDITOR = "AUDITOR"


class WebhookDeliveryStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class AlertType(str, enum.Enum):
    LOW_STOCK = "LOW_STOCK"
    NEGATIVE_STOCK = "NEGATIVE_STOCK"
    DEAD_STOCK = "DEAD_STOCK"
    SPIKE_SALES = "SPIKE_SALES"
    COST_CHANGE = "COST_CHANGE"
    SUPPLIER_DELAY = "SUPPLIER_DELAY"


class AlertSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertStatus(str, enum.Enum):
    OPEN = "OPEN"
    ACK = "ACK"
    DONE = "DONE"


class AiDocumentType(str, enum.Enum):
    INVOICE = "INVOICE"


class AiDocumentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class Tenant(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)


class StoreLocation(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "store_locations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_store_location_code_per_tenant"),
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    tenant: Mapped[Optional[Tenant]] = relationship("Tenant")


class ItemCategory(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "item_categories"
    __table_args__ = (
        UniqueConstraint("tenant_id", "category1", "category2", name="uq_item_category_levels"),
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("item_categories.id"), nullable=True
    )
    category1: Mapped[str] = mapped_column(String(100), nullable=False)
    category2: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    parent: Mapped[Optional["ItemCategory"]] = relationship(
        "ItemCategory", remote_side="ItemCategory.id", backref="children"
    )
    tenant: Mapped[Optional[Tenant]] = relationship("Tenant")


class Item(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "items"
    __table_args__ = (
        UniqueConstraint("item_code", name="uq_items_item_code"),
        UniqueConstraint("tenant_id", "sku", name="uq_items_sku_per_tenant"),
        Index("ix_items_name", "name"),
        Index("ix_items_barcode", "barcode"),
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True
    )
    item_code: Mapped[str] = mapped_column(String(64), nullable=False)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    barcode: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    uom: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("item_categories.id"), nullable=True
    )
    brand: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    tenant: Mapped[Optional[Tenant]] = relationship("Tenant")
    category: Mapped[Optional[ItemCategory]] = relationship("ItemCategory")
    source_fields: Mapped[Optional["ItemSourceFields"]] = relationship(
        "ItemSourceFields", back_populates="item", uselist=False, cascade="all, delete-orphan"
    )
    sales_lines: Mapped[list["SalesInvoiceLine"]] = relationship("SalesInvoiceLine", back_populates="item")
    grn_lines: Mapped[list["GoodsReceiptLine"]] = relationship("GoodsReceiptLine", back_populates="item")


class Customer(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("customer_code", name="uq_customers_code"),
        Index("ix_customers_name", "name"),
        Index("ix_customers_phone", "phone"),
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True
    )
    customer_code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    credit_limit: Mapped[Optional[Numeric]] = mapped_column(Numeric(14, 2), nullable=True)
    credit_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    tenant: Mapped[Optional[Tenant]] = relationship("Tenant")
    source_fields: Mapped[Optional["CustomerSourceFields"]] = relationship(
        "CustomerSourceFields", back_populates="customer", uselist=False, cascade="all, delete-orphan"
    )
    invoices: Mapped[list["SalesInvoice"]] = relationship("SalesInvoice", back_populates="customer")


class Supplier(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "suppliers"
    __table_args__ = (
        UniqueConstraint("supplier_code", name="uq_suppliers_code"),
        Index("ix_suppliers_name", "name"),
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True
    )
    supplier_code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    payment_terms: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)

    tenant: Mapped[Optional[Tenant]] = relationship("Tenant")
    source_fields: Mapped[Optional["SupplierSourceFields"]] = relationship(
        "SupplierSourceFields", back_populates="supplier", uselist=False, cascade="all, delete-orphan"
    )
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship("PurchaseOrder", back_populates="supplier")
    goods_receipts: Mapped[list["GoodsReceipt"]] = relationship("GoodsReceipt", back_populates="supplier")


class PriceBook(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "price_books"

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    tenant: Mapped[Optional[Tenant]] = relationship("Tenant")


class TaxProfile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "tax_profiles"

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    rate: Mapped[Numeric] = mapped_column(Numeric(6, 3), nullable=False, default=0)
    description: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)

    tenant: Mapped[Optional[Tenant]] = relationship("Tenant")


class ItemSourceFields(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "item_source_fields"

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    source: Mapped[dict] = mapped_column(JSONB, nullable=False)
    source_file: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    item: Mapped[Item] = relationship("Item", back_populates="source_fields")


class CustomerSourceFields(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "customer_source_fields"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    source: Mapped[dict] = mapped_column(JSONB, nullable=False)
    source_file: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    customer: Mapped[Customer] = relationship("Customer", back_populates="source_fields")


class SupplierSourceFields(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "supplier_source_fields"

    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    source: Mapped[dict] = mapped_column(JSONB, nullable=False)
    source_file: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    supplier: Mapped[Supplier] = relationship("Supplier", back_populates="source_fields")


class SalesInvoice(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "sales_invoices"
    __table_args__ = (
        UniqueConstraint("invoice_no", name="uq_sales_invoice_no"),
        Index("ix_sales_invoice_customer", "customer_id"),
    )

    invoice_no: Mapped[str] = mapped_column(String(64), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("store_locations.id"), nullable=False
    )
    status: Mapped[SalesInvoiceStatus] = mapped_column(
        SAEnum(SalesInvoiceStatus), default=SalesInvoiceStatus.DRAFT, nullable=False
    )
    subtotal: Mapped[Numeric] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    tax_total: Mapped[Numeric] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    discount_total: Mapped[Numeric] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    grand_total: Mapped[Numeric] = mapped_column(Numeric(14, 2), default=0, nullable=False)

    customer: Mapped[Customer] = relationship("Customer", back_populates="invoices")
    location: Mapped[StoreLocation] = relationship("StoreLocation")
    lines: Mapped[list["SalesInvoiceLine"]] = relationship(
        "SalesInvoiceLine", back_populates="invoice", cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship(
        "Payment", back_populates="invoice", cascade="all, delete-orphan"
    )


class SalesInvoiceLine(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "sales_invoice_lines"
    __table_args__ = (Index("ix_sales_invoice_lines_invoice", "invoice_id"),)

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sales_invoices.id", ondelete="CASCADE"), nullable=False
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("items.id"), nullable=False
    )
    qty: Mapped[Numeric] = mapped_column(Numeric(14, 3), nullable=False)
    unit_price: Mapped[Numeric] = mapped_column(Numeric(14, 2), nullable=False)
    discount: Mapped[Numeric] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    tax: Mapped[Numeric] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    line_total: Mapped[Numeric] = mapped_column(Numeric(14, 2), nullable=False)
    unit_cost_snapshot: Mapped[Numeric] = mapped_column(Numeric(14, 2), nullable=True)

    invoice: Mapped[SalesInvoice] = relationship("SalesInvoice", back_populates="lines")
    item: Mapped[Item] = relationship("Item", back_populates="sales_lines")


class Payment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "payments"
    __table_args__ = (Index("ix_payments_invoice", "invoice_id"),)

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sales_invoices.id", ondelete="CASCADE"), nullable=False
    )
    method: Mapped[PaymentMethod] = mapped_column(SAEnum(PaymentMethod), nullable=False)
    amount: Mapped[Numeric] = mapped_column(Numeric(14, 2), nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    invoice: Mapped[SalesInvoice] = relationship("SalesInvoice", back_populates="payments")


class PurchaseOrder(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (
        UniqueConstraint("po_no", name="uq_purchase_order_no"),
        Index("ix_purchase_order_supplier", "supplier_id"),
    )

    po_no: Mapped[str] = mapped_column(String(64), nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("store_locations.id"), nullable=False
    )
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        SAEnum(PurchaseOrderStatus), default=PurchaseOrderStatus.OPEN, nullable=False
    )

    supplier: Mapped[Supplier] = relationship("Supplier", back_populates="purchase_orders")
    location: Mapped[StoreLocation] = relationship("StoreLocation")


class GoodsReceipt(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "goods_receipts"
    __table_args__ = (
        UniqueConstraint("grn_no", name="uq_goods_receipt_no"),
        Index("ix_goods_receipt_supplier", "supplier_id"),
    )

    grn_no: Mapped[str] = mapped_column(String(64), nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("store_locations.id"), nullable=False
    )
    status: Mapped[GoodsReceiptStatus] = mapped_column(
        SAEnum(GoodsReceiptStatus), default=GoodsReceiptStatus.DRAFT, nullable=False
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    supplier: Mapped[Supplier] = relationship("Supplier", back_populates="goods_receipts")
    location: Mapped[StoreLocation] = relationship("StoreLocation")
    lines: Mapped[list["GoodsReceiptLine"]] = relationship(
        "GoodsReceiptLine", back_populates="goods_receipt", cascade="all, delete-orphan"
    )


class GoodsReceiptLine(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "goods_receipt_lines"
    __table_args__ = (Index("ix_grn_lines_grn", "grn_id"),)

    grn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("goods_receipts.id", ondelete="CASCADE"), nullable=False
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("items.id"), nullable=False
    )
    qty: Mapped[Numeric] = mapped_column(Numeric(14, 3), nullable=False)
    unit_cost: Mapped[Numeric] = mapped_column(Numeric(14, 2), nullable=False)
    line_total: Mapped[Numeric] = mapped_column(Numeric(14, 2), nullable=False)

    goods_receipt: Mapped[GoodsReceipt] = relationship("GoodsReceipt", back_populates="lines")
    item: Mapped[Item] = relationship("Item", back_populates="grn_lines")


class StockMovement(UUIDMixin, Base):
    __tablename__ = "stock_movements"
    __table_args__ = (
        UniqueConstraint(
            "ref_type", "ref_id", "movement_type", "item_id", name="uq_stock_movement_idempotent"
        ),
        Index("ix_stock_movement_item", "item_id"),
        Index("ix_stock_movement_location", "location_id"),
    )

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("items.id"), nullable=False
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("store_locations.id"), nullable=False
    )
    ref_type: Mapped[str] = mapped_column(String(64), nullable=False)
    ref_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    movement_type: Mapped[MovementType] = mapped_column(SAEnum(MovementType), nullable=False)
    qty_delta: Mapped[Numeric] = mapped_column(Numeric(14, 3), nullable=False)
    unit_cost: Mapped[Optional[Numeric]] = mapped_column(Numeric(14, 2), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    item: Mapped[Item] = relationship("Item")
    location: Mapped[StoreLocation] = relationship("StoreLocation")


class StaffUser(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "staff_users"
    __table_args__ = (UniqueConstraint("email", name="uq_staff_email"),)

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[StaffRole] = mapped_column(SAEnum(StaffRole), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ApiKey(UUIDMixin, Base):
    __tablename__ = "api_keys"
    __table_args__ = (UniqueConstraint("name", name="uq_api_key_name"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    scopes: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReorderRule(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "reorder_rules"
    __table_args__ = (
        UniqueConstraint("item_id", "location_id", name="uq_reorder_rule_item_location"),
        Index("ix_reorder_rule_item_location", "item_id", "location_id"),
    )

    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("items.id"), nullable=False)
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("store_locations.id"), nullable=False
    )
    min_level: Mapped[Numeric] = mapped_column(Numeric(14, 3), nullable=False)
    max_level: Mapped[Numeric] = mapped_column(Numeric(14, 3), nullable=False)
    reorder_qty: Mapped[Numeric] = mapped_column(Numeric(14, 3), nullable=False)
    preferred_supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True
    )
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    item: Mapped[Item] = relationship("Item")
    location: Mapped[StoreLocation] = relationship("StoreLocation")
    preferred_supplier: Mapped[Supplier | None] = relationship("Supplier")


class WebhookEndpoint(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "webhook_endpoints"
    __table_args__ = (UniqueConstraint("name", name="uq_webhook_endpoint_name"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    secret: Mapped[str] = mapped_column(String(255), nullable=False)
    events: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class WebhookDelivery(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "webhook_deliveries"
    __table_args__ = (
        Index("ix_webhook_delivery_status", "status"),
        Index("ix_webhook_delivery_next_retry", "next_retry_at"),
    )

    endpoint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[WebhookDeliveryStatus] = mapped_column(
        SAEnum(WebhookDeliveryStatus), default=WebhookDeliveryStatus.PENDING, nullable=False
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text(), nullable=True)

    endpoint: Mapped[WebhookEndpoint] = relationship("WebhookEndpoint")


class Alert(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "alerts"
    __table_args__ = (
        Index("ix_alert_status", "status"),
        Index("ix_alert_type", "type"),
        Index("ix_alert_location", "location_id"),
    )

    type: Mapped[AlertType] = mapped_column(SAEnum(AlertType), nullable=False)
    severity: Mapped[AlertSeverity] = mapped_column(SAEnum(AlertSeverity), nullable=False)
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("store_locations.id"), nullable=True
    )
    item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("items.id"), nullable=True
    )
    message: Mapped[str] = mapped_column(Text(), nullable=False)
    context: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[AlertStatus] = mapped_column(
        SAEnum(AlertStatus), default=AlertStatus.OPEN, nullable=False
    )
    ack_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    ack_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AiDocument(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "ai_documents"

    type: Mapped[AiDocumentType] = mapped_column(SAEnum(AiDocumentType), nullable=False)
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mime: Mapped[str | None] = mapped_column(String(128), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text(), nullable=False)
    extracted_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[AiDocumentStatus] = mapped_column(
        SAEnum(AiDocumentStatus), default=AiDocumentStatus.PENDING, nullable=False
    )


