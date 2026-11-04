"""
Unit tests for Authentication Service.
"""

import pytest
from services.auth_service import AuthService
from repositories.user_repository import UserRepository


def test_register_and_authenticate(temp_db):
    auth = AuthService(temp_db)

    # Valid registration
    ok, msg, user = auth.register_user(
        name="Bob Smith",
        email="bob@example.com",
        password="ValidPassword123!",
        display_name="BobEco",
    )
    assert ok is True
    assert user is not None
    assert user["email"] == "bob@example.com"

    # Authenticate with correct credentials
    ok, msg, profile = auth.authenticate("bob@example.com", "ValidPassword123!")
    assert ok is True
    assert profile["email"] == "bob@example.com"
    assert profile["display_name"] == "BobEco"

    # Authenticate with wrong password
    ok, msg, profile = auth.authenticate("bob@example.com", "WrongPassword!")
    assert ok is False
    assert profile is None

    # Authenticate with non-existent user
    ok, msg, profile = auth.authenticate("ghost@example.com", "AnyPassword!")
    assert ok is False


def test_duplicate_registration_prevented(temp_db, test_user):
    auth = AuthService(temp_db)
    ok, msg, user = auth.register_user(
        name="Alice Clone",
        email="alice@example.com",  # Already exists from fixture
        password="AnotherPassword123!",
    )
    assert ok is False
    assert "already exists" in msg.lower()


def test_invalid_input_validation(temp_db):
    auth = AuthService(temp_db)

    # Invalid email
    ok, msg, _ = auth.register_user("Shorty", "not-an-email", "Password123!")
    assert ok is False

    # Short password (< 8 chars)
    ok, msg, _ = auth.register_user("Shorty", "shorty@example.com", "123")
    assert ok is False

    # Empty name
    ok, msg, _ = auth.register_user("", "shorty@example.com", "Password123!")
    assert ok is False


def test_password_change(temp_db, test_user):
    auth = AuthService(temp_db)
    uid = test_user["id"]

    # Wrong current password
    ok, msg = auth.change_password(uid, "WrongOldPass!", "BrandNewPassword123!")
    assert ok is False

    # Correct current password
    ok, msg = auth.change_password(uid, "TestSecret123!", "BrandNewPassword123!")
    assert ok is True

    # Authenticate with new password
    ok, msg, _ = auth.authenticate(test_user["email"], "BrandNewPassword123!")
    assert ok is True


def test_deactivated_user_cannot_login(temp_db, test_user):
    auth = AuthService(temp_db)
    repo = UserRepository(temp_db)

    # Deactivate
    repo.set_user_active(test_user["id"], False)

    ok, msg, profile = auth.authenticate(test_user["email"], "TestSecret123!")
    assert ok is False
    assert "deactivated" in msg.lower()


def test_reset_password_by_email(temp_db, test_user):
    auth = AuthService(temp_db)
    email = test_user["email"]

    # Non-existent email
    ok, msg = auth.reset_password_by_email("unknown@nowhere.com", "NewValidPass123!", "NewValidPass123!")
    assert ok is False
    assert "no account found" in msg.lower()

    # Mismatched confirmation password
    ok, msg = auth.reset_password_by_email(email, "NewValidPass123!", "DifferentPass123!")
    assert ok is False
    assert "do not match" in msg.lower()

    # Too short password
    ok, msg = auth.reset_password_by_email(email, "short", "short")
    assert ok is False

    # Successful reset
    ok, msg = auth.reset_password_by_email(email, "NewSecurePassword123!", "NewSecurePassword123!")
    assert ok is True
    assert "successfully" in msg.lower()

    # Verify old password no longer works
    ok, _, _ = auth.authenticate(email, "TestSecret123!")
    assert ok is False

    # Verify new password works
    ok, _, profile = auth.authenticate(email, "NewSecurePassword123!")
    assert ok is True
    assert profile["email"] == email
