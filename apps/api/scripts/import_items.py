from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
from typing import Optional

from sqlalchemy import select

from app.core.db import Base
from app.core.db import engine as app_engine
from app.models.entities import Item, ItemCategory, ItemSourceFields
from scripts.utils import RejectLogger, common_argparser, iter_dict_rows, session_scope, utcnow


ESSENTIAL_HEADERS = ["Item Code", "Item Name"]


def map_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y"}


async def upsert_item(session, row: dict, source_file: str):
    code = row.get("Item Code") or row.get("ITEM CODE")
    name = row.get("Item Name") or row.get("ITEM NAME")
    if not code or not name:
        raise ValueError("Missing item code or name")

    stmt = select(Item).where(Item.item_code == code)
    existing = (await session.execute(stmt)).scalar_one_or_none()

    category1 = row.get("Category1") or row.get("Category 1")
    category2 = row.get("Category2") or row.get("Category 2")
    category = None
    if category1:
        cat_stmt = select(ItemCategory).where(
            ItemCategory.category1 == category1, ItemCategory.category2 == category2
        )
        category = (await session.execute(cat_stmt)).scalar_one_or_none()
        if not category:
            category = ItemCategory(category1=category1, category2=category2, name=f"{category1}/{category2 or ''}")
            session.add(category)
            await session.flush()

    if existing:
        existing.name = name
        existing.short_name = row.get("Short Name") or row.get("Short name") or existing.short_name
        existing.barcode = row.get("Barcode") or existing.barcode
        existing.uom = row.get("Unit") or row.get("UOM") or existing.uom
        existing.brand = row.get("Brand") or existing.brand
        existing.category_id = category.id if category else existing.category_id
        existing.active = map_bool(row.get("Active", "true"))
        item = existing
    else:
        item = Item(
            item_code=code,
            sku=code,
            name=name,
            short_name=row.get("Short Name") or row.get("Short name"),
            barcode=row.get("Barcode"),
            uom=row.get("Unit") or row.get("UOM"),
            brand=row.get("Brand"),
            category_id=category.id if category else None,
            active=map_bool(row.get("Active", "true")),
        )
        session.add(item)
        await session.flush()

    source = await session.get(ItemSourceFields, {"item_id": item.id})
    if source:
        source.source = row
        source.source_file = source_file
        source.imported_at = utcnow()
    else:
        session.add(
            ItemSourceFields(
                item_id=item.id,
                source=row,
                source_file=source_file,
                imported_at=utcnow(),
            )
        )

    return item


async def import_items(path: str, db_url: str, reject_log: str):
    logger = RejectLogger(reject_log)
    async with session_scope(db_url) as session:
        async with session.begin():
            for row_num, row in iter_dict_rows(path, ESSENTIAL_HEADERS):
                try:
                    await upsert_item(session, row, source_file=path)
                except Exception as exc:  # noqa: BLE001
                    logger.log(row_num, str(exc))
            await session.commit()


def build_parser():
    parser = common_argparser("import_items")
    parser.add_argument("--items", required=True, help="Path to items CSV or ZIP")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    import asyncio

    asyncio.run(import_items(args.items, args.db_url, args.reject_log))


if __name__ == "__main__":
    main()

