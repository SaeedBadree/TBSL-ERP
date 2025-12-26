from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.security import require_roles, get_current_user
from app.models.entities import Alert, AlertSeverity, AlertStatus, AlertType, StaffRole
from app.schemas.alerts import AlertListResponse, AlertResponse
from app.services.alert_service import ack_alert, resolve_alert

router = APIRouter()

ManagerOrAdmin = Depends(require_roles([StaffRole.MANAGER, StaffRole.ADMIN, StaffRole.AUDITOR]))


@router.get("/alerts", response_model=AlertListResponse, dependencies=[ManagerOrAdmin])
async def list_alerts(
    status: AlertStatus | None = None,
    type: AlertType | None = None,
    severity: AlertSeverity | None = None,
    location_id: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    conditions = []
    if status:
        conditions.append(Alert.status == status)
    if type:
        conditions.append(Alert.type == type)
    if severity:
        conditions.append(Alert.severity == severity)
    if location_id:
        conditions.append(Alert.location_id == location_id)

    where_clause = and_(*conditions) if conditions else None

    total = (
        await session.execute(
            select(func.count()).select_from(Alert).where(where_clause) if where_clause else select(func.count()).select_from(Alert)
        )
    ).scalar_one()

    query = select(Alert)
    if where_clause is not None:
        query = query.where(where_clause)
    query = query.order_by(Alert.created_at.desc()).offset(offset).limit(limit)
    alerts = (await session.execute(query)).scalars().all()

    return AlertListResponse(
        total=total,
        items=[
            AlertResponse(
                id=str(a.id),
                type=a.type,
                severity=a.severity,
                status=a.status,
                message=a.message,
                context=a.context,
                location_id=str(a.location_id) if a.location_id else None,
                item_id=str(a.item_id) if a.item_id else None,
                created_at=a.created_at,
                ack_by=str(a.ack_by) if a.ack_by else None,
                ack_at=a.ack_at,
            )
            for a in alerts
        ],
    )


@router.post("/alerts/{alert_id}/ack", response_model=AlertResponse, dependencies=[ManagerOrAdmin])
async def ack(alert_id: str, session: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    try:
        alert = await ack_alert(session, alert_id, user_id=str(current_user.id))
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found")
    return AlertResponse(
        id=str(alert.id),
        type=alert.type,
        severity=alert.severity,
        status=alert.status,
        message=alert.message,
        context=alert.context,
        location_id=str(alert.location_id) if alert.location_id else None,
        item_id=str(alert.item_id) if alert.item_id else None,
        created_at=alert.created_at,
        ack_by=str(alert.ack_by) if alert.ack_by else None,
        ack_at=alert.ack_at,
    )


@router.post("/alerts/{alert_id}/resolve", response_model=AlertResponse, dependencies=[ManagerOrAdmin])
async def resolve(alert_id: str, session: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    try:
        alert = await resolve_alert(session, alert_id, user_id=str(current_user.id))
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found")
    return AlertResponse(
        id=str(alert.id),
        type=alert.type,
        severity=alert.severity,
        status=alert.status,
        message=alert.message,
        context=alert.context,
        location_id=str(alert.location_id) if alert.location_id else None,
        item_id=str(alert.item_id) if alert.item_id else None,
        created_at=alert.created_at,
        ack_by=str(alert.ack_by) if alert.ack_by else None,
        ack_at=alert.ack_at,
    )

