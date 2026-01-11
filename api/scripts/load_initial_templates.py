#!/usr/bin/env python3
"""
Script to load initial templates and component_template_config configurations.
This script should be executed after migrations to populate the database with initial data.
"""

import os
import sys
from pathlib import Path

# Add root directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.shared.database.database import SessionLocal
from uuid import uuid4

from app.templates.infra.template_model import Template as TemplateModel
from app.templates.infra.component_template_config_model import ComponentTemplateConfig as ComponentTemplateConfigModel


def read_template_file(file_path: Path) -> str:
    """Read the content of a template file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def get_variables_schema() -> str:
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
    }
  },
  "environment": {
    "disable_workload": "boolean"
  }
}"""


def load_templates(db: Session):
    """Load initial templates into the templates table."""
    templates_base_dir = Path(__file__).parent.parent / "app" / "k8s" / "templates"
    webapp_dir = templates_base_dir / "webapp"
    cron_dir = templates_base_dir / "cron"
    worker_dir = templates_base_dir / "worker"

    templates_data = [
        # Templates Webapp
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
        # Templates Cron
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

    created_templates = []

    for template_data in templates_data:
        # Check if template already exists (by name and category)
        existing_template = (
            db.query(TemplateModel)
            .filter(
                TemplateModel.name == template_data["name"],
                TemplateModel.category == template_data["category"]
            )
            .first()
        )

        if existing_template:
            print(f"Template '{template_data['name']}' already exists, checking configuration...")
            # Check if component_template_config already exists for this template
            # The unique constraint is by component_type and template_id
            existing_config = (
                db.query(ComponentTemplateConfigModel)
                .filter(
                    ComponentTemplateConfigModel.template_id == existing_template.id,
                    ComponentTemplateConfigModel.component_type == template_data["category"]
                )
                .first()
            )

            if not existing_config:
                # Create configuration if it doesn't exist
                try:
                    config = ComponentTemplateConfigModel(
                        uuid=uuid4(),
                        component_type=template_data["category"],
                        template_id=existing_template.id,
                        render_order=template_data["render_order"],
                        enabled="true",
                    )
                    db.add(config)
                    db.flush()
                    print(f"  ✓ Configuration created for template '{template_data['name']}'")
                except Exception as e:
                    print(f"  ⚠ Error creating configuration: {e}")
            else:
                # Update render_order if necessary
                if existing_config.render_order != template_data["render_order"]:
                    existing_config.render_order = template_data["render_order"]
                    print(f"  ✓ Render order updated for template '{template_data['name']}'")
                else:
                    print(f"  ✓ Configuration already exists for template '{template_data['name']}'")

            created_templates.append(existing_template)
            continue

        # Read file content
        if not template_data["file_path"].exists():
            print(f"WARNING: File not found: {template_data['file_path']}")
            continue

        content = read_template_file(template_data["file_path"])

        # Create the template
        new_template = TemplateModel(
            uuid=uuid4(),
            name=template_data["name"],
            description=template_data["description"],
            category=template_data["category"],
            content=content,
            variables_schema=get_variables_schema(),
        )

        db.add(new_template)
        db.flush()  # Flush to get the ID

        # Create component_template_config configuration
        config = ComponentTemplateConfigModel(
            uuid=uuid4(),
            component_type=template_data["category"],
            template_id=new_template.id,
            render_order=template_data["render_order"],
            enabled="true",
        )

        db.add(config)
        created_templates.append(new_template)
        print(f"✓ Template '{template_data['name']}' created successfully")

    db.commit()
    return created_templates


def main():
    """Main function."""
    print("🚀 Loading initial templates...")

    db: Session = SessionLocal()
    try:
        templates = load_templates(db)
        print(f"\n✅ {len(templates)} template(s) processed successfully!")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error loading templates: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

