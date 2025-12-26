from __future__ import annotations

import argparse
import asyncio

from app.scripts.import_items import import_items
from app.scripts.import_customers import import_customers
from app.scripts.import_suppliers import import_suppliers
from app.scripts.utils import common_argparser


def build_parser():
    parser = common_argparser("import_all")
    parser.add_argument("--items", required=False, help="Path to items CSV/ZIP")
    parser.add_argument("--customers", required=False, help="Path to customers CSV/ZIP")
    parser.add_argument("--suppliers", required=False, help="Path to suppliers CSV/ZIP")
    return parser


async def run_all(args):
    if args.items:
        await import_items(args.items, args.db_url, args.reject_log)
    if args.customers:
        await import_customers(args.customers, args.db_url, args.reject_log)
    if args.suppliers:
        await import_suppliers(args.suppliers, args.db_url, args.reject_log)


def main():
    parser = build_parser()
    args = parser.parse_args()
    asyncio.run(run_all(args))


if __name__ == "__main__":
    main()

