from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4


@dataclass
class _Result:
    data: List[Dict[str, Any]]


class _Query:
    def __init__(self, tables: Dict[str, List[Dict[str, Any]]], table_name: str):
        self._tables = tables
        self._table_name = table_name
        self._filters: List[Tuple[str, str, Any]] = []
        self._limit: Optional[int] = None
        self._order_key: Optional[str] = None
        self._order_asc: bool = True
        self._insert_rows: Optional[List[Dict[str, Any]]] = None
        self._update_patch: Optional[Dict[str, Any]] = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, column: str, value: Any):
        self._filters.append(("eq", column, value))
        return self

    def limit(self, n: int):
        self._limit = int(n)
        return self

    def order(self, column: str, desc: bool = False):
        self._order_key = column
        self._order_asc = not bool(desc)
        return self

    def insert(self, row: Dict[str, Any] | List[Dict[str, Any]]):
        if isinstance(row, list):
            self._insert_rows = row
        else:
            self._insert_rows = [row]
        return self

    def update(self, patch: Dict[str, Any]):
        self._update_patch = patch
        return self

    def execute(self) -> _Result:
        table = self._tables.get(self._table_name, [])

        # INSERT
        if self._insert_rows is not None:
            inserted: List[Dict[str, Any]] = []
            for r in self._insert_rows:
                row = dict(r)
                row.setdefault("id", str(uuid4()))
                row.setdefault("created_at", datetime.now(timezone.utc).isoformat())
                table.append(row)
                inserted.append(row)
            self._tables[self._table_name] = table
            return _Result(data=inserted)

        # UPDATE (requires filters)
        if self._update_patch is not None:
            updated: List[Dict[str, Any]] = []
            for row in table:
                if self._row_matches(row):
                    row.update(self._update_patch)
                    updated.append(dict(row))
            return _Result(data=updated)

        # SELECT
        rows = [dict(r) for r in table if self._row_matches(r)]
        if self._order_key:
            rows.sort(key=lambda x: (x.get(self._order_key) is None, x.get(self._order_key)), reverse=not self._order_asc)
        if self._limit is not None:
            rows = rows[: self._limit]
        return _Result(data=rows)

    def _row_matches(self, row: Dict[str, Any]) -> bool:
        for op, col, val in self._filters:
            if op == "eq":
                if row.get(col) != val:
                    return False
        return True


class MockSupabaseClient:
    """
    Minimal subset of the Supabase Python client used by this project.
    Supports: table().select().eq().limit().order().insert().update().execute()
    """

    def __init__(self, tables: Dict[str, List[Dict[str, Any]]]):
        self._tables = tables

    def table(self, name: str) -> _Query:
        return _Query(self._tables, name)

