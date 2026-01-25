"""
Cryptography utilities for encrypting/decrypting application secrets.

Uses Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256).
This provides authenticated encryption - any tampering will be detected.

Security notes:
- The TRON_SECRETS_KEY must be kept secure
- Losing the key means losing access to all encrypted secrets
- Key rotation requires re-encrypting all secrets
"""

import os
import base64
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken


class SecretsKeyNotConfiguredError(Exception):
    """Raised when TRON_SECRETS_KEY is not configured."""

    def __init__(self):
        super().__init__(
            "TRON_SECRETS_KEY environment variable is not configured. "
            "Generate a key using: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )


def get_or_generate_key() -> str:
    """
    Get the encryption key from environment or generate a new one.

    For production, TRON_SECRETS_KEY should be set.
    For development, a key will be auto-generated (not recommended for production).

    Returns:
        The Fernet key as a string.
    """
    key = os.environ.get("TRON_SECRETS_KEY")

    if key:
        return key

    # In development, we can auto-generate a key
    # This is stored in memory only - secrets won't persist across restarts
    # without a configured key
    env = os.environ.get("ENVIRONMENT", "development")
    if env == "development":
        # Generate and cache the key for this session
        if not hasattr(get_or_generate_key, "_dev_key"):
            get_or_generate_key._dev_key = Fernet.generate_key().decode()
            print(
                "WARNING: Using auto-generated secrets key. "
                "Set TRON_SECRETS_KEY for persistence."
            )
        return get_or_generate_key._dev_key

    raise SecretsKeyNotConfiguredError()


def _get_fernet() -> Fernet:
    """Get a Fernet instance with the configured key."""
    key = get_or_generate_key()
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_secret(plaintext: str) -> str:
    """
    Encrypt a secret value.

    Args:
        plaintext: The secret value to encrypt.

    Returns:
        The encrypted value as a base64-encoded string.

    Raises:
        SecretsKeyNotConfiguredError: If TRON_SECRETS_KEY is not set in production.
    """
    if not plaintext:
        return ""

    fernet = _get_fernet()
    encrypted = fernet.encrypt(plaintext.encode("utf-8"))
    return base64.urlsafe_b64encode(encrypted).decode("utf-8")


def decrypt_secret(ciphertext: str) -> str:
    """
    Decrypt a secret value.

    Args:
        ciphertext: The encrypted value (base64-encoded).

    Returns:
        The decrypted plaintext value.

    Raises:
        SecretsKeyNotConfiguredError: If TRON_SECRETS_KEY is not set in production.
        InvalidToken: If the ciphertext is invalid or was encrypted with a different key.
    """
    if not ciphertext:
        return ""

    fernet = _get_fernet()
    encrypted = base64.urlsafe_b64decode(ciphertext.encode("utf-8"))
    decrypted = fernet.decrypt(encrypted)
    return decrypted.decode("utf-8")


def mask_secret_value(value: str, show_chars: int = 4) -> str:
    """
    Mask a secret value for display purposes.

    Args:
        value: The secret value to mask.
        show_chars: Number of characters to show at the end.

    Returns:
        Masked string like "********abcd"
    """
    if not value:
        return ""

    if len(value) <= show_chars:
        return "*" * len(value)

    return "*" * (len(value) - show_chars) + value[-show_chars:]
