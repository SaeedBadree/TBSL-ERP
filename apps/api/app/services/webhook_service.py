from __future__ import annotations

import asyncio
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

import httpx
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.entities import WebhookDelivery, WebhookDeliveryStatus, WebhookEndpoint


def _signature(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), body, "sha256").hexdigest()


async def enqueue_event(session: AsyncSession, event_type: str, payload: dict) -> None:
    endpoints = (
        await session.execute(
            select(WebhookEndpoint).where(
                WebhookEndpoint.active.is_(True),
                WebhookEndpoint.events.contains([event_type]),
            )
        )
    ).scalars()

    for ep in endpoints:
        delivery = WebhookDelivery(
            endpoint_id=ep.id,
            event_type=event_type,
            payload=payload,
            status=WebhookDeliveryStatus.PENDING,
            attempts=0,
        )
        session.add(delivery)
    await session.commit()


async def deliver_pending(session: AsyncSession, limit: int = 20) -> None:
    now = datetime.now(timezone.utc)
    deliveries = (
        await session.execute(
            select(WebhookDelivery)
            .join(WebhookEndpoint, WebhookDelivery.endpoint_id == WebhookEndpoint.id)
            .where(
                WebhookDelivery.status == WebhookDeliveryStatus.PENDING,
                WebhookEndpoint.active.is_(True),
                (WebhookDelivery.next_retry_at.is_(None)) | (WebhookDelivery.next_retry_at <= now),
            )
            .limit(limit)
        )
    ).scalars().all()

    if not deliveries:
        return

    async with httpx.AsyncClient(timeout=10) as client:
        for delivery in deliveries:
            endpoint = delivery.endpoint
            body = json.dumps(delivery.payload).encode("utf-8")
            signature = _signature(endpoint.secret, body)
            try:
                resp = await client.post(
                    endpoint.url,
                    content=body,
                    headers={
                        "Content-Type": "application/json",
                        "X-Event-Type": delivery.event_type,
                        "X-Signature": signature,
                    },
                )
                if resp.status_code < 300:
                    delivery.status = WebhookDeliveryStatus.SUCCESS
                else:
                    raise httpx.HTTPStatusError(
                        f"Failed with status {resp.status_code}", request=resp.request, response=resp
                    )
            except Exception as exc:  # noqa: BLE001
                delivery.attempts += 1
                delay = min(60, 2 ** delivery.attempts)
                delivery.next_retry_at = now + timedelta(seconds=delay)
                delivery.last_error = str(exc)
            finally:
                session.add(delivery)
        await session.commit()


async def webhook_worker(session_maker: async_sessionmaker[AsyncSession], interval: int = 15) -> None:
    while True:
        async with session_maker() as session:
            await deliver_pending(session)
        await asyncio.sleep(interval)

