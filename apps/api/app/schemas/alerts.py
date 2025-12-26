from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.entities import AlertSeverity, AlertStatus, AlertType


class AlertResponse(BaseModel):
    id: str
    type: AlertType
    severity: AlertSeverity
    status: AlertStatus
    message: str
    context: dict
    location_id: Optional[str] = None
    item_id: Optional[str] = None
    created_at: datetime
    ack_by: Optional[str] = None
    ack_at: Optional[datetime] = None


class AlertListResponse(BaseModel):
    total: int
    items: list[AlertResponse]

