"""
Reward and Redemption Repository.
Handles reward inventory, redemption requests, and spin history.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional

from database.connection import get_db_connection
from utils.time_utils import to_iso_string


class RewardRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def get_active_rewards(self, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM rewards WHERE is_active = 1 ORDER BY required_points ASC"

        def _execute(c: sqlite3.Connection):
            return [dict(r) for r in c.execute(query).fetchall()]

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def get_by_id(self, reward_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM rewards WHERE id = ?"

        def _execute(c: sqlite3.Connection):
            row = c.execute(query, (reward_id,)).fetchone()
            return dict(row) if row else None

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def create_redemption(
        self,
        user_id: int,
        reward_id: int,
        points_cost: int,
        notes: str = "",
        conn: Optional[sqlite3.Connection] = None,
    ) -> Dict[str, Any]:
        """Creates a pending redemption record."""
        now = to_iso_string()
        query = """
            INSERT INTO reward_redemptions (user_id, reward_id, points_cost, status, requested_at, notes)
            VALUES (?, ?, ?, 'pending', ?, ?)
        """

        def _execute(c: sqlite3.Connection) -> Dict[str, Any]:
            cur = c.cursor()
            cur.execute(query, (user_id, reward_id, points_cost, now, notes))
            redemption_id = cur.lastrowid
            return {
                "id": redemption_id,
                "user_id": user_id,
                "reward_id": reward_id,
                "points_cost": points_cost,
                "status": "pending",
                "requested_at": now,
                "notes": notes,
            }

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def get_user_redemptions(self, user_id: int, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
        """Retrieves redemptions for a user joined with reward details."""
        query = """
            SELECT rr.*, r.name as reward_name, r.reward_type
            FROM reward_redemptions rr
            JOIN rewards r ON rr.reward_id = r.id
            WHERE rr.user_id = ?
            ORDER BY rr.id DESC
        """

        def _execute(c: sqlite3.Connection):
            return [dict(r) for r in c.execute(query, (user_id,)).fetchall()]

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def get_all_redemptions(self, status: Optional[str] = None, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
        """Retrieves all redemptions for admin review."""
        if status:
            query = """
                SELECT rr.*, r.name as reward_name, u.email as user_email, u.name as user_name
                FROM reward_redemptions rr
                JOIN rewards r ON rr.reward_id = r.id
                JOIN users u ON rr.user_id = u.id
                WHERE rr.status = ?
                ORDER BY rr.id DESC
            """
            params = (status,)
        else:
            query = """
                SELECT rr.*, r.name as reward_name, u.email as user_email, u.name as user_name
                FROM reward_redemptions rr
                JOIN rewards r ON rr.reward_id = r.id
                JOIN users u ON rr.user_id = u.id
                ORDER BY rr.id DESC
            """
            params = ()

        def _execute(c: sqlite3.Connection):
            return [dict(r) for r in c.execute(query, params).fetchall()]

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def update_redemption_status(
        self,
        redemption_id: int,
        status: str,
        reviewed_by: int,
        notes: str = "",
        conn: Optional[sqlite3.Connection] = None,
    ) -> bool:
        """Updates redemption status to 'approved' or 'rejected'."""
        now = to_iso_string()
        query = """
            UPDATE reward_redemptions
            SET status = ?, reviewed_at = ?, reviewed_by = ?, notes = ?
            WHERE id = ? AND status = 'pending'
        """

        def _execute(c: sqlite3.Connection) -> bool:
            res = c.execute(query, (status, now, reviewed_by, notes, redemption_id))
            return res.rowcount > 0

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def decrement_stock(self, reward_id: int, conn: Optional[sqlite3.Connection] = None) -> bool:
        """Decrements stock if not NULL and > 0."""
        query = """
            UPDATE rewards
            SET stock_quantity = stock_quantity - 1
            WHERE id = ? AND (stock_quantity IS NULL OR stock_quantity > 0)
        """

        def _execute(c: sqlite3.Connection) -> bool:
            res = c.execute(query, (reward_id,))
            return res.rowcount > 0

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def increment_stock(self, reward_id: int, conn: Optional[sqlite3.Connection] = None) -> bool:
        """Restores stock on rejection."""
        query = "UPDATE rewards SET stock_quantity = stock_quantity + 1 WHERE id = ? AND stock_quantity IS NOT NULL"

        def _execute(c: sqlite3.Connection) -> bool:
            res = c.execute(query, (reward_id,))
            return res.rowcount > 0

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def record_spin(
        self,
        user_id: int,
        points: int,
        idempotency_key: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Dict[str, Any]:
        """Records a Lucky Scan Spin event."""
        now = to_iso_string()
        query = "INSERT INTO spin_history (user_id, points_awarded, created_at, idempotency_key) VALUES (?, ?, ?, ?)"

        def _execute(c: sqlite3.Connection) -> Dict[str, Any]:
            cur = c.cursor()
            cur.execute(query, (user_id, points, now, idempotency_key))
            return {"id": cur.lastrowid, "user_id": user_id, "points": points, "created_at": now}

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def get_last_spin(self, user_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM spin_history WHERE user_id = ? ORDER BY id DESC LIMIT 1"

        def _execute(c: sqlite3.Connection):
            row = c.execute(query, (user_id,)).fetchone()
            return dict(row) if row else None

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)
