"""Tests for template slug and template settings helpers."""

from types import SimpleNamespace

import pytest

from app.templates.core.template_settings import (
    build_template_settings_context,
    slugify_template_name,
    uniquify_slug,
    validate_component_template_setting_values,
    validate_template_settings_schema,
)


def test_slugify_template_name():
    assert slugify_template_name("Webapp Deployment") == "webapp_deployment"
    assert slugify_template_name("  Worker HPA  ") == "worker_hpa"
    assert slugify_template_name("123 Foo") == "t_123_foo"
    assert slugify_template_name("") == "template"


def test_uniquify_slug():
    assert uniquify_slug("webapp_deployment", set()) == "webapp_deployment"
    assert (
        uniquify_slug("webapp_deployment", {"webapp_deployment"})
        == "webapp_deployment_2"
    )
    assert (
        uniquify_slug("webapp_deployment", {"webapp_deployment", "webapp_deployment_2"})
        == "webapp_deployment_3"
    )


def test_validate_template_settings_schema_success():
    result = validate_template_settings_schema(
        [
            {"name": "enable_pdb", "description": "PDB", "type": "boolean"},
            {"name": "region", "type": "string"},
        ]
    )
    assert len(result) == 2
    assert result[0]["name"] == "enable_pdb"


def test_validate_template_settings_schema_duplicate_name():
    with pytest.raises(ValueError, match="Duplicate"):
        validate_template_settings_schema(
            [
                {"name": "region", "type": "string"},
                {"name": "region", "type": "boolean"},
            ]
        )


def test_validate_template_settings_schema_invalid_name():
    with pytest.raises(ValueError, match="valid identifier"):
        validate_template_settings_schema([{"name": "1region", "type": "string"}])


def test_validate_template_settings_schema_invalid_type():
    with pytest.raises(ValueError, match="invalid type"):
        validate_template_settings_schema([{"name": "region", "type": "number"}])


def test_validate_component_template_setting_values_unknown_slug():
    templates = [
        SimpleNamespace(
            slug="webapp_deployment",
            template_settings=[{"name": "enable_pdb", "type": "boolean"}],
        )
    ]
    with pytest.raises(ValueError, match="Unknown template slug"):
        validate_component_template_setting_values(
            {"other_slug": {"enable_pdb": True}}, templates
        )


def test_validate_component_template_setting_values_type_mismatch():
    templates = [
        SimpleNamespace(
            slug="webapp_deployment",
            template_settings=[{"name": "enable_pdb", "type": "boolean"}],
        )
    ]
    with pytest.raises(ValueError, match="must be a boolean"):
        validate_component_template_setting_values(
            {"webapp_deployment": {"enable_pdb": "yes"}}, templates
        )


def test_validate_component_template_setting_values_same_name_on_two_templates():
    templates = [
        SimpleNamespace(
            slug="webapp_deployment",
            template_settings=[{"name": "region", "type": "string"}],
        ),
        SimpleNamespace(
            slug="webapp_service",
            template_settings=[{"name": "region", "type": "string"}],
        ),
    ]
    validate_component_template_setting_values(
        {
            "webapp_deployment": {"region": "us-east-1"},
            "webapp_service": {"region": "eu-west-1"},
        },
        templates,
    )


def test_build_template_settings_context_filters_and_omits_missing():
    templates = [
        SimpleNamespace(
            slug="webapp_deployment",
            template_settings=[
                {"name": "enable_pdb", "type": "boolean"},
                {"name": "region", "type": "string"},
            ],
        ),
        SimpleNamespace(
            slug="webapp_service",
            template_settings=[{"name": "region", "type": "string"}],
        ),
        SimpleNamespace(slug="webapp_hpa", template_settings=[]),
    ]
    context = build_template_settings_context(
        templates,
        {
            "webapp_deployment": {"enable_pdb": True, "unknown": "x"},
            "deleted_template": {"foo": "bar"},
        },
    )
    assert context["webapp_deployment"]["settings"] == {"enable_pdb": True}
    assert context["webapp_service"]["settings"] == {}
    assert "webapp_hpa" not in context
    assert "deleted_template" not in context
