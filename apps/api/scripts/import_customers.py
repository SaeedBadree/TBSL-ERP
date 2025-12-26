from __future__ import annotations

import argparse

from sqlalchemy import select

from app.models.entities import Customer, CustomerSourceFields
from app.scripts.utils import RejectLogger, common_argparser, iter_dict_rows, session_scope, utcnow


ESSENTIAL_HEADERS = ["Customer Code", "Customer Name"]


async def upsert_customer(session, row: dict, source_file: str):
    code = row.get("Customer Code") or row.get("CUSTOMER CODE")
    name = row.get("Customer Name") or row.get("CUSTOMER NAME")
    if not code or not name:
        raise ValueError("Missing customer code or name")

    stmt = select(Customer).where(Customer.customer_code == code)
    existing = (await session.execute(stmt)).scalar_one_or_none()

    if existing:
        existing.name = name
        existing.phone = row.get("Phone") or existing.phone
        existing.email = row.get("Email") or existing.email
        existing.address = row.get("Address") or existing.address
        existing.credit_limit = existing.credit_limit
        existing.credit_days = existing.credit_days
        existing.status = row.get("Status") or existing.status or "active"
        existing.type = row.get("Type") or existing.type
        customer = existing
    else:
        customer = Customer(
            customer_code=code,
            name=name,
            phone=row.get("Phone"),
            email=row.get("Email"),
            address=row.get("Address"),
            credit_limit=None,
            credit_days=None,
            status=row.get("Status") or "active",
            type=row.get("Type"),
        )
        session.add(customer)
        await session.flush()

    source = await session.get(CustomerSourceFields, {"customer_id": customer.id})
    if source:
        source.source = row
        source.source_file = source_file
        source.imported_at = utcnow()
    else:
        session.add(
            CustomerSourceFields(
                customer_id=customer.id,
                source=row,
                source_file=source_file,
                imported_at=utcnow(),
            )
        )


async def import_customers(path: str, db_url: str, reject_log: str):
    logger = RejectLogger(reject_log)
    async with session_scope(db_url) as session:
        async with session.begin():
            for row_num, row in iter_dict_rows(path, ESSENTIAL_HEADERS):
                try:
                    await upsert_customer(session, row, source_file=path)
                except Exception as exc:  # noqa: BLE001
                    logger.log(row_num, str(exc))
            await session.commit()


def build_parser():
    parser = common_argparser("import_customers")
    parser.add_argument("--customers", required=True, help="Path to customers CSV or ZIP")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    import asyncio

    asyncio.run(import_customers(args.customers, args.db_url, args.reject_log))


if __name__ == "__main__":
    main()

