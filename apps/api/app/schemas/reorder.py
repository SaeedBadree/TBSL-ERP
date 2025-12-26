from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, HttpUrl


class ReorderRuleCreate(BaseModel):
    item_id: str
    location_id: str
    min_level: Decimal
    max_level: Decimal
    reorder_qty: Decimal
    preferred_supplier_id: Optional[str] = None
    lead_time_days: Optional[int] = None
    active: bool = True


class ReorderRuleResponse(ReorderRuleCreate):
    id: str


class WebhookEndpointCreate(BaseModel):
    name: str
    url: HttpUrl
    secret: str
    events: List[str]
    active: bool = True


class WebhookEndpointResponse(WebhookEndpointCreate):
    id: str

