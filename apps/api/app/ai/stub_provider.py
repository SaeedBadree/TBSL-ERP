from __future__ import annotations

from app.ai.provider import ExtractedInvoice, ExtractedLine, InvoiceExtractor


class StubInvoiceExtractor(InvoiceExtractor):
    async def extract(self, content: str) -> ExtractedInvoice:
        # Deterministic stub for now
        return ExtractedInvoice(
            supplier="Demo Supplier",
            invoice_number="INV-123",
            invoice_date="2024-01-01",
            subtotal=100.0,
            tax_total=10.0,
            discount_total=0.0,
            grand_total=110.0,
            lines=[
                ExtractedLine(description="Widget A", qty=2, unit_cost=25.0, total=50.0),
                ExtractedLine(description="Widget B", qty=1, unit_cost=50.0, total=50.0),
            ],
        )

