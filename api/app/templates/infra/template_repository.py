from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List
from app.templates.infra.template_model import Template as TemplateModel
from app.templates.infra.component_template_config_model import (
    ComponentTemplateConfig as ComponentTemplateConfigModel,
)


class TemplateRepository:
    """Repository for Template database operations. No business logic here."""

    def __init__(self, database_session: Session):
        self.db = database_session

    def find_by_uuid(self, uuid: UUID) -> Optional[TemplateModel]:
        """Find template by UUID."""
        return self.db.query(TemplateModel).filter(TemplateModel.uuid == uuid).first()

    def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        category: str = None,
        organization_id: int | None = None,
    ) -> List[TemplateModel]:
        """Find all templates, optionally filtered by category and organization_id."""
        query = self.db.query(TemplateModel)
        if organization_id is not None:
            query = query.filter(TemplateModel.organization_id == organization_id)
        if category:
            query = query.filter(TemplateModel.category == category)
        return query.offset(skip).limit(limit).all()

    def find_slugs_by_organization_id(self, organization_id: int) -> List[str]:
        """Return all template slugs for an organization."""
        rows = (
            self.db.query(TemplateModel.slug)
            .filter(TemplateModel.organization_id == organization_id)
            .all()
        )
        return [row[0] for row in rows if row[0]]

    def find_by_organization_id(
        self,
        organization_id: int,
        skip: int = 0,
        limit: int = 100,
        category: str = None,
    ) -> List[TemplateModel]:
        """Find templates by organization_id, optionally filtered by category."""
        return self.find_all(
            skip=skip, limit=limit, category=category, organization_id=organization_id
        )

    def find_component_configs_by_template_id(
        self, template_id: int
    ) -> List[ComponentTemplateConfigModel]:
        """Find all component template configs associated with a template."""
        return (
            self.db.query(ComponentTemplateConfigModel)
            .filter(ComponentTemplateConfigModel.template_id == template_id)
            .all()
        )

    def create(self, template: TemplateModel) -> TemplateModel:
        """Create a new template."""
        self.db.add(template)
        try:
            self.db.commit()
            self.db.refresh(template)
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to create template: {str(e)}")
        return template

    def update(self, template: TemplateModel) -> TemplateModel:
        """Update an existing template."""
        try:
            self.db.commit()
            self.db.refresh(template)
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to update template: {str(e)}")
        return template

    def delete(self, template: TemplateModel) -> None:
        """Delete a template."""
        self.db.delete(template)
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to delete template: {str(e)}")

    def delete_component_configs(
        self, configs: List[ComponentTemplateConfigModel]
    ) -> None:
        """Delete component template configs."""
        for config in configs:
            self.db.delete(config)
        try:
            self.db.flush()
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to delete component configs: {str(e)}")

    def rollback(self) -> None:
        """Rollback current transaction."""
        self.db.rollback()
