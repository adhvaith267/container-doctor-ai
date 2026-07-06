"""SQLite persistence for ContainerDoctor incident records."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from datetime import datetime, timezone
from os import PathLike
from pathlib import Path
from typing import Any


DATABASE_PATH = Path(__file__).resolve().parents[1] / "db" / "sqlite.db"

_CREATE_INCIDENTS_TABLE = """
CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    container TEXT NOT NULL,
    errors TEXT NOT NULL,
    logs TEXT NOT NULL DEFAULT '',
    root_cause TEXT NOT NULL,
    severity TEXT NOT NULL,
    action TEXT NOT NULL,
    decision TEXT NOT NULL DEFAULT '{}',
    result TEXT NOT NULL,
    timeline TEXT NOT NULL DEFAULT '[]',
    timestamp TEXT NOT NULL
)
"""

_INCIDENT_MIGRATIONS = {
    "logs": "TEXT NOT NULL DEFAULT ''",
    "decision": "TEXT NOT NULL DEFAULT '{}'",
    "timeline": "TEXT NOT NULL DEFAULT '[]'",
}


def _resolve_database_path(database_path: str | PathLike[str] | None) -> Path:
    return Path(database_path) if database_path is not None else DATABASE_PATH


def _connect(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path, timeout=5.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def _to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)


def _from_json(value: str) -> Any:
    return json.loads(value)


def initialize_database(
    database_path: str | PathLike[str] | None = None,
) -> None:
    """Create the database directory and incidents table if they do not exist."""
    path = _resolve_database_path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with _connect(path) as connection:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute(_CREATE_INCIDENTS_TABLE)
        existing_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(incidents)"
            ).fetchall()
        }
        for column, definition in _INCIDENT_MIGRATIONS.items():
            if column not in existing_columns:
                connection.execute(
                    f"ALTER TABLE incidents ADD COLUMN {column} {definition}"
                )


def insert_incident(
    record: Mapping[str, Any],
    database_path: str | PathLike[str] | None = None,
) -> dict[str, Any]:
    """Persist one incident and return its normalized database representation."""
    required_fields = {
        "container",
        "errors",
        "root_cause",
        "severity",
        "action",
        "result",
    }
    missing_fields = required_fields.difference(record)
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"Missing required incident fields: {missing}")

    path = _resolve_database_path(database_path)
    initialize_database(path)

    timestamp = str(
        record.get("timestamp") or datetime.now(timezone.utc).isoformat()
    )
    values = (
        str(record["container"]),
        _to_json(record["errors"]),
        str(record.get("logs", "")),
        str(record["root_cause"]),
        str(record["severity"]),
        str(record["action"]),
        _to_json(record.get("decision", {})),
        _to_json(record["result"]),
        _to_json(record.get("timeline", [])),
        timestamp,
    )

    with _connect(path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO incidents (
                container,
                errors,
                logs,
                root_cause,
                severity,
                action,
                decision,
                result,
                timeline,
                timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )
        incident_id = cursor.lastrowid

    return {
        "id": incident_id,
        "container": values[0],
        "errors": record["errors"],
        "logs": values[2],
        "root_cause": values[3],
        "severity": values[4],
        "action": values[5],
        "decision": record.get("decision", {}),
        "result": record["result"],
        "timeline": record.get("timeline", []),
        "timestamp": timestamp,
    }


def _incident_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "container": row["container"],
        "errors": _from_json(row["errors"]),
        "logs": row["logs"],
        "root_cause": row["root_cause"],
        "severity": row["severity"],
        "action": row["action"],
        "decision": _from_json(row["decision"]),
        "result": _from_json(row["result"]),
        "timeline": _from_json(row["timeline"]),
        "timestamp": row["timestamp"],
    }


def fetch_incidents(
    limit: int | None = None,
    database_path: str | PathLike[str] | None = None,
) -> list[dict[str, Any]]:
    """Fetch incidents newest first, optionally capped by a positive limit."""
    if limit is not None and limit < 1:
        raise ValueError("limit must be a positive integer or None")

    path = _resolve_database_path(database_path)
    initialize_database(path)

    query = """
        SELECT
            id,
            container,
            errors,
            logs,
            root_cause,
            severity,
            action,
            decision,
            result,
            timeline,
            timestamp
        FROM incidents
        ORDER BY id DESC
    """
    parameters: tuple[int, ...] = ()
    if limit is not None:
        query += " LIMIT ?"
        parameters = (limit,)

    with _connect(path) as connection:
        rows = connection.execute(query, parameters).fetchall()

    return [_incident_from_row(row) for row in rows]


def fetch_incident(
    incident_id: int,
    database_path: str | PathLike[str] | None = None,
) -> dict[str, Any] | None:
    """Fetch a single incident by primary key."""
    if incident_id < 1:
        raise ValueError("incident_id must be a positive integer")

    path = _resolve_database_path(database_path)
    initialize_database(path)

    with _connect(path) as connection:
        row = connection.execute(
            """
            SELECT
                id,
                container,
                errors,
                logs,
                root_cause,
                severity,
                action,
                decision,
                result,
                timeline,
                timestamp
            FROM incidents
            WHERE id = ?
            """,
            (incident_id,),
        ).fetchone()

    return _incident_from_row(row) if row is not None else None


def count_incidents(
    database_path: str | PathLike[str] | None = None,
) -> int:
    """Return the number of persisted incidents without loading their contents."""
    path = _resolve_database_path(database_path)
    initialize_database(path)

    with _connect(path) as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS total FROM incidents"
        ).fetchone()

    return int(row["total"]) if row is not None else 0
