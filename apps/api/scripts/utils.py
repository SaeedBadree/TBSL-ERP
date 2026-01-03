from __future__ import annotations

import argparse
import csv
import io
import os
import zipfile
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AsyncIterator, Iterable, Iterator, Sequence

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


def _open_text_stream(path: str) -> Iterator[list[str]]:
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path, "r") as zf:
            first = zf.namelist()[0]
            with zf.open(first) as f:
                for line in io.TextIOWrapper(f, encoding="utf-8-sig"):
                    yield next(csv.reader([line]))
    else:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            for row in reader:
                yield row


def detect_header(rows: Sequence[str], required: Iterable[str]) -> bool:
    row_lower = {c.strip().lower() for c in rows}
    return all(r.lower() in row_lower for r in required)


def iter_dict_rows(path: str, required_headers: Iterable[str]) -> Iterator[tuple[int, dict]]:
    """
    Yield (row_index, row_dict) after skipping preamble lines until a header is found.
    Row index is 1-based from the raw file.
    """
    rows_iter = _open_text_stream(path)
    header = None
    buffered: list[list[str]] = []
    for idx, row in enumerate(rows_iter, start=1):
        if detect_header(row, required_headers):
            header = [c.strip() for c in row]
            break
        buffered.append(row)
    if not header:
        raise ValueError(f"Header not found in {path}")

    # Consume remaining rows including any buffered after header
    def dict_reader():
        for r in buffered:
            yield r
        yield from rows_iter

    for offset, row in enumerate(dict_reader(), start=1):
        if not any(cell.strip() for cell in row):
            continue
        row_dict = {header[i]: row[i].strip() if i < len(row) else "" for i in range(len(header))}
        yield idx + offset, row_dict


@dataclass
class RejectLogger:
    path: str

    def log(self, row_num: int, reason: str) -> None:
        dirname = os.path.dirname(self.path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(f"{row_num},{reason}\n")


@asynccontextmanager
async def session_scope(db_url: str | None = None) -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(db_url or settings.database_url, future=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
            await engine.dispose()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def common_argparser(prog: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=prog)
    parser.add_argument("--db-url", default=settings.database_url, help="Database URL")
    parser.add_argument("--reject-log", default="rejects.log", help="File to log rejects")
    return parser

