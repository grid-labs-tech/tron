"""
Service functions for handling secrets in application settings.

This module provides functions to encrypt secrets when saving to database
and to strip secret values from API responses.
"""

from typing import Dict, Any, List
from .secrets_crypto import encrypt_secret


def encrypt_secrets_in_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Encrypt all secret values in the settings dict.

    This should be called before saving settings to the database.

    Args:
        settings: The settings dict containing a 'secrets' list.

    Returns:
        A new settings dict with encrypted secret values.
    """
    if not settings:
        return settings

    # Make a copy to avoid modifying the original
    import copy

    encrypted_settings = copy.deepcopy(settings)

    if "secrets" in encrypted_settings and encrypted_settings["secrets"]:
        encrypted_secrets = []
        for secret in encrypted_settings["secrets"]:
            encrypted_secrets.append(
                {
                    "key": secret.get("key", ""),
                    "value": encrypt_secret(secret.get("value", "")),
                }
            )
        encrypted_settings["secrets"] = encrypted_secrets

    return encrypted_settings


def strip_secrets_from_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove secret values from settings for API responses.

    Secret keys are preserved but values are replaced with a placeholder.
    This ensures secrets are never exposed via the API.

    Args:
        settings: The settings dict containing a 'secrets' list.

    Returns:
        A new settings dict with secret values stripped.
    """
    if not settings:
        return settings

    # Make a copy to avoid modifying the original
    import copy

    stripped_settings = copy.deepcopy(settings)

    if "secrets" in stripped_settings and stripped_settings["secrets"]:
        stripped_secrets = []
        for secret in stripped_settings["secrets"]:
            stripped_secrets.append(
                {
                    "key": secret.get("key", ""),
                    "value": "********",  # Never expose actual values
                }
            )
        stripped_settings["secrets"] = stripped_secrets

    return stripped_settings


def merge_secrets_for_update(
    new_secrets: List[Dict[str, str]],
    existing_secrets: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    """
    Merge new secrets with existing ones for updates.

    If a new secret has value "********", preserve the existing encrypted value.
    This allows updating other settings without re-entering all secret values.

    Args:
        new_secrets: List of secrets from the update request.
        existing_secrets: List of existing encrypted secrets from the database.

    Returns:
        List of secrets with proper encryption.
    """
    if not new_secrets:
        return []

    # Build a map of existing secrets by key
    existing_map = {s.get("key"): s.get("value") for s in (existing_secrets or [])}

    merged_secrets = []
    for secret in new_secrets:
        key = secret.get("key", "")
        value = secret.get("value", "")

        if value == "********" and key in existing_map:
            # Preserve existing encrypted value
            merged_secrets.append({"key": key, "value": existing_map[key]})
        else:
            # Encrypt new value
            merged_secrets.append({"key": key, "value": encrypt_secret(value)})

    return merged_secrets
