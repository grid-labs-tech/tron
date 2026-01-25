"""
Cryptography module for encrypting/decrypting secrets.

Uses Fernet (AES-128-CBC + HMAC) for symmetric encryption.
The encryption key is read from TRON_SECRETS_KEY environment variable.
"""

from .secrets_crypto import (
    encrypt_secret,
    decrypt_secret,
    get_or_generate_key,
    SecretsKeyNotConfiguredError,
)

from .secrets_service import (
    encrypt_secrets_in_settings,
    strip_secrets_from_settings,
    merge_secrets_for_update,
)

__all__ = [
    "encrypt_secret",
    "decrypt_secret",
    "get_or_generate_key",
    "SecretsKeyNotConfiguredError",
    "encrypt_secrets_in_settings",
    "strip_secrets_from_settings",
    "merge_secrets_for_update",
]
