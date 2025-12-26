from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import MovementType, SalesInvoice, SalesInvoiceStatus
from app.services.stock_service import post_stock_movement


async def _get_invoice_with_lines(session: AsyncSession, invoice_id) -> SalesInvoice | None:
    result = await session.execute(
        select(SalesInvoice)
        .options(selectinload(SalesInvoice.lines))
        .where(SalesInvoice.id == invoice_id)
    )
    return result.scalar_one_or_none()


async def post_sales_invoice(session: AsyncSession, invoice_id) -> SalesInvoice:
    """Finalize/post an invoice and record stock movements."""
    invoice = await _get_invoice_with_lines(session, invoice_id)
    if not invoice:
        raise ValueError("Invoice not found")

    if invoice.status == SalesInvoiceStatus.POSTED:
        return invoice

    for line in invoice.lines:
        await post_stock_movement(
            session,
            item_id=line.item_id,
            location_id=invoice.location_id,
            movement_type=MovementType.SALE,
            qty_delta=-line.qty,
            unit_cost=line.unit_cost_snapshot,
            ref_type="sales_invoice",
            ref_id=invoice.id,
        )

    invoice.status = SalesInvoiceStatus.POSTED
    session.add(invoice)
    await session.commit()
    await session.refresh(invoice)
    return invoice


async def post_sales_return(session: AsyncSession, invoice_id) -> SalesInvoice:
    """Post a sales return (reverse stock) for an invoice."""
    invoice = await _get_invoice_with_lines(session, invoice_id)
    if not invoice:
        raise ValueError("Invoice not found")

    for line in invoice.lines:
        await post_stock_movement(
            session,
            item_id=line.item_id,
            location_id=invoice.location_id,
            movement_type=MovementType.SALE_RETURN,
            qty_delta=line.qty,
            unit_cost=line.unit_cost_snapshot,
            ref_type="sales_return",
            ref_id=invoice.id,
        )

    return invoice

