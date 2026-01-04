from __future__ import annotations

from typing import Optional
import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.models.entities import (
    Item,
    Customer,
    Supplier,
    StoreLocation,
    StockMovement,
    ReorderRule,
)

router = APIRouter()


class ItemOut(BaseModel):
    id: uuid.UUID
    item_code: Optional[str] = None
    sku: Optional[str] = None
    name: Optional[str] = None
    short_name: Optional[str] = None
    barcode: Optional[str] = None
    uom: Optional[str] = None
    brand: Optional[str] = None
    active: bool

    model_config = {"from_attributes": True}


class CustomerOut(BaseModel):
    id: uuid.UUID
    customer_code: Optional[str] = None
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None
    type: Optional[str] = None

    model_config = {"from_attributes": True}


class SupplierOut(BaseModel):
    id: uuid.UUID
    supplier_code: Optional[str] = None
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    payment_terms: Optional[str] = None

    model_config = {"from_attributes": True}


class LocationOut(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class StockBalanceOut(BaseModel):
    item_id: uuid.UUID
    item_code: Optional[str]
    item_name: Optional[str]
    location_id: uuid.UUID
    location_name: Optional[str]
    available: float
    min_level: Optional[float] = None
    max_level: Optional[float] = None


@router.get("/items")
async def list_items(
    session: AsyncSession = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    search: Optional[str] = None,
):
    stmt = select(Item)
    if search:
        like = f"%{search.lower()}%"
        stmt = stmt.where(
            func.lower(Item.name).like(like)
            | func.lower(Item.item_code).like(like)
            | func.lower(Item.barcode).like(like)
        )
    total = await session.scalar(select(func.count()).select_from(stmt.subquery()))
    result = await session.execute(stmt.offset(offset).limit(limit))
    items = result.scalars().all()
    return {"items": [ItemOut.model_validate(i) for i in items], "total": total or 0}


@router.get("/items/{item_id}")
async def get_item(item_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        return {"detail": "Not found"}, 404
    return ItemOut.model_validate(item)


@router.get("/customers")
async def list_customers(
    session: AsyncSession = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    search: Optional[str] = None,
):
    stmt = select(Customer)
    if search:
        like = f"%{search.lower()}%"
        stmt = stmt.where(
            func.lower(Customer.name).like(like)
            | func.lower(Customer.customer_code).like(like)
            | func.lower(Customer.phone).like(like)
        )
    total = await session.scalar(select(func.count()).select_from(stmt.subquery()))
    result = await session.execute(stmt.offset(offset).limit(limit))
    customers = result.scalars().all()
    return {
        "items": [CustomerOut.model_validate(c) for c in customers],
        "total": total or 0,
    }


@router.get("/customers/{customer_id}")
async def get_customer(customer_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        return {"detail": "Not found"}, 404
    return CustomerOut.model_validate(customer)


@router.get("/suppliers")
async def list_suppliers(
    session: AsyncSession = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    search: Optional[str] = None,
):
    stmt = select(Supplier)
    if search:
        like = f"%{search.lower()}%"
        stmt = stmt.where(
            func.lower(Supplier.name).like(like)
            | func.lower(Supplier.supplier_code).like(like)
            | func.lower(Supplier.phone).like(like)
        )
    total = await session.scalar(select(func.count()).select_from(stmt.subquery()))
    result = await session.execute(stmt.offset(offset).limit(limit))
    suppliers = result.scalars().all()
    return {
        "items": [SupplierOut.model_validate(s) for s in suppliers],
        "total": total or 0,
    }


@router.get("/suppliers/{supplier_id}")
async def get_supplier(supplier_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        return {"detail": "Not found"}, 404
    return SupplierOut.model_validate(supplier)


@router.get("/locations")
async def list_locations(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(StoreLocation))
    locations = result.scalars().all()
    return {"items": [LocationOut.model_validate(l) for l in locations]}


@router.get("/inventory/balances")
async def inventory_balances(
    session: AsyncSession = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    search: Optional[str] = None,
    location_id: Optional[str] = Query(None),
):
    base = (
        select(
            StockMovement.item_id,
            StockMovement.location_id,
            func.sum(StockMovement.qty_delta).label("available"),
        )
        .group_by(StockMovement.item_id, StockMovement.location_id)
        .subquery()
    )

    stmt = (
        select(
            Item.id.label("item_id"),
            Item.item_code,
            Item.name.label("item_name"),
            StoreLocation.id.label("location_id"),
            StoreLocation.name.label("location_name"),
            base.c.available,
            ReorderRule.min_level,
            ReorderRule.max_level,
        )
        .join(Item, Item.id == base.c.item_id)
        .join(StoreLocation, StoreLocation.id == base.c.location_id)
        .outerjoin(
            ReorderRule,
            (ReorderRule.item_id == Item.id)
            & (ReorderRule.location_id == StoreLocation.id),
        )
    )

    if location_id:
        stmt = stmt.where(StoreLocation.id == location_id)
    if search:
        like = f"%{search.lower()}%"
        stmt = stmt.where(
            func.lower(Item.name).like(like) | func.lower(Item.item_code).like(like)
        )

    total = await session.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = await session.execute(stmt.offset(offset).limit(limit))
    items = [
        StockBalanceOut(
            item_id=r.item_id,
            item_code=r.item_code,
            item_name=r.item_name,
            location_id=r.location_id,
            location_name=r.location_name,
            available=float(r.available or 0),
            min_level=float(r.min_level) if r.min_level is not None else None,
            max_level=float(r.max_level) if r.max_level is not None else None,
        )
        for r in rows
    ]
    return {"items": items, "total": total or 0}

