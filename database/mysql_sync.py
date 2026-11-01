"""
MySQL / MariaDB Synchronization Engine.
Connects to an external MySQL / MariaDB server, initializes tables,
and synchronizes local SQLite data to the remote MySQL database.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pymysql
from pymysql.constants import CLIENT

from config import config
from database.connection import get_db_connection
from utils.logging_config import logger


class MySQLSyncManager:
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        ssl: Optional[bool] = None,
    ):
        self.host = host or os.getenv("MYSQL_HOST", "localhost")
        self.port = int(port or os.getenv("MYSQL_PORT", "3306"))
        self.user = user or os.getenv("MYSQL_USER", "root")
        self.password = password or os.getenv("MYSQL_PASSWORD", "")
        self.database = database or os.getenv("MYSQL_DATABASE", "smart_waste_db")
        self.use_ssl = ssl if ssl is not None else (os.getenv("MYSQL_SSL", "False").lower() in ("true", "1", "yes"))

    def get_connection(self, include_db: bool = True) -> pymysql.Connection:
        """Establishes connection to MySQL server."""
        ssl_ctx = {"ssl": True} if self.use_ssl else None
        conn = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database if include_db else None,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10,
            ssl=ssl_ctx,
            client_flag=CLIENT.MULTI_STATEMENTS,
        )
        return conn

    def test_connection(self) -> Dict[str, Any]:
        """Tests connectivity and reports server version."""
        try:
            conn = self.get_connection(include_db=False)
            with conn.cursor() as cur:
                cur.execute("SELECT VERSION() AS ver, NOW() AS ts;")
                res = cur.fetchone()
            conn.close()
            return {
                "success": True,
                "message": f"Connected to MySQL server successfully! Version: {res['ver']}",
                "server_version": res["ver"],
                "server_time": str(res["ts"]),
            }
        except Exception as e:
            logger.error(f"MySQL connection failed: {e}")
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "error": str(e),
            }

    def init_mysql_schema(self) -> Dict[str, Any]:
        """Executes database/mysql_schema.sql to build schema on MySQL server."""
        schema_path = Path(__file__).resolve().parent / "mysql_schema.sql"
        if not schema_path.exists():
            return {"success": False, "message": "mysql_schema.sql not found."}

        with open(schema_path, "r", encoding="utf-8") as f:
            sql_script = f.read()

        try:
            conn = self.get_connection(include_db=False)
            with conn.cursor() as cur:
                for statement in sql_script.split(";"):
                    stmt = statement.strip()
                    if stmt:
                        cur.execute(stmt)
            conn.commit()
            conn.close()
            logger.info("MySQL schema initialized successfully.")
            return {"success": True, "message": "MySQL schema and tables initialized successfully."}
        except Exception as e:
            logger.error(f"Failed to initialize MySQL schema: {e}")
            return {"success": False, "message": f"Schema initialization failed: {str(e)}"}

    def sync_from_sqlite(self) -> Dict[str, Any]:
        """
        Synchronizes all local SQLite records into the remote MySQL database.
        Uses INSERT ... ON DUPLICATE KEY UPDATE to make syncs safe and idempotent.
        """
        tables = [
            "users",
            "user_profiles",
            "badges",
            "levels",
            "rewards",
            "challenges",
            "waste_scans",
            "point_transactions",
            "user_badges",
            "reward_redemptions",
            "spin_history",
            "referrals",
            "challenge_participation",
            "tree_award_claims",
            "admin_audit_logs",
        ]

        summary = {}

        try:
            # 1. Connect to MySQL and ensure schema exists
            self.init_mysql_schema()
            mysql_conn = self.get_connection(include_db=True)

            with get_db_connection() as sqlite_conn:
                for table in tables:
                    # Fetch SQLite rows
                    sqlite_cur = sqlite_conn.execute(f"SELECT * FROM {table}")
                    rows = sqlite_cur.fetchall()
                    if not rows:
                        summary[table] = 0
                        continue

                    cols = [col[0] for col in sqlite_cur.description]
                    col_names = ", ".join(cols)
                    placeholders = ", ".join(["%s"] * len(cols))
                    update_clause = ", ".join([f"{c}=VALUES({c})" for c in cols if c != "id"])

                    insert_sql = f"""
                        INSERT INTO {table} ({col_names})
                        VALUES ({placeholders})
                        ON DUPLICATE KEY UPDATE {update_clause if update_clause else f'{cols[0]}={cols[0]}'}
                    """

                    with mysql_conn.cursor() as my_cur:
                        data = [tuple(r[c] for c in cols) for r in rows]
                        my_cur.executemany(insert_sql, data)

                    summary[table] = len(rows)

            mysql_conn.commit()
            mysql_conn.close()
            logger.info(f"SQLite -> MySQL sync finished successfully: {summary}")
            return {
                "success": True,
                "message": f"Synchronized {sum(summary.values())} records across {len(summary)} tables to MySQL.",
                "summary": summary,
            }
        except Exception as e:
            logger.error(f"Sync to MySQL failed: {e}")
            return {
                "success": False,
                "message": f"Sync failed: {str(e)}",
                "summary": summary,
            }


if __name__ == "__main__":
    print("Testing connection to MySQL...")
    mgr = MySQLSyncManager()
    res = mgr.test_connection()
    print(res["message"])
    if res["success"]:
        print("Initializing schema...")
        mgr.init_mysql_schema()
        print("Starting sync...")
        sync_res = mgr.sync_from_sqlite()
        print(sync_res["message"])
        print("Summary:", sync_res.get("summary"))
