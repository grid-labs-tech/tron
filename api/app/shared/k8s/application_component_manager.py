import os
import yaml
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

# Path to the shared secrets template
SECRETS_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "k8s", "templates", "shared", "secret.yaml.j2"
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
    ):
        """
        Render Kubernetes templates for an application component.

        Args:
            application_component: Dict with component information (name, uuid, settings, etc.)
            component_type: Component type (webapp, worker, cron)
            settings: Optional dict with environment settings
            db: Database session (required)
            gateway_reference: Optional dict with gateway information (namespace, name)

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

        # Fetch configured templates for component type
        # Templates already come ordered by render_order
        config_repository = ComponentTemplateConfigRepository(db)
        template_repository = TemplateRepository(db)
        service = ComponentTemplateConfigService(config_repository, template_repository)
        templates = service.get_templates_for_component_type(component_type)

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
            secret_payload = KubernetesApplicationComponentManager._render_secrets_template(
                variables
            )
            if secret_payload:
                combined_payloads.append(secret_payload)

        # Render each template in configured order
        for template in templates:
            try:
                rendered_yaml = (
                    KubernetesApplicationComponentManager.render_template_from_string(
                        template.content, variables
                    )
                )
                # Filter None documents (when template doesn't render anything due to conditions)
                if rendered_yaml is not None:
                    combined_payloads.append(rendered_yaml)
            except Exception as e:
                raise ValueError(f"Error rendering template '{template.name}': {e}")

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
                template_content, variables
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
    def render_template_from_string(template_content: str, variables: dict):
        """
        Render a Jinja2 template from a string.

        Args:
            template_content: Jinja2 template content
            variables: Dictionary with variables for rendering

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
