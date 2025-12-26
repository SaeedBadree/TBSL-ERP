from __future__ import annotations

import argparse

from sqlalchemy import select

from app.models.entities import Supplier, SupplierSourceFields
from app.scripts.utils import RejectLogger, common_argparser, iter_dict_rows, session_scope, utcnow


ESSENTIAL_HEADERS = ["Distributor Code", "Distributor Name"]


async def upsert_supplier(session, row: dict, source_file: str):
    code = row.get("Distributor Code") or row.get("Distributor code")
    name = row.get("Distributor Name") or row.get("Distributor name")
    if not code or not name:
        raise ValueError("Missing supplier code or name")

    stmt = select(Supplier).where(Supplier.supplier_code == code)
    existing = (await session.execute(stmt)).scalar_one_or_none()

    if existing:
        existing.name = name
        existing.phone = row.get("Phone") or existing.phone
        existing.email = row.get("Email") or existing.email
        existing.address = row.get("Address") or existing.address
        existing.payment_terms = row.get("Payment Terms") or existing.payment_terms
        supplier = existing
    else:
        supplier = Supplier(
            supplier_code=code,
            name=name,
            phone=row.get("Phone"),
            email=row.get("Email"),
            address=row.get("Address"),
            payment_terms=row.get("Payment Terms"),
        )
        session.add(supplier)
        await session.flush()

    source = await session.get(SupplierSourceFields, {"supplier_id": supplier.id})
    if source:
        source.source = row
        source.source_file = source_file
        source.imported_at = utcnow()
    else:
        session.add(
            SupplierSourceFields(
                supplier_id=supplier.id,
                source=row,
                source_file=source_file,
                imported_at=utcnow(),
            )
        )


async def import_suppliers(path: str, db_url: str, reject_log: str):
    logger = RejectLogger(reject_log)
    async with session_scope(db_url) as session:
        async with session.begin():
            for row_num, row in iter_dict_rows(path, ESSENTIAL_HEADERS):
                try:
                    await upsert_supplier(session, row, source_file=path)
                except Exception as exc:  # noqa: BLE001
                    logger.log(row_num, str(exc))
            await session.commit()


def build_parser():
    parser = common_argparser("import_suppliers")
    parser.add_argument("--suppliers", required=True, help="Path to suppliers CSV or ZIP")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    import asyncio

    asyncio.run(import_suppliers(args.suppliers, args.db_url, args.reject_log))


if __name__ == "__main__":
    main()

