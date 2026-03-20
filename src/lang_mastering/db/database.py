"""SQLite database connection and migration management."""

import sqlite3
from pathlib import Path
from typing import Optional

from lang_mastering.db.migrations import SCHEMA_SQL


class Database:
    """Manages SQLite database connection and schema migrations."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Default to data/lang_mastering.db relative to project root
            db_path = str(Path(__file__).parent.parent.parent.parent / "data" / "lang_mastering.db")
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._ensure_directory()
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def _ensure_directory(self):
        """Create parent directory if it doesn't exist."""
        path = Path(self.db_path)
        path.parent.mkdir(parents=True, exist_ok=True)

    def run_migrations(self):
        """Execute schema creation SQL."""
        self.conn.executescript(SCHEMA_SQL)

    def close(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        self.run_migrations()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
