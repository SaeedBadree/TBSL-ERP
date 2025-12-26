from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.db import Base
from app.models import (
    Customer,
    GoodsReceipt,
    GoodsReceiptLine,
    GoodsReceiptStatus,
    Item,
    MovementType,
    SalesInvoice,
    SalesInvoiceLine,
    StoreLocation,
    Supplier,
    StockMovement,
)
from app.services.purchase_service import post_goods_receipt
from app.services.sales_service import post_sales_invoice, post_sales_return


@pytest.fixture(scope="module")
async def async_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(async_engine):
    session_maker = async_sessionmaker(async_engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session
        await session.rollback()


async def _count_movements(session: AsyncSession) -> int:
    result = await session.execute(select(StockMovement))
    return len(result.scalars().all())


@pytest.mark.asyncio
async def test_grn_sale_return_lifecycle(session: AsyncSession):
    location = StoreLocation(code="LOC1", name="Main")
    customer = Customer(customer_code="CUST1", name="Alice")
    supplier = Supplier(supplier_code="SUP1", name="ACME")
    item = Item(item_code="ITM1", sku="SKU1", name="Widget", uom="ea")

    session.add_all([location, customer, supplier, item])
    await session.commit()

    grn = GoodsReceipt(
        grn_no="GRN-1",
        supplier_id=supplier.id,
        location_id=location.id,
        status=GoodsReceiptStatus.DRAFT,
    )
    grn_line = GoodsReceiptLine(
        item_id=item.id,
        qty=Decimal("10"),
        unit_cost=Decimal("5"),
        line_total=Decimal("50"),
    )
    grn.lines.append(grn_line)
    session.add(grn)
    await session.commit()

    grn = await post_goods_receipt(session, grn.id)
    assert grn.status == GoodsReceiptStatus.POSTED
    assert await _count_movements(session) == 1

    # Create sales invoice
    invoice = SalesInvoice(
        invoice_no="INV-1",
        customer_id=customer.id,
        location_id=location.id,
        subtotal=Decimal("16"),
        tax_total=Decimal("0"),
        discount_total=Decimal("0"),
        grand_total=Decimal("16"),
    )
    line = SalesInvoiceLine(
        item_id=item.id,
        qty=Decimal("2"),
        unit_price=Decimal("8"),
        discount=Decimal("0"),
        tax=Decimal("0"),
        line_total=Decimal("16"),
        unit_cost_snapshot=Decimal("5"),
    )
    invoice.lines.append(line)
    session.add(invoice)
    await session.commit()

    invoice = await post_sales_invoice(session, invoice.id)
    assert await _count_movements(session) == 2

    # Post return (idempotent)
    await post_sales_return(session, invoice.id)
    await post_sales_return(session, invoice.id)
    assert await _count_movements(session) == 3

    result = await session.execute(
        select(StockMovement).where(StockMovement.movement_type == MovementType.SALE_RETURN)
    )
    sale_return = result.scalar_one()
    assert sale_return.qty_delta == Decimal("2")

