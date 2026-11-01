"""
Pytest fixtures and test setup.
Uses temporary / in-memory SQLite database to keep tests completely isolated and fast.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Generator
import pytest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set Matplotlib cache dir to /tmp to avoid home directory permission issues
os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib_cache"

from database.connection import get_db_connection
from database.init_db import init_database
from repositories.user_repository import UserRepository
from repositories.scan_repository import ScanRepository
from repositories.points_repository import PointsRepository
from repositories.badge_repository import BadgeRepository
from repositories.reward_repository import RewardRepository
from repositories.challenge_repository import ChallengeRepository
from repositories.referral_repository import ReferralRepository
from utils.security import hash_password


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    """Creates an isolated temporary SQLite database initialized with schema."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        init_database(path)
        yield path
    finally:
        if os.path.exists(path):
            os.remove(path)


@pytest.fixture
def test_user(temp_db: str) -> dict:
    """Creates a regular test user."""
    repo = UserRepository(temp_db)
    pwd_hash = hash_password("TestSecret123!")
    user = repo.create_user("Alice Green", "alice@example.com", pwd_hash, role="user", display_name="AliceEco")
    return user


@pytest.fixture
def test_admin(temp_db: str) -> dict:
    """Creates an admin test user."""
    repo = UserRepository(temp_db)
    pwd_hash = hash_password("AdminSecret123!")
    user = repo.create_user("Admin User", "superadmin@example.com", pwd_hash, role="admin", display_name="SuperAdmin")
    return user
