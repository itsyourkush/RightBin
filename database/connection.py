"""
SQLite Database Connection Manager.
Ensures foreign-key enforcement, dictionary-like row access,
atomic transaction handling, and isolated connection lifecycles.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional, Union

from config import config
from utils.logging_config import logger


@contextmanager
def get_db_connection(db_path: Optional[Union[str, Path]] = None) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager that yields a configured SQLite connection.
    Enforces foreign keys, enables WAL mode if file-backed, sets Row factory,
    and commits transactions automatically on clean exit (or rolls back on error).
    """
    target_path = Path(db_path) if db_path else config.db_path

    # Ensure parent directory exists for file-backed databases
    if str(target_path) != ":memory:":
        target_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(target_path), timeout=20.0)
    conn.row_factory = sqlite3.Row

    try:
        # Enforce foreign key constraints strictly on every connection
        conn.execute("PRAGMA foreign_keys = ON;")
        if str(target_path) != ":memory:":
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error during transaction, rolled back: {e}")
        raise
    finally:
        conn.close()
