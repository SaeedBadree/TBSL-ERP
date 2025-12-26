from __future__ import annotations

from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.security import require_roles
from app.models.entities import (
    ReorderRule,
    StaffRole,
    WebhookEndpoint,
    StockMovement,
    Item,
    StoreLocation,
)
from app.schemas.reorder import (
    ReorderRuleCreate,
    ReorderRuleResponse,
    WebhookEndpointCreate,
    WebhookEndpointResponse,
)

router = APIRouter()


Admin = Depends(require_roles([StaffRole.MANAGER, StaffRole.ADMIN]))


@router.post("/reorder-rules", response_model=ReorderRuleResponse, dependencies=[Admin])
async def create_reorder_rule(payload: ReorderRuleCreate, session: AsyncSession = Depends(get_session)):
    rule = ReorderRule(**payload.model_dump())
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return ReorderRuleResponse(id=str(rule.id), **payload.model_dump())


@router.get("/reorder-rules", response_model=List[ReorderRuleResponse], dependencies=[Admin])
async def list_reorder_rules(session: AsyncSession = Depends(get_session)):
    rules = (await session.execute(select(ReorderRule))).scalars().all()
    return [
        ReorderRuleResponse(
            id=str(r.id),
            item_id=str(r.item_id),
            location_id=str(r.location_id),
            min_level=r.min_level,
            max_level=r.max_level,
            reorder_qty=r.reorder_qty,
            preferred_supplier_id=str(r.preferred_supplier_id) if r.preferred_supplier_id else None,
            lead_time_days=r.lead_time_days,
            active=r.active,
        )
        for r in rules
    ]


@router.put("/reorder-rules/{rule_id}", response_model=ReorderRuleResponse, dependencies=[Admin])
async def update_reorder_rule(
    rule_id: str, payload: ReorderRuleCreate, session: AsyncSession = Depends(get_session)
):
    rule = await session.get(ReorderRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump().items():
        setattr(rule, k, v)
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return ReorderRuleResponse(id=str(rule.id), **payload.model_dump())


@router.delete("/reorder-rules/{rule_id}", status_code=204, dependencies=[Admin])
async def delete_reorder_rule(rule_id: str, session: AsyncSession = Depends(get_session)):
    rule = await session.get(ReorderRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Not found")
    await session.delete(rule)
    await session.commit()
    return None


@router.post("/webhook-endpoints", response_model=WebhookEndpointResponse, dependencies=[Admin])
async def create_webhook_endpoint(
    payload: WebhookEndpointCreate, session: AsyncSession = Depends(get_session)
):
    endpoint = WebhookEndpoint(**payload.model_dump())
    session.add(endpoint)
    await session.commit()
    await session.refresh(endpoint)
    return WebhookEndpointResponse(id=str(endpoint.id), **payload.model_dump())


@router.get("/webhook-endpoints", response_model=List[WebhookEndpointResponse], dependencies=[Admin])
async def list_webhook_endpoints(session: AsyncSession = Depends(get_session)):
    endpoints = (await session.execute(select(WebhookEndpoint))).scalars().all()
    return [
        WebhookEndpointResponse(
            id=str(ep.id),
            name=ep.name,
            url=ep.url,
            secret=ep.secret,
            events=ep.events,
            active=ep.active,
        )
        for ep in endpoints
    ]


@router.put("/webhook-endpoints/{endpoint_id}", response_model=WebhookEndpointResponse, dependencies=[Admin])
async def update_webhook_endpoint(
    endpoint_id: str, payload: WebhookEndpointCreate, session: AsyncSession = Depends(get_session)
):
    endpoint = await session.get(WebhookEndpoint, endpoint_id)
    if not endpoint:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump().items():
        setattr(endpoint, k, v)
    session.add(endpoint)
    await session.commit()
    await session.refresh(endpoint)
    return WebhookEndpointResponse(id=str(endpoint.id), **payload.model_dump())


@router.delete("/webhook-endpoints/{endpoint_id}", status_code=204, dependencies=[Admin])
async def delete_webhook_endpoint(endpoint_id: str, session: AsyncSession = Depends(get_session)):
    endpoint = await session.get(WebhookEndpoint, endpoint_id)
    if not endpoint:
        raise HTTPException(status_code=404, detail="Not found")
    await session.delete(endpoint)
    await session.commit()
    return None


@router.get("/dashboard/low-stock", dependencies=[Admin])
async def low_stock_dashboard(session: AsyncSession = Depends(get_session)):
    subq = (
        select(
            StockMovement.item_id,
            StockMovement.location_id,
            func.coalesce(func.sum(StockMovement.qty_delta), 0).label("available"),
        )
        .group_by(StockMovement.item_id, StockMovement.location_id)
        .subquery()
    )

    results = await session.execute(
        select(
            ReorderRule,
            subq.c.available,
            Item.name,
            StoreLocation.name,
        )
        .join(subq, (ReorderRule.item_id == subq.c.item_id) & (ReorderRule.location_id == subq.c.location_id))
        .join(Item, Item.id == ReorderRule.item_id)
        .join(StoreLocation, StoreLocation.id == ReorderRule.location_id)
        .where(ReorderRule.active.is_(True), subq.c.available <= ReorderRule.min_level)
    )

    return [
        {
            "rule_id": str(rule.id),
            "item_id": str(rule.item_id),
            "item_name": item_name,
            "location_id": str(rule.location_id),
            "location_name": loc_name,
            "available": str(available),
            "min_level": str(rule.min_level),
            "max_level": str(rule.max_level),
        }
        for rule, available, item_name, loc_name in results.all()
    ]

