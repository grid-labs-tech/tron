import os
import re
import yaml
from datetime import datetime
from typing import Optional
from jinja2 import Environment, BaseLoader
from sqlalchemy.orm import Session

from app.templates.infra.component_template_config_repository import (
    ComponentTemplateConfigRepository,
)
from app.templates.infra.template_repository import TemplateRepository
from app.templates.core.component_template_config_service import (
    ComponentTemplateConfigService,
)
from app.templates.core.template_settings import build_template_settings_context

# When set, rendered Jinja outputs are written here for debugging (one file per template + one combined)
TRON_DEBUG_RENDER_DIR = os.environ.get("TRON_DEBUG_RENDER_DIR", "").strip()


def _save_rendered_debug(rendered_yaml: str, label: str) -> None:
    """If TRON_DEBUG_RENDER_DIR is set, save rendered YAML to a file for debugging."""
    if not TRON_DEBUG_RENDER_DIR:
        return
    os.makedirs(TRON_DEBUG_RENDER_DIR, exist_ok=True)
    safe_label = re.sub(r"[^\w\-]", "_", label)[:80]
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(TRON_DEBUG_RENDER_DIR, f"render_{timestamp}_{safe_label}.yaml")
    with open(path, "w") as f:
        f.write(rendered_yaml)
    import logging

    logging.getLogger(__name__).info("Debug render saved: %s", path)


def _save_combined_debug(payloads: list) -> None:
    """If TRON_DEBUG_RENDER_DIR is set, save combined rendered payloads as multi-doc YAML."""
    if not TRON_DEBUG_RENDER_DIR:
        return
    os.makedirs(TRON_DEBUG_RENDER_DIR, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(TRON_DEBUG_RENDER_DIR, f"combined_{timestamp}.yaml")
    with open(path, "w") as f:
        yaml.dump_all(payloads, f, default_flow_style=False, sort_keys=False)
    import logging

    logging.getLogger(__name__).info("Debug combined render saved: %s", path)


# Path to the shared secrets template
SECRETS_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "k8s",
    "templates",
    "shared",
    "secret.yaml.j2",
)


