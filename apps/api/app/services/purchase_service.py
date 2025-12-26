from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import (
    GoodsReceipt,
    GoodsReceiptStatus,
    MovementType,
    PurchaseOrder,
    PurchaseOrderStatus,
)
from app.services.stock_service import post_stock_movement


async def _get_grn_with_lines(session: AsyncSession, grn_id) -> GoodsReceipt | None:
    result = await session.execute(
        select(GoodsReceipt)
        .options(selectinload(GoodsReceipt.lines))
        .where(GoodsReceipt.id == grn_id)
    )
    return result.scalar_one_or_none()


async def post_goods_receipt(session: AsyncSession, grn_id) -> GoodsReceipt:
    """Post a goods receipt to the stock ledger."""
    grn = await _get_grn_with_lines(session, grn_id)
    if not grn:
        raise ValueError("Goods receipt not found")

    if grn.status == GoodsReceiptStatus.POSTED:
        return grn

    for line in grn.lines:
        await post_stock_movement(
            session,
            item_id=line.item_id,
            location_id=grn.location_id,
            movement_type=MovementType.PURCHASE_RECEIPT,
            qty_delta=line.qty,
            unit_cost=line.unit_cost,
            ref_type="goods_receipt",
            ref_id=grn.id,
        )

    grn.status = GoodsReceiptStatus.POSTED
    session.add(grn)
    await session.commit()
    await session.refresh(grn)
    return grn


async def post_purchase_return(session: AsyncSession, grn_id) -> GoodsReceipt:
    """Post a purchase return (reverse stock) for a goods receipt."""
    grn = await _get_grn_with_lines(session, grn_id)
    if not grn:
        raise ValueError("Goods receipt not found")

    for line in grn.lines:
        await post_stock_movement(
            session,
            item_id=line.item_id,
            location_id=grn.location_id,
            movement_type=MovementType.PURCHASE_RETURN,
            qty_delta=-line.qty,
            unit_cost=line.unit_cost,
            ref_type="purchase_return",
            ref_id=grn.id,
        )

    return grn


async def close_purchase_order(session: AsyncSession, po_id) -> PurchaseOrder:
    result = await session.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise ValueError("Purchase order not found")
    if po.status == PurchaseOrderStatus.CLOSED:
        return po
    po.status = PurchaseOrderStatus.CLOSED
    session.add(po)
    await session.commit()
    await session.refresh(po)
    return po

