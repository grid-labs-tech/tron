import yaml
from typing import Optional
from jinja2 import Environment, BaseLoader
from sqlalchemy.orm import Session

from app.templates.infra.component_template_config_repository import ComponentTemplateConfigRepository
from app.templates.infra.template_repository import TemplateRepository
from app.templates.core.component_template_config_service import ComponentTemplateConfigService


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
        gateway_reference: Optional[dict] = None
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
            gateway_reference = {
                "namespace": "",
                "name": ""
            }

        # Prepare variables for templates
        variables = {
            "application": application_component,
            "environment": settings,
            "cluster": {
                "gateway": {
                    "reference": gateway_reference
                }
            }
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

        # Render each template in configured order
        for template in templates:
            try:
                rendered_yaml = KubernetesApplicationComponentManager.render_template_from_string(
                    template.content, variables
                )
                # Filter None documents (when template doesn't render anything due to conditions)
                if rendered_yaml is not None:
                    combined_payloads.append(rendered_yaml)
            except Exception as e:
                raise ValueError(
                    f"Error rendering template '{template.name}': {e}"
                )

        return combined_payloads

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
            if 'httproute' in template_content.lower():
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"HTTPRoute YAML parsing error: {e}. Rendered content:\n{rendered_yaml[:500]}")
            raise ValueError(f"Error parsing YAML template: {e}")
