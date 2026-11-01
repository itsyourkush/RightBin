"""
Security and Cryptography Utilities.
Provides PBKDF2-HMAC-SHA256 password hashing with salt,
constant-time comparisons, token generation, and image content hashing.
"""

from __future__ import annotations

import hashlib
import os
import secrets
from typing import Tuple


def hash_password(password: str) -> str:
    """
    Hashes a password using PBKDF2-HMAC-SHA256 with a unique 16-byte random salt.
    Returns string formatted as: 'pbkdf2:sha256:iterations$salt_hex$hash_hex'
    """
    salt = os.urandom(16)
    iterations = 100_000
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2:sha256:{iterations}${salt.hex()}${pwd_hash.hex()}"


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verifies a password against the stored hash in constant time to prevent timing attacks.
    """
    try:
        method, salt_hex, hash_hex = hashed_password.split("$")
        algorithm, iterations_str = method.split(":")[-2:]
        iterations = int(iterations_str)
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)

        calculated_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return secrets.compare_digest(calculated_hash, expected_hash)
    except Exception:
        return False


def generate_referral_code(prefix: str = "ECO", length: int = 6) -> str:
    """Generates an uppercase alphanumeric referral code."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    random_part = "".join(secrets.choice(alphabet) for _ in range(length))
    return f"{prefix}-{random_part}"


def generate_session_token() -> str:
    """Generates a secure random 32-byte URL-safe token."""
    return secrets.token_urlsafe(32)


def compute_image_hash(image_bytes: bytes) -> str:
    """Computes SHA-256 hash of image bytes for duplicate detection."""
    return hashlib.sha256(image_bytes).hexdigest()