class KubernetesApplicationComponentManager:
    """
    Manages the rendering of Kubernetes templates for application components.
    Uses template configuration (component_template_config) to determine
    which templates should be rendered and in what order.
    """

    @staticmethod
    def instance_management(
        application_component: dict,
        component_type: str,
        settings: Optional[dict] = None,
        db: Optional[Session] = None,
        gateway_reference: Optional[dict] = None,
        organization_id: Optional[int] = None,
    ):
        """
        Render Kubernetes templates for an application component.

        Args:
            application_component: Dict with component information (name, uuid, settings, etc.)
            component_type: Component type (webapp, worker, cron)
            settings: Optional dict with environment settings
            db: Database session (required)
            gateway_reference: Optional dict with gateway information (namespace, name)
            organization_id: Optional organization id to fetch only that org's templates (avoids duplicate renders)

        Returns:
            List of rendered YAML dictionaries, ordered by render_order

        Raises:
            ValueError: If no templates are configured or error in rendering
        """
        if db is None:
            raise ValueError("Database session is required")

        if settings is None:
            settings = {}

        # Default values for gateway_reference if not provided
        if gateway_reference is None:
            gateway_reference = {"namespace": "", "name": ""}

        # Prepare variables for templates
        variables = {
            "application": application_component,
            "environment": settings,
            "cluster": {"gateway": {"reference": gateway_reference}},
        }

        # Fetch configured templates for component type (scoped by organization to avoid duplicates)
        # Templates already come ordered by render_order
        config_repository = ComponentTemplateConfigRepository(db)
        template_repository = TemplateRepository(db)
        service = ComponentTemplateConfigService(config_repository, template_repository)
        templates = service.get_templates_for_component_type(
            component_type, organization_id=organization_id
        )
        # Deduplicate by template id (same template in multiple configs = render once)
        seen_ids = set()
        unique_templates = []
        for t in templates:
            if t.id not in seen_ids:
                seen_ids.add(t.id)
                unique_templates.append(t)
        templates = unique_templates

        stored_template_values = {}
        serialized_template = application_component.get("template") or {}
        if isinstance(serialized_template, dict):
            for slug, payload in serialized_template.items():
                if isinstance(payload, dict) and "settings" in payload:
                    stored_template_values[slug] = payload.get("settings") or {}
                elif isinstance(payload, dict):
                    stored_template_values[slug] = payload
        application_component["template"] = build_template_settings_context(
            templates, stored_template_values
        )

        if not templates:
            raise ValueError(
                f"No templates configured for component type '{component_type}'. "
                "Please configure templates in the Component Template Config section."
            )

        combined_payloads = []

        # Check if component has secrets and render Secret template first
        component_settings = application_component.get("settings", {})
        secrets = component_settings.get("secrets", [])
        if secrets and len(secrets) > 0:
            secret_payload = (
                KubernetesApplicationComponentManager._render_secrets_template(
                    variables
                )
            )
            if secret_payload:
                combined_payloads.append(secret_payload)

        # Render each template in configured order
        for template in templates:
            try:
                rendered_yaml = (
                    KubernetesApplicationComponentManager.render_template_from_string(
                        template.content, variables, debug_label=template.name
                    )
                )
                # Filter None documents (when template doesn't render anything due to conditions)
                if rendered_yaml is not None:
                    combined_payloads.append(rendered_yaml)
            except Exception as e:
                raise ValueError(f"Error rendering template '{template.name}': {e}")

        if TRON_DEBUG_RENDER_DIR and combined_payloads:
            _save_combined_debug(combined_payloads)

        return combined_payloads

    @staticmethod
    def _render_secrets_template(variables: dict):
        """
        Render the Kubernetes Secret template for components with secrets.

        This is called automatically when a component has secrets configured.
        The Secret is created/updated in the namespace before the main resources.

        Args:
            variables: Dictionary with variables for rendering

        Returns:
            Python dictionary representing the rendered Secret YAML, or None if no secrets
        """
        try:
            with open(SECRETS_TEMPLATE_PATH, "r") as f:
                template_content = f.read()

            return KubernetesApplicationComponentManager.render_template_from_string(
                template_content, variables, debug_label="secret"
            )
        except FileNotFoundError:
            # Template file not found, skip secrets
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Secrets template not found at {SECRETS_TEMPLATE_PATH}")
            return None
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error rendering secrets template: {e}")
            return None

    @staticmethod
    def render_template_from_string(
        template_content: str, variables: dict, debug_label: Optional[str] = None
    ):
        """
        Render a Jinja2 template from a string.

        Args:
            template_content: Jinja2 template content
            variables: Dictionary with variables for rendering
            debug_label: Optional label for debug output file (used when TRON_DEBUG_RENDER_DIR is set)

        Returns:
            Python dictionary representing the rendered YAML

        Raises:
            FileNotFoundError: If there's an error creating the template
            ValueError: If there's an error parsing the YAML
        """
        env = Environment(loader=BaseLoader())

        try:
            template = env.from_string(template_content)
        except Exception as e:
            raise FileNotFoundError(f"Template rendering error: {e}")

        rendered_yaml = template.render(variables)

        if TRON_DEBUG_RENDER_DIR and rendered_yaml and rendered_yaml.strip():
            _save_rendered_debug(rendered_yaml, debug_label or "template")

        # If template rendered an empty string or only whitespace, return None
        if not rendered_yaml or not rendered_yaml.strip():
            return None

        try:
            # Use safe_load for a single YAML document
            parsed_yaml = yaml.safe_load(rendered_yaml)
            return parsed_yaml
        except yaml.YAMLError as e:
            # Debug: log parsing error for httproute
            if "httproute" in template_content.lower():
                import logging

                logger = logging.getLogger(__name__)
                logger.error(
                    f"HTTPRoute YAML parsing error: {e}. Rendered content:\n{rendered_yaml[:500]}"
                )
            raise ValueError(f"Error parsing YAML template: {e}")
