"""
Unit tests for MySQL Sync Manager and Schema Parser.
"""

from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

from database.mysql_sync import MySQLSyncManager


def test_mysql_sync_manager_initialization():
    mgr = MySQLSyncManager(
        host="db.example.com",
        port=3307,
        user="eco_admin",
        password="secure_password",
        database="smart_waste_prod",
        ssl=True,
    )
    assert mgr.host == "db.example.com"
    assert mgr.port == 3307
    assert mgr.user == "eco_admin"
    assert mgr.database == "smart_waste_prod"
    assert mgr.use_ssl is True


def test_mysql_schema_file_exists():
    schema_path = Path(__file__).resolve().parent.parent / "database" / "mysql_schema.sql"
    assert schema_path.exists()
    content = schema_path.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS waste_scans" in content
    assert "ENGINE=InnoDB" in content
    assert "is_discarded" in content


@patch("pymysql.connect")
def test_test_connection_mock(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {"ver": "8.0.35-MySQL", "ts": "2026-10-25 22:00:00"}
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    mgr = MySQLSyncManager(host="localhost", user="test")
    res = mgr.test_connection()
    assert res["success"] is True
    assert "8.0.35-MySQL" in res["server_version"]
