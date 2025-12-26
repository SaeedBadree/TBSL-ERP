from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import (
    AiDocument,
    AiDocumentStatus,
    GoodsReceipt,
    GoodsReceiptLine,
    Item,
)


def match_item(items: List[Item], line_desc: str, barcode: str | None = None, sku: str | None = None):
    # barcode
    if barcode:
        for item in items:
            if item.barcode and item.barcode == barcode:
                return item, 1.0
    if sku:
        for item in items:
            if item.sku == sku:
                return item, 0.9
    # fuzzy name
    best = None
    best_score = 0
    for item in items:
        score = fuzz.QRatio(item.name.lower(), line_desc.lower()) / 100.0
        if score > best_score:
            best = item
            best_score = score
    if best:
        return best, best_score
    return None, 0.0


async def confirm_invoice(
    session: AsyncSession,
    ai_doc_id: str,
    location_id: str,
    supplier_id: Optional[str] = None,
) -> GoodsReceipt:
    doc = await session.get(AiDocument, ai_doc_id)
    if not doc or doc.status != AiDocumentStatus.PROCESSED or not doc.extracted_json:
        raise ValueError("AI document not ready")

    payload = doc.extracted_json
    lines_payload = payload.get("lines", [])

    items = (await session.execute(select(Item))).scalars().all()

    grn = GoodsReceipt(
        grn_no=f"GRN-AI-{doc.id}",
        supplier_id=supplier_id,
        location_id=location_id,
    )
    session.add(grn)
    await session.flush()

    for line in lines_payload:
        desc = line.get("description") or ""
        qty = Decimal(str(line.get("qty") or 0))
        unit_cost = Decimal(str(line.get("unit_cost") or 0))
        item, confidence = match_item(items, desc, barcode=line.get("barcode"), sku=line.get("sku"))
        grn_line = GoodsReceiptLine(
            grn_id=grn.id,
            item_id=item.id if item else None,
            qty=qty,
            unit_cost=unit_cost,
            line_total=qty * unit_cost,
        )
        session.add(grn_line)
        # attach confidence into unused field (line_total is used) -> store in grn_line.unit_cost? We keep separate context in payload
        line["match_confidence"] = confidence

    await session.commit()
    await session.refresh(grn)
    return grn

