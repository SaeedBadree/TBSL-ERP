from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import MovementType, StockMovement
from app.services.reorder_service import handle_stock_movement


async def post_stock_movement(
    session: AsyncSession,
    *,
    item_id,
    location_id,
    movement_type: MovementType,
    qty_delta,
    unit_cost=None,
    ref_type: str,
    ref_id,
    details: Optional[dict[str, Any]] = None,
) -> StockMovement:
    """Idempotently post a stock movement for a given reference and item."""
    result = await session.execute(
        select(StockMovement).where(
            StockMovement.ref_type == ref_type,
            StockMovement.ref_id == ref_id,
            StockMovement.movement_type == movement_type,
            StockMovement.item_id == item_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    movement = StockMovement(
        item_id=item_id,
        location_id=location_id,
        ref_type=ref_type,
        ref_id=ref_id,
        movement_type=movement_type,
        qty_delta=qty_delta,
        unit_cost=unit_cost,
        details=details or {},
    )
    session.add(movement)
    await session.commit()
    await session.refresh(movement)
    await handle_stock_movement(session, item_id=item_id, location_id=location_id)
    return movement

