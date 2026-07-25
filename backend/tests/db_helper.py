"""Minimal Mongo-collection-like shim over Postgres.

Keeps the existing pytest fixtures' `db.<table>.<method>(...)` calls working
after the Mongo -> Postgres migration, so the test bodies (HTTP calls +
assertions) didn't need to change, only how fixtures poke the DB directly.
"""
import os

import psycopg2
import psycopg2.extras


def _sync_url() -> str:
    return os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")


def _where(filter: dict):
    clauses = []
    params = []
    for k, v in filter.items():
        if isinstance(v, dict) and "$regex" in v:
            clauses.append(f"{k} ~ %s")
            params.append(v["$regex"])
        else:
            clauses.append(f"{k} = %s")
            params.append(v)
    if not clauses:
        return "TRUE", []
    return " AND ".join(clauses), params


class _Collection:
    def __init__(self, conn, table: str):
        self.conn = conn
        self.table = table

    def insert_one(self, doc: dict):
        cols = list(doc.keys())
        values = [psycopg2.extras.Json(v) if isinstance(v, (dict, list)) else v for v in doc.values()]
        placeholders = ", ".join(["%s"] * len(cols))
        sql = f'INSERT INTO {self.table} ({", ".join(cols)}) VALUES ({placeholders})'
        with self.conn.cursor() as cur:
            cur.execute(sql, values)
        self.conn.commit()

    def find_one(self, filter: dict):
        where, params = _where(filter)
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(f"SELECT * FROM {self.table} WHERE {where} LIMIT 1", params)
            return cur.fetchone()

    def count_documents(self, filter: dict) -> int:
        where, params = _where(filter)
        with self.conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {self.table} WHERE {where}", params)
            return cur.fetchone()[0]

    def delete_one(self, filter: dict):
        where, params = _where(filter)
        with self.conn.cursor() as cur:
            cur.execute(f"DELETE FROM {self.table} WHERE {where}", params)
        self.conn.commit()

    delete_many = delete_one


class TestDB:
    def __init__(self):
        self.conn = psycopg2.connect(_sync_url())
        self.users = _Collection(self.conn, "users")
        self.user_sessions = _Collection(self.conn, "user_sessions")
        self.allowed_emails = _Collection(self.conn, "allowed_emails")
        self.settings = _Collection(self.conn, "settings")
        self.shipments = _Collection(self.conn, "shipments")
        self.pickups = _Collection(self.conn, "pickups")
