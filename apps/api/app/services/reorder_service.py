from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import ReorderRule, StockMovement
from app.services.webhook_service import enqueue_event
from app.services.alert_service import emit_alert
from app.models.entities import AlertSeverity, AlertType, AlertStatus

EVENT_LOW_STOCK = "inventory.low_stock"
EVENT_NEGATIVE_STOCK = "inventory.negative_stock"
EVENT_PURCHASE_SUGGESTED = "purchase.suggested"


async def get_available_qty(session: AsyncSession, item_id, location_id) -> Decimal:
    result = await session.execute(
        select(func.coalesce(func.sum(StockMovement.qty_delta), 0)).where(
            StockMovement.item_id == item_id,
            StockMovement.location_id == location_id,
        )
    )
    return Decimal(result.scalar_one() or 0)


async def handle_stock_movement(session: AsyncSession, item_id, location_id) -> None:
    available = await get_available_qty(session, item_id, location_id)
    rules = (
        await session.execute(
            select(ReorderRule).where(
                ReorderRule.item_id == item_id,
                ReorderRule.location_id == location_id,
                ReorderRule.active.is_(True),
            )
        )
    ).scalars()

    for rule in rules:
        if available <= rule.min_level:
            await enqueue_event(
                session,
                EVENT_LOW_STOCK,
                {
                    "item_id": str(item_id),
                    "location_id": str(location_id),
                    "available": str(available),
                    "min_level": str(rule.min_level),
                },
            )
            await emit_alert(
                session,
                type=AlertType.LOW_STOCK,
                severity=AlertSeverity.WARNING,
                message="Low stock detected",
                context={
                    "available": str(available),
                    "min_level": str(rule.min_level),
                    "item_id": str(item_id),
                    "location_id": str(location_id),
                },
                item_id=item_id,
                location_id=location_id,
            )
        if available < 0:
            await enqueue_event(
                session,
                EVENT_NEGATIVE_STOCK,
                {
                    "item_id": str(item_id),
                    "location_id": str(location_id),
                    "available": str(available),
                },
            )
            await emit_alert(
                session,
                type=AlertType.NEGATIVE_STOCK,
                severity=AlertSeverity.CRITICAL,
                message="Negative stock detected",
                context={
                    "available": str(available),
                    "item_id": str(item_id),
                    "location_id": str(location_id),
                },
                item_id=item_id,
                location_id=location_id,
            )

        suggested = max(Decimal(0), Decimal(rule.max_level) - available)
        if suggested > 0:
            qty = suggested if rule.reorder_qty is None else max(suggested, rule.reorder_qty)
            await enqueue_event(
                session,
                EVENT_PURCHASE_SUGGESTED,
                {
                    "item_id": str(item_id),
                    "location_id": str(location_id),
                    "suggested_qty": str(qty),
                    "preferred_supplier_id": str(rule.preferred_supplier_id)
                    if rule.preferred_supplier_id
                    else None,
                },
            )

