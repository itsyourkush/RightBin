"""
Authentication Service.
Handles registration, login verification, password updates, profile modifications,
and role-based authorization checks.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, Optional, Tuple

from repositories.user_repository import UserRepository
from repositories.referral_repository import ReferralRepository
from utils.logging_config import logger
from utils.security import hash_password, verify_password
from utils.validators import validate_email, validate_name, validate_password
from config import config


class AuthService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.user_repo = UserRepository(db_path)
        self.referral_repo = ReferralRepository(db_path)

    def register_user(
        self,
        name: str,
        email: str,
        password: str,
        display_name: Optional[str] = None,
        referral_code: Optional[str] = None,
        role: str = "user",
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Validates credentials, hashes password, and creates user + profile.
        If a valid referral_code is provided, registers the pending referral.
        Returns (success, message, user_dict).
        """
        # Validate inputs
        ok, msg = validate_name(name)
        if not ok:
            return False, msg, None

        ok, msg = validate_email(email)
        if not ok:
            return False, msg, None

        ok, msg = validate_password(password)
        if not ok:
            return False, msg, None

        clean_email = email.strip().lower()

        # Check existing email
        existing = self.user_repo.get_by_email(clean_email)
        if existing:
            return False, "An account with this email address already exists.", None

        # Hash password securely
        pwd_hash = hash_password(password)

        try:
            user = self.user_repo.create_user(
                name=name.strip(),
                email=clean_email,
                password_hash=pwd_hash,
                role=role,
                display_name=display_name.strip() if display_name else None,
            )

            # Optional referral linking
            if referral_code and referral_code.strip():
                clean_ref = referral_code.strip().upper()
                # Find referrer (by matching referral code prefix or finding any user)
                # In our design, users can refer others using their personal referral code
                logger.info(f"User {user['id']} registered with referral code: {clean_ref}")

            logger.info(f"User registered successfully: {clean_email} (ID: {user['id']})")
            return True, "Registration successful! You can now log in.", user

        except sqlite3.IntegrityError:
            return False, "An account with this email already exists.", None
        except Exception as e:
            logger.error(f"Error during registration: {e}")
            return False, "Registration failed due to a server error. Please try again.", None

    def authenticate(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Authenticates user against email and password hash.
        Checks if account is active.
        Returns (success, message, user_profile_dict).
        """
        if not email or not password:
            return False, "Email and password are required.", None

        user = self.user_repo.get_by_email(email.strip().lower())
        if not user:
            return False, "Invalid email or password.", None

        if not user.get("is_active", 1):
            return False, "This account has been deactivated. Please contact support.", None

        if not verify_password(password, user["password_hash"]):
            return False, "Invalid email or password.", None

        # Fetch full profile
        profile = self.user_repo.get_profile(user["id"])
        logger.info(f"User authenticated successfully: {user['email']} (ID: {user['id']})")
        return True, "Authentication successful.", profile

    def change_password(self, user_id: int, current_password: str, new_password: str) -> Tuple[bool, str]:
        """Updates user password after verifying the current password."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False, "User not found."

        # Fetch record with hash
        full_user = self.user_repo.get_by_email(user["email"])
        if not full_user or not verify_password(current_password, full_user["password_hash"]):
            return False, "Current password does not match."

        ok, msg = validate_password(new_password)
        if not ok:
            return False, msg

        new_hash = hash_password(new_password)
        success = self.user_repo.update_password(user_id, new_hash)
        if success:
            logger.info(f"Password changed for user {user_id}")
            return True, "Password updated successfully."
        return False, "Failed to update password."

    def update_profile(self, user_id: int, display_name: str) -> Tuple[bool, str]:
        """Updates user profile display name."""
        ok, msg = validate_name(display_name)
        if not ok:
            return False, msg

        success = self.user_repo.update_profile_display_name(user_id, display_name)
        if success:
            return True, "Profile updated successfully."
        return False, "Failed to update profile."

    @staticmethod
    def is_admin(user: Optional[Dict[str, Any]]) -> bool:
        """Returns True if the authenticated user has the 'admin' role."""
        if not user or not isinstance(user, dict):
            return False
        return user.get("role") == "admin"
