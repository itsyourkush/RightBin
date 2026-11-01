"""
Points and Transaction Repository.
Manages the authoritative immutable points ledger and balances.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional

from database.connection import get_db_connection
from utils.time_utils import to_iso_string


class PointsRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def record_transaction(
        self,
        user_id: int,
        activity_type: str,
        points_delta: int,
        reference_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Dict[str, Any]:
        """
        Inserts a point transaction into the ledger.
        If idempotency_key already exists, raises IntegrityError to prevent double-crediting.
        """
        now = to_iso_string()
        query = """
            INSERT INTO point_transactions (
                user_id, activity_type, reference_id, points_delta, idempotency_key, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """

        def _execute(c: sqlite3.Connection) -> Dict[str, Any]:
            cur = c.cursor()
            cur.execute(query, (user_id, activity_type, reference_id, points_delta, idempotency_key, now))
            tx_id = cur.lastrowid
            return {
                "id": tx_id,
                "user_id": user_id,
                "activity_type": activity_type,
                "reference_id": reference_id,
                "points_delta": points_delta,
                "idempotency_key": idempotency_key,
                "created_at": now,
            }

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def get_user_balance(self, user_id: int, conn: Optional[sqlite3.Connection] = None) -> int:
        """Calculates authoritative point balance as sum of all ledger transactions."""
        query = "SELECT COALESCE(SUM(points_delta), 0) as balance FROM point_transactions WHERE user_id = ?"

        def _execute(c: sqlite3.Connection) -> int:
            row = c.execute(query, (user_id,)).fetchone()
            return int(row["balance"]) if row else 0

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def get_user_transactions(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        conn: Optional[sqlite3.Connection] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves paginated ledger history for a user."""
        query = """
            SELECT * FROM point_transactions
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """

        def _execute(c: sqlite3.Connection):
            rows = c.execute(query, (user_id, limit, offset)).fetchall()
            return [dict(r) for r in rows]

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def get_weekly_points_for_user(
        self,
        user_id: int,
        start_iso: str,
        end_iso: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> int:
        """Sums positive points earned by a user within the specified week boundary."""
        query = """
            SELECT COALESCE(SUM(points_delta), 0) as weekly_pts
            FROM point_transactions
            WHERE user_id = ? AND points_delta > 0 AND created_at >= ? AND created_at <= ?
        """

        def _execute(c: sqlite3.Connection) -> int:
            row = c.execute(query, (user_id, start_iso, end_iso)).fetchone()
            return int(row["weekly_pts"]) if row else 0

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def get_weekly_leaderboard(
        self,
        start_iso: str,
        end_iso: str,
        limit: int = 25,
        conn: Optional[sqlite3.Connection] = None,
    ) -> List[Dict[str, Any]]:
        """
        Calculates weekly leaderboard rankings with privacy-safe display names.
        Tie-breaking rule: Higher weekly points first, then earliest activity timestamp, then higher total points.
        """
        query = """
            SELECT
                u.id as user_id,
                p.display_name,
                COALESCE(SUM(pt.points_delta), 0) as weekly_points,
                MIN(pt.created_at) as first_activity_in_week,
                p.green_score
            FROM users u
            JOIN user_profiles p ON u.id = p.user_id
            JOIN point_transactions pt ON u.id = pt.user_id
            WHERE pt.points_delta > 0
              AND pt.created_at >= ?
              AND pt.created_at <= ?
              AND u.is_active = 1
            GROUP BY u.id, p.display_name, p.green_score
            ORDER BY weekly_points DESC, first_activity_in_week ASC, p.green_score DESC
            LIMIT ?
        """

        def _execute(c: sqlite3.Connection):
            rows = c.execute(query, (start_iso, end_iso, limit)).fetchall()
            return [dict(r) for r in rows]

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def has_idempotency_key(self, key: str, conn: Optional[sqlite3.Connection] = None) -> bool:
        """Checks if a given idempotency key has already been recorded."""
        query = "SELECT 1 FROM point_transactions WHERE idempotency_key = ?"

        def _execute(c: sqlite3.Connection) -> bool:
            return c.execute(query, (key,)).fetchone() is not None

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)
