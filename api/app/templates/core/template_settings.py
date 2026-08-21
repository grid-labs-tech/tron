"""Helpers for template slugs and template settings schema/values."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

SETTING_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SLUG_RE = re.compile(r"^[a-z][a-z0-9_]*$")
ALLOWED_SETTING_TYPES = frozenset({"boolean", "string"})

SETTING_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SLUG_RE = re.compile(r"^[a-z][a-z0-9_]*$")
ALLOWED_SETTING_TYPES = frozenset({"boolean", "string"})


def slugify_template_name(name: str) -> str:
    """Turn a display name into a lower-snake-case slug."""
    slug = re.sub(r"[^a-z0-9]+", "_", (name or "").strip().lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    if not slug:
        slug = "template"
    if not slug[0].isalpha():
        slug = f"t_{slug}"
    return slug


def uniquify_slug(base: str, existing: set[str]) -> str:
    """Return base, or base_2 / base_3 / ... if already taken."""
    if base not in existing:
        return base
    i = 2
    while f"{base}_{i}" in existing:
        i += 1
    return f"{base}_{i}"


def validate_template_settings_schema(settings: Sequence[Any] | None) -> list[dict]:
    """
    Validate template setting definitions.

    Names must be unique within the template and match SETTING_NAME_RE.
    Types must be boolean or string.
    """
    if settings is None:
        return []
    if not isinstance(settings, list):
        raise ValueError("template_settings must be a list")

    seen: set[str] = set()
    normalized: list[dict] = []
    for i, item in enumerate(settings):
        if hasattr(item, "model_dump"):
            item = item.model_dump()
        if not isinstance(item, dict):
            raise ValueError(f"Template setting at position {i + 1} must be an object")

        name = (item.get("name") or "").strip()
        if not name:
            raise ValueError(f"Template setting at position {i + 1} is missing a name")
        if not SETTING_NAME_RE.match(name):
            raise ValueError(
                f"Template setting name '{name}' must be a valid identifier "
                "(letters, digits, underscore; cannot start with a digit)"
            )
        if name in seen:
            raise ValueError(
                f"Duplicate template setting name '{name}'. "
                "Names must be unique within a template."
            )
        seen.add(name)

        setting_type = item.get("type")
        if setting_type not in ALLOWED_SETTING_TYPES:
            raise ValueError(
                f"Template setting '{name}' has invalid type '{setting_type}'. "
                "Allowed types: boolean, string"
            )

        description = item.get("description")
        if description is not None:
            description = str(description)

        normalized.append(
            {
                "name": name,
                "description": description,
                "type": setting_type,
            }
        )
    return normalized


def _definition_map(definitions: Sequence[Any]) -> dict[str, str]:
    """Map setting name -> type from a list of dicts or objects."""
    result: dict[str, str] = {}
    for item in definitions or []:
        if hasattr(item, "name"):
            result[item.name] = getattr(item, "type", None) or (
                item.type.value if hasattr(item.type, "value") else str(item.type)
            )
        elif isinstance(item, dict):
            name = item.get("name")
            if name:
                result[name] = item.get("type")
    return result


def validate_component_template_setting_values(
    values: Mapping[str, Mapping[str, Any]] | None,
    templates: Iterable[Any],
) -> None:
    """
    Validate component-stored template_settings against enabled template schema.

    Unknown slugs or setting names are rejected. Values must match definition types.
    """
    if not values:
        return
    if not isinstance(values, dict):
        raise ValueError("template_settings must be an object keyed by template slug")

    schema_by_slug: dict[str, dict[str, str]] = {}
    for template in templates:
        slug = getattr(template, "slug", None)
        defs = getattr(template, "template_settings", None) or []
        if slug and defs:
            schema_by_slug[slug] = _definition_map(defs)

    for slug, settings in values.items():
        if slug not in schema_by_slug:
            raise ValueError(
                f"Unknown template slug '{slug}' in template settings. "
                "Use a slug from an enabled template that defines settings."
            )
        if not isinstance(settings, dict):
            raise ValueError(
                f"Template settings for '{slug}' must be an object of name -> value"
            )
        type_by_name = schema_by_slug[slug]
        for name, value in settings.items():
            if name not in type_by_name:
                raise ValueError(
                    f"Unknown template setting '{name}' for template '{slug}'"
                )
            expected = type_by_name[name]
            if expected == "boolean" and not isinstance(value, bool):
                raise ValueError(f"Template setting '{slug}.{name}' must be a boolean")
            if expected == "string" and not isinstance(value, str):
                raise ValueError(f"Template setting '{slug}.{name}' must be a string")


def validate_component_template_settings_for_org(
    db,
    organization_id: int,
    component_type: str,
    values: Mapping[str, Mapping[str, Any]] | None,
) -> None:
    """Load enabled templates for the org/type and validate stored values."""
    from app.templates.infra.component_template_config_repository import (
        ComponentTemplateConfigRepository,
    )

    templates = ComponentTemplateConfigRepository(db).find_templates_for_component_type(
        component_type, organization_id=organization_id
    )
    validate_component_template_setting_values(values, templates)


def build_template_settings_context(
    templates: Iterable[Any],
    stored_values: Mapping[str, Mapping[str, Any]] | None,
) -> dict[str, dict[str, dict[str, Any]]]:
    """
    Build Jinja context: { slug: { "settings": { name: value } } }.

    Only enabled templates that define settings are included. Missing values omitted.
    """
    stored = stored_values or {}
    context: dict[str, dict[str, dict[str, Any]]] = {}
    for template in templates:
        slug = getattr(template, "slug", None)
        defs = getattr(template, "template_settings", None) or []
        if not slug or not defs:
            continue
        defined_names = set(_definition_map(defs).keys())
        values = stored.get(slug) or {}
        if not isinstance(values, dict):
            values = {}
        filtered = {name: values[name] for name in defined_names if name in values}
        context[slug] = {"settings": filtered}
    return context
