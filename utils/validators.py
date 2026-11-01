"""
Input Validation Utilities.
Ensures clean, robust validation for registration, login, and waste image uploads.
"""

from __future__ import annotations

import io
import re
from typing import Tuple
from PIL import Image

from config import config

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_email(email: str) -> Tuple[bool, str]:
    """Validates user email format."""
    if not email or not isinstance(email, str):
        return False, "Email address cannot be empty."
    clean_email = email.strip()
    if len(clean_email) > 254:
        return False, "Email address is too long."
    if not EMAIL_REGEX.match(clean_email):
        return False, "Please provide a valid email address (e.g., student@university.edu)."
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """Validates user password strength (minimum 8 characters)."""
    if not password or not isinstance(password, str):
        return False, "Password cannot be empty."
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    return True, ""


def validate_name(name: str) -> Tuple[bool, str]:
    """Validates user name."""
    if not name or not isinstance(name, str):
        return False, "Name cannot be empty."
    clean_name = name.strip()
    if len(clean_name) < 2:
        return False, "Name must be at least 2 characters long."
    if len(clean_name) > 60:
        return False, "Name cannot exceed 60 characters."
    return True, ""


def validate_image_file(file_name: str, file_size_bytes: int, file_bytes: bytes) -> Tuple[bool, str]:
    """
    Validates file extension, size limit, and genuine decodability via Pillow.
    Returns (is_valid, error_message).
    """
    if not file_name:
        return False, "No file provided."

    # Extension check
    ext = file_name.split(".")[-1].lower() if "." in file_name else ""
    if ext not in config.allowed_extensions:
        return False, f"Unsupported file extension '.{ext}'. Allowed: {', '.join(config.allowed_extensions)}."

    # Size check
    if file_size_bytes > config.max_image_size_bytes:
        max_mb = config.max_image_size_bytes / (1024 * 1024)
        return False, f"File size exceeds {max_mb:.0f} MB limit."

    if len(file_bytes) == 0:
        return False, "Uploaded image file is empty."

    # Integrity & decode check using Pillow
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            img.verify()
        # Re-open for format check since verify() consumes the stream
        with Image.open(io.BytesIO(file_bytes)) as img:
            width, height = img.size
            if width < 32 or height < 32:
                return False, f"Image dimensions ({width}x{height}) are too small for waste classification."
    except Exception as e:
        return False, f"Corrupted or invalid image file: {str(e)}"

    return True, ""
