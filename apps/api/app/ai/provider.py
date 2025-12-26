from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import List, Optional


@dataclass
class ExtractedLine:
    description: str
    qty: float
    unit_cost: float
    total: float


@dataclass
class ExtractedInvoice:
    supplier: Optional[str]
    invoice_number: Optional[str]
    invoice_date: Optional[str]
    subtotal: Optional[float]
    tax_total: Optional[float]
    discount_total: Optional[float]
    grand_total: Optional[float]
    lines: List[ExtractedLine]


class InvoiceExtractor(ABC):
    @abstractmethod
    async def extract(self, content: str) -> ExtractedInvoice: ...

