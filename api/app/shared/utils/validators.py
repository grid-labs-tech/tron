"""Shared validation utilities."""

import re
from typing import Optional, List, Any


class InvalidEnvVarError(Exception):
    """Raised when environment variable validation fails."""

    pass


class InvalidSecretError(Exception):
    """Raised when secret validation fails."""

    pass


def validate_env_vars(envs: List[Any]) -> None:
    """
    Validate environment variables have non-empty keys and values.

    Args:
        envs: List of environment variable objects with key and value attributes

    Raises:
        InvalidEnvVarError: If any env var has empty key or value
    """
    for i, env in enumerate(envs):
        key = getattr(env, "key", None) if hasattr(env, "key") else env.get("key")
        value = (
            getattr(env, "value", None) if hasattr(env, "value") else env.get("value")
        )

        if not key or not str(key).strip():
            raise InvalidEnvVarError(
                f"Environment variable at position {i + 1} has an empty key. "
                "All environment variables must have a non-empty key."
            )

        # Allow "0" and "false" as valid values, but not empty strings or whitespace-only
        if value is None or (isinstance(value, str) and not value.strip()):
            raise InvalidEnvVarError(
                f"Environment variable '{key}' has an empty value. "
                "All environment variables must have a non-empty value."
            )


def validate_secrets(secrets: List[Any]) -> None:
    """
    Validate secrets have non-empty keys and values.

    Args:
        secrets: List of secret objects with key and value attributes

    Raises:
        InvalidSecretError: If any secret has empty key or value
    """
    for i, secret in enumerate(secrets):
        key = (
            getattr(secret, "key", None)
            if hasattr(secret, "key")
            else secret.get("key")
        )
        value = (
            getattr(secret, "value", None)
            if hasattr(secret, "value")
            else secret.get("value")
        )

        if not key or not str(key).strip():
            raise InvalidSecretError(
                f"Secret at position {i + 1} has an empty key. "
                "All secrets must have a non-empty key."
            )

        # Secrets must always have a non-empty value
        if value is None or (isinstance(value, str) and not value.strip()):
            raise InvalidSecretError(
                f"Secret '{key}' has an empty value. "
                "All secrets must have a non-empty value."
            )


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
