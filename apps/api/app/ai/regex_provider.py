from __future__ import annotations

import re
from decimal import Decimal
from typing import List

from app.ai.provider import ExtractedInvoice, ExtractedLine, InvoiceExtractor


LINE_RE = re.compile(r"(?P<name>.+?)\\s+x?(?P<qty>\\d+(?:\\.\\d+)?)\\s+@\\s+(?P<unit>\\d+(?:\\.\\d+)?)", re.IGNORECASE)
TOTAL_RE = re.compile(r"(subtotal|tax|discount|total)[:\\s]+(?P<amount>\\d+(?:\\.\\d+)?)", re.IGNORECASE)
INVOICE_RE = re.compile(r"invoice\\s*(no\\.?|number)[:\\s]+(?P<num>[\\w-]+)", re.IGNORECASE)
DATE_RE = re.compile(r"(\\d{4}-\\d{2}-\\d{2})|(\\d{2}/\\d{2}/\\d{4})")
SUPPLIER_RE = re.compile(r"supplier[:\\s]+(?P<name>.+)", re.IGNORECASE)


def parse_decimal(val: str | None) -> float | None:
    try:
        return float(Decimal(val)) if val is not None else None
    except Exception:
        return None


class RegexInvoiceExtractor(InvoiceExtractor):
    async def extract(self, content: str) -> ExtractedInvoice:
        lines: List[ExtractedLine] = []
        for m in LINE_RE.finditer(content):
            qty = parse_decimal(m.group("qty")) or 0
            unit = parse_decimal(m.group("unit")) or 0
            lines.append(
                ExtractedLine(
                    description=m.group("name").strip(),
                    qty=qty,
                    unit_cost=unit,
                    total=qty * unit,
                )
            )

        totals = {}
        for m in TOTAL_RE.finditer(content):
            totals[m.group(1).lower()] = parse_decimal(m.group("amount"))

        inv_match = INVOICE_RE.search(content)
        date_match = DATE_RE.search(content)
        supp_match = SUPPLIER_RE.search(content)

        return ExtractedInvoice(
            supplier=supp_match.group("name").strip() if supp_match else None,
            invoice_number=inv_match.group("num") if inv_match else None,
            invoice_date=date_match.group(0) if date_match else None,
            subtotal=totals.get("subtotal"),
            tax_total=totals.get("tax"),
            discount_total=totals.get("discount"),
            grand_total=totals.get("total"),
            lines=lines,
        )

