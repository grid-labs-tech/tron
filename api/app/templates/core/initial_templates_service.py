"""
Service to seed initial Kubernetes templates and component_template_config for an organization.
Used when creating a new organization (create_organization_with_defaults) and optionally by scripts.
Does not commit; caller is responsible for commit.
"""

from pathlib import Path
from typing import List
from uuid import uuid4

from sqlalchemy.orm import Session

from app.templates.core.template_settings import slugify_template_name
from app.templates.infra.component_template_config_model import (
    ComponentTemplateConfig as ComponentTemplateConfigModel,
)
from app.templates.infra.template_model import Template as TemplateModel


def _get_templates_base_path() -> Path:
    """Return base path to k8s templates (api/app/k8s/templates)."""
    return Path(__file__).resolve().parent.parent.parent / "k8s" / "templates"


def _get_variables_schema() -> str:
    """Return the JSON schema of variables available for templates."""
    return """{
  "application": {
    "component_name": "string",
    "application_name": "string",
    "environment": "string",
    "image": "string",
    "version": "string",
    "workload": "string",
    "settings": {
      "cpu": "number",
      "memory": "number",
      "cpu_scaling_threshold": "number",
      "memory_scaling_threshold": "number",
      "autoscaling": {
        "min": "number",
        "max": "number"
      },
      "custom_metrics": {
        "enabled": "boolean",
        "port": "number",
        "path": "string"
      },
      "exposure": {
        "type": "string",
        "port": "number",
        "visibility": "string"
      },
      "envs": [
        {
          "key": "string",
          "value": "string"
        }
      ],
      "secrets": [
        {
          "key": "string",
          "value": "string"
        }
      ],
      "healthcheck": {
        "protocol": "string",
        "path": "string",
        "port": "number",
        "failure_threshold": "number",
        "initial_interval": "number",
        "interval": "number",
        "timeout": "number"
      },
      "schedule": "string",
      "command": "array"
    },
    "template": {
      "[slug]": {
        "settings": {
          "[name]": "boolean | string"
        }
      }
    }
  },
  "environment": {
    "disable_workload": "boolean"
  }
}"""


def _build_templates_data(base_path: Path) -> List[dict]:
    """Build list of template definitions (name, description, category, file_path, render_order)."""
    webapp_dir = base_path / "webapp"
    cron_dir = base_path / "cron"
    worker_dir = base_path / "worker"
    return [
        {
            "name": "Webapp Deployment",
            "description": "Deployment template for webapp components",
            "category": "webapp",
            "file_path": webapp_dir / "deployment.yaml.j2",
            "render_order": 1,
        },
        {
            "name": "Webapp Service",
            "description": "Service template for webapp components",
            "category": "webapp",
            "file_path": webapp_dir / "service.yaml.j2",
            "render_order": 2,
        },
        {
            "name": "Webapp HPA",
            "description": "HorizontalPodAutoscaler template for webapp components",
            "category": "webapp",
            "file_path": webapp_dir / "hpa.yaml.j2",
            "render_order": 3,
        },
        {
            "name": "Webapp HTTPRoute",
            "description": "HTTPRoute template for webapp components",
            "category": "webapp",
            "file_path": webapp_dir / "httproute.yaml.j2",
            "render_order": 4,
        },
        {
            "name": "Webapp TCPRoute",
            "description": "TCPRoute template for webapp components",
            "category": "webapp",
            "file_path": webapp_dir / "tcproute.yaml.j2",
            "render_order": 5,
        },
        {
            "name": "Webapp UDPRoute",
            "description": "UDPRoute template for webapp components",
            "category": "webapp",
            "file_path": webapp_dir / "udproute.yaml.j2",
            "render_order": 6,
        },
        {
            "name": "Cron CronJob",
            "description": "CronJob template for cron components",
            "category": "cron",
            "file_path": cron_dir / "cron.yaml.j2",
            "render_order": 1,
        },
        {
            "name": "Worker Deployment",
            "description": "Deployment template for worker components",
            "category": "worker",
            "file_path": worker_dir / "deployment.yaml.j2",
            "render_order": 1,
        },
        {
            "name": "Worker HPA",
            "description": "HorizontalPodAutoscaler template for worker components",
            "category": "worker",
            "file_path": worker_dir / "hpa.yaml.j2",
            "render_order": 2,
        },
    ]


def seed_templates_for_organization(
    db: Session, organization_id: int
) -> List[TemplateModel]:
    """
    Seed initial templates and component_template_config for the given organization.
    Adds to session and flushes; does NOT commit. Caller must commit.

    Args:
        db: Database session (will add templates and configs, flush, but not commit)
        organization_id: Organization ID to associate templates with

    Returns:
        List of created Template model instances (new ones only; existing are skipped but not returned)
    """
    base_path = _get_templates_base_path()
    templates_data = _build_templates_data(base_path)
    variables_schema = _get_variables_schema()
    created: List[TemplateModel] = []

    for template_data in templates_data:
        # Check if template already exists (by name, category, organization)
        existing_template = (
            db.query(TemplateModel)
            .filter(
                TemplateModel.name == template_data["name"],
                TemplateModel.category == template_data["category"],
                TemplateModel.organization_id == organization_id,
            )
            .first()
        )

        if existing_template:
            # Ensure component_template_config exists for this template
            existing_config = (
                db.query(ComponentTemplateConfigModel)
                .filter(
                    ComponentTemplateConfigModel.template_id == existing_template.id,
                    ComponentTemplateConfigModel.component_type
                    == template_data["category"],
                    ComponentTemplateConfigModel.organization_id == organization_id,
                )
                .first()
            )
            if not existing_config:
                config = ComponentTemplateConfigModel(
                    uuid=uuid4(),
                    component_type=template_data["category"],
                    template_id=existing_template.id,
                    render_order=template_data["render_order"],
                    enabled="true",
                    organization_id=organization_id,
                )
                db.add(config)
                db.flush()
            elif existing_config.render_order != template_data["render_order"]:
                existing_config.render_order = template_data["render_order"]
            continue

        file_path = template_data["file_path"]
        if not file_path.exists():
            continue

        content = file_path.read_text(encoding="utf-8")
        new_template = TemplateModel(
            uuid=uuid4(),
            name=template_data["name"],
            slug=slugify_template_name(template_data["name"]),
            description=template_data["description"],
            category=template_data["category"],
            content=content,
            variables_schema=variables_schema,
            template_settings=[],
            organization_id=organization_id,
        )
        db.add(new_template)
        db.flush()

        config = ComponentTemplateConfigModel(
            uuid=uuid4(),
            component_type=template_data["category"],
            template_id=new_template.id,
            render_order=template_data["render_order"],
            enabled="true",
            organization_id=organization_id,
        )
        db.add(config)
        db.flush()
        created.append(new_template)

    return created
