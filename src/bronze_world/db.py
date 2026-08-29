from __future__ import annotations

import contextlib
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Iterator

CANONICAL_HASH_TABLES_V1 = [
    "runs", "places", "routes", "institutions", "households", "persons",
    "character_traits", "household_memberships", "roles", "person_roles",
    "relationships", "resource_stocks", "debts", "obligations", "propositions",
    "knowledge", "memories", "messages", "scenes", "scene_participants",
    "cognition_jobs", "decisions", "actions", "events",
]


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class WorldDB:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "WorldDB":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    @contextlib.contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        if self.conn.in_transaction:
            raise RuntimeError("nested transactions are not supported")
        try:
            self.conn.execute("BEGIN IMMEDIATE")
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def migrate(self) -> None:
        migrations = Path(__file__).with_name("migrations")
        for migration in sorted(migrations.glob("[0-9][0-9][0-9][0-9]_*.sql")):
            self.conn.executescript(migration.read_text(encoding="utf-8"))
        self.conn.commit()

    def schema_version(self) -> int:
        row = self.one("SELECT value FROM schema_meta WHERE key='schema_version'")
        return int(row[0]) if row else 1

    def canonical_hash_tables(self) -> list[str]:
        tables = list(CANONICAL_HASH_TABLES_V1)
        if self.schema_version() >= 2:
            tables.extend(["marriages", "kinship_edges"])
        return tables

    def one(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        return self.conn.execute(sql, params).fetchone()

    def all(self, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        return list(self.conn.execute(sql, params).fetchall())

    def scalar(self, sql: str, params: tuple[Any, ...] = ()) -> Any:
        row = self.one(sql, params)
        return None if row is None else row[0]

    def canonical_state(self, run_id: str) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for table in self.canonical_hash_tables():
            cols = [r[1] for r in self.conn.execute(f"PRAGMA table_info({table})")]
            order = ",".join(cols) if cols else "rowid"
            if table in {"runs", "scenes", "cognition_jobs", "events", "marriages", "kinship_edges"}:
                where = " WHERE run_id = ?"
                params: tuple[Any, ...] = (run_id,)
            elif table in {"decisions", "actions"}:
                if table == "decisions":
                    where = " WHERE job_id IN (SELECT job_id FROM cognition_jobs WHERE run_id = ?)"
                else:
                    where = " WHERE decision_id IN (SELECT decision_id FROM decisions WHERE job_id IN (SELECT job_id FROM cognition_jobs WHERE run_id = ?))"
                params = (run_id,)
            else:
                where = ""
                params = ()
            rows = [dict(r) for r in self.conn.execute(f"SELECT * FROM {table}{where} ORDER BY {order}", params)]
            if table == "runs":
                for row in rows:
                    row.pop("created_at", None)
            out[table] = rows
        return out

    def state_hash(self, run_id: str) -> str:
        payload = canonical_json(self.canonical_state(run_id)).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()
