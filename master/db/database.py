"""
SQLite database connection management for AIPipeline.

Based on the DirectorsConsole storage pattern.
Uses Python's built-in sqlite3 module (no ORM).
"""

from __future__ import annotations

import sqlite3
import os
from pathlib import Path
from typing import Optional, Iterator

from loguru import logger


class Database:
    """SQLite database with WAL mode, migrations, and helper methods."""

    def __init__(self, db_path: str) -> None:
        self._path = Path(db_path)

    def initialize(self) -> None:
        """Create parent dirs and run migrations."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._run_migrations()
        logger.info(f"Database initialized at {self._path}")

    def connect(self) -> sqlite3.Connection:
        """Get a new connection (caller must close it)."""
        return self._connect()

    def execute(self, sql: str, params: tuple = ()) -> None:
        with self._connect() as conn:
            conn.execute(sql, params)
            conn.commit()

    def execute_many(self, sql: str, params_list: list[tuple]) -> None:
        with self._connect() as conn:
            conn.executemany(sql, params_list)
            conn.commit()

    def fetchone(self, sql: str, params: tuple = ()) -> Optional[dict]:
        with self._connect() as conn:
            cursor = conn.execute(sql, params)
            row = cursor.fetchone()
            return dict(row) if row else None

    def fetchall(self, sql: str, params: tuple = ()) -> list[dict]:
        with self._connect() as conn:
            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    # -- Internal --

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _run_migrations(self) -> None:
        with self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)"
            )
            current = self._get_schema_version(conn)

            for version, sql_path in self._iter_migration_files():
                if version <= current:
                    continue
                logger.info(f"Running migration {sql_path.name} (v{version})")
                script = sql_path.read_text(encoding="utf-8")
                conn.executescript(script)
                conn.execute("DELETE FROM schema_version")
                conn.execute(
                    "INSERT INTO schema_version (version) VALUES (?)", (version,)
                )
                conn.commit()

    def _get_schema_version(self, conn: sqlite3.Connection) -> int:
        cursor = conn.execute("SELECT version FROM schema_version LIMIT 1")
        row = cursor.fetchone()
        return int(row["version"]) if row else 0

    def _iter_migration_files(self) -> Iterator[tuple[int, Path]]:
        migrations_dir = Path(__file__).resolve().parent / "migrations"
        if not migrations_dir.exists():
            return

        migrations = []
        for path in migrations_dir.glob("*.sql"):
            try:
                version = int(path.stem.split("_")[0])
                migrations.append((version, path))
            except ValueError:
                logger.warning(f"Skipping migration file with bad name: {path.name}")

        yield from sorted(migrations, key=lambda item: item[0])


# -- Singleton --

_db_instance: Optional[Database] = None


def get_database() -> Database:
    """Get the singleton Database instance. Must call init_database() first."""
    global _db_instance
    if _db_instance is None:
        from ..utils.config import settings
        _db_instance = Database(settings.DATABASE_PATH)
        _db_instance.initialize()
    return _db_instance
