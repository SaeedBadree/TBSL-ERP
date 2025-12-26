from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.provider import InvoiceExtractor
from app.ai.regex_provider import RegexInvoiceExtractor
from app.ai.stub_provider import StubInvoiceExtractor
from app.models.entities import AiDocument, AiDocumentStatus, AiDocumentType


class AiService:
    def __init__(self, extractor: Optional[InvoiceExtractor] = None):
        self.extractor = extractor or StubInvoiceExtractor()
        self.fallback = RegexInvoiceExtractor()

    async def extract_invoice(self, session: AsyncSession, raw_text: str, filename: str | None, mime: str | None) -> AiDocument:
        doc = AiDocument(
            type=AiDocumentType.INVOICE,
            filename=filename,
            mime=mime,
            raw_text=raw_text,
            status=AiDocumentStatus.PENDING,
        )
        session.add(doc)
        await session.commit()
        await session.refresh(doc)

        try:
            result = await self.extractor.extract(raw_text)
        except Exception:
            result = await self.fallback.extract(raw_text)

        doc.extracted_json = {
            "supplier": result.supplier,
            "invoice_number": result.invoice_number,
            "invoice_date": result.invoice_date,
            "subtotal": result.subtotal,
            "tax_total": result.tax_total,
            "discount_total": result.discount_total,
            "grand_total": result.grand_total,
            "lines": [
                {
                    "description": line.description,
                    "qty": line.qty,
                    "unit_cost": line.unit_cost,
                    "total": line.total,
                }
                for line in result.lines
            ],
        }
        doc.status = AiDocumentStatus.PROCESSED
        session.add(doc)
        await session.commit()
        await session.refresh(doc)
        return doc

