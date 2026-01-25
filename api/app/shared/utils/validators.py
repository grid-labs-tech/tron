"""Shared validation utilities."""

import re
from typing import Optional


def validate_email_permissive(email: str) -> str:
    """
    Validate email format with permissive rules for self-hosted environments.

    This validator allows local/internal domains like:
    - .local, .localhost, .internal, .corp, .lan, .test

    These domains are commonly used in corporate/self-hosted environments
    but rejected by strict email validators like Pydantic's EmailStr.

    Args:
        email: Email address to validate

    Returns:
        Lowercase email if valid

    Raises:
        ValueError: If email format is invalid
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        raise ValueError("Invalid email format")
    return email.lower()


def validate_email_optional(email: Optional[str]) -> Optional[str]:
    """
    Validate optional email field.

    Args:
        email: Email address to validate or None

    Returns:
        Lowercase email if valid, None if input is None

    Raises:
        ValueError: If email format is invalid
    """
    if email is None:
        return None
    return validate_email_permissive(email)
