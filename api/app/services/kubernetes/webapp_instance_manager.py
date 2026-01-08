import yaml
from typing import Optional
from jinja2 import Environment, BaseLoader
from sqlalchemy.orm import Session

from app.services.component_template_config import ComponentTemplateConfigService


class KubernetesApplicationComponentManager:
    """
    Gerencia a renderização de templates Kubernetes para componentes de aplicação.
    Utiliza a configuração de templates (component_template_config) para determinar
    quais templates devem ser renderizados e em que ordem.
    """

    @staticmethod
    def instance_management(
        application_component: dict,
        component_type: str,
        settings: Optional[dict] = None,
        db: Optional[Session] = None
    ):
        """
        Renderiza templates Kubernetes para um componente de aplicação.

        Args:
            application_component: Dict com informações do componente (name, uuid, settings, etc.)
            component_type: Tipo do componente (webapp, worker, cron)
            settings: Dict opcional com configurações do ambiente
            db: Sessão do banco de dados (obrigatória)

        Returns:
            Lista de dicionários YAML renderizados, ordenados por render_order

        Raises:
            ValueError: Se não houver templates configurados ou erro na renderização
        """
        if db is None:
            raise ValueError("Database session is required")

        if settings is None:
            settings = {}

        # Preparar variáveis para os templates
        variables = {
            "application_settings": application_component,
            "environment_settings": settings
        }

        # Buscar templates configurados para o tipo de componente
        # Os templates já vêm ordenados por render_order
        templates = ComponentTemplateConfigService.get_templates_for_component(db, component_type)

        if not templates:
            raise ValueError(
                f"No templates configured for component type '{component_type}'. "
                "Please configure templates in the Component Template Config section."
            )

        combined_payloads = []

        # Renderizar cada template na ordem configurada
        for template in templates:
            try:
                rendered_yaml = KubernetesApplicationComponentManager.render_template_from_string(
                    template.content, variables
                )
                combined_payloads.append(rendered_yaml)
            except Exception as e:
                raise ValueError(
                    f"Error rendering template '{template.name}': {e}"
                )

        return combined_payloads

    @staticmethod
    def render_template_from_string(template_content: str, variables: dict):
        """
        Renderiza um template Jinja2 a partir de uma string.

        Args:
            template_content: Conteúdo do template Jinja2
            variables: Dicionário com variáveis para renderização

        Returns:
            Dicionário Python representando o YAML renderizado

        Raises:
            FileNotFoundError: Se houver erro na criação do template
            ValueError: Se houver erro no parsing do YAML
        """
        env = Environment(loader=BaseLoader())

        try:
            template = env.from_string(template_content)
        except Exception as e:
            raise FileNotFoundError(f"Template rendering error: {e}")

        rendered_yaml = template.render(variables)

        try:
            return yaml.safe_load(rendered_yaml)
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML template: {e}")
