from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Alert, AlertSeverity, AlertStatus, AlertType


def now() -> datetime:
    return datetime.now(timezone.utc)


async def emit_alert(
    session: AsyncSession,
    *,
    type: AlertType,
    severity: AlertSeverity,
    message: str,
    context: dict,
    location_id=None,
    item_id=None,
) -> Alert:
    alert = Alert(
        type=type,
        severity=severity,
        message=message,
        context=context,
        location_id=location_id,
        item_id=item_id,
        status=AlertStatus.OPEN,
    )
    session.add(alert)
    await session.commit()
    await session.refresh(alert)
    return alert


async def ack_alert(session: AsyncSession, alert_id: str, user_id: Optional[str] = None) -> Alert:
    alert = await session.get(Alert, alert_id)
    if not alert:
        raise ValueError("Alert not found")
    alert.status = AlertStatus.ACK
    alert.ack_by = user_id
    alert.ack_at = now()
    session.add(alert)
    await session.commit()
    await session.refresh(alert)
    return alert


async def resolve_alert(session: AsyncSession, alert_id: str, user_id: Optional[str] = None) -> Alert:
    alert = await session.get(Alert, alert_id)
    if not alert:
        raise ValueError("Alert not found")
    alert.status = AlertStatus.DONE
    alert.ack_by = user_id
    alert.ack_at = now()
    session.add(alert)
    await session.commit()
    await session.refresh(alert)
    return alert


async def maybe_resolve_open_low_stock(
    session: AsyncSession, type: AlertType, item_id, location_id
) -> None:
    """Helper to resolve stale alerts if conditions clear (optional future use)."""
    result = await session.execute(
        select(Alert).where(
            Alert.type == type,
            Alert.item_id == item_id,
            Alert.location_id == location_id,
            Alert.status != AlertStatus.DONE,
        )
    )
    alerts = result.scalars().all()
    for alert in alerts:
        alert.status = AlertStatus.DONE
        alert.ack_at = now()
        session.add(alert)
    if alerts:
        await session.commit()

