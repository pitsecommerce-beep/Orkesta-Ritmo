"""Shared test fixtures: mock Supabase client + auth dependencies."""

from __future__ import annotations

from typing import Optional
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.db import get_supabase, get_current_user_id
from app.main import app


class FakeResponse:
    def __init__(self, data=None, count=None):
        self.data = data or []
        self.count = count


class FakeQueryBuilder:
    def __init__(self, table_name: str, store: dict):
        self._table = table_name
        self._store = store
        self._filters = {}
        self._data = None
        self._count_mode = None
        self._single = False
        self._order_fields = []
        self._limit_val = None

    def select(self, *args, count=None, **kwargs):
        self._count_mode = count
        return self

    def insert(self, data):
        self._data = data
        return self

    def upsert(self, data, on_conflict=None):
        self._data = data
        return self

    def update(self, data):
        self._data = data
        return self

    def delete(self):
        return self

    def eq(self, col, val):
        self._filters[col] = val
        return self

    def neq(self, col, val):
        return self

    def is_(self, col, val):
        return self

    def not_(self):
        return self

    def in_(self, col, vals):
        return self

    def single(self):
        self._single = True
        return self

    def order(self, col, desc=False):
        return self

    def limit(self, val):
        self._limit_val = val
        return self

    def execute(self):
        rows = self._store.get(self._table, [])
        if self._data is not None and not self._filters:
            import uuid
            record = {**self._data}
            if "id" not in record:
                record["id"] = str(uuid.uuid4())
            rows.append(record)
            self._store.setdefault(self._table, [])
            self._store[self._table] = rows
            return FakeResponse(data=[record])

        if self._data is not None and self._filters:
            matched = [r for r in rows if all(r.get(k) == v for k, v in self._filters.items())]
            if matched:
                for r in matched:
                    r.update(self._data)
                return FakeResponse(data=matched)
            return FakeResponse(data=[])

        if self._filters:
            matched = [r for r in rows if all(r.get(k) == v for k, v in self._filters.items())]
        else:
            matched = rows

        if self._count_mode == "exact":
            return FakeResponse(data=matched, count=len(matched))

        if self._single:
            return FakeResponse(data=matched[0] if matched else None)

        return FakeResponse(data=matched)


class FakeSupabaseClient:
    def __init__(self):
        self._store: dict[str, list] = {}
        self.postgrest = MagicMock()
        self.auth = MagicMock()

    def table(self, name: str) -> FakeQueryBuilder:
        return FakeQueryBuilder(name, self._store)


_fake_db = FakeSupabaseClient()
_fake_user_id = "test-user-id-00000"


def _override_get_supabase():
    return _fake_db


async def _override_get_current_user_id() -> Optional[str]:
    return _fake_user_id


app.dependency_overrides[get_supabase] = _override_get_supabase
app.dependency_overrides[get_current_user_id] = _override_get_current_user_id


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    _fake_db._store.clear()
    yield
