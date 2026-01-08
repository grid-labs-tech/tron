from fastapi import HTTPException
import app.models.template as TemplateModel
import app.models.component_template_config as ComponentTemplateConfigModel
import app.schemas.template as TemplateSchema
from sqlalchemy.orm import Session
from uuid import uuid4
from uuid import UUID


class TemplateService:
    def upsert_template(
        db: Session, template: TemplateSchema.TemplateCreate, template_uuid: UUID = None
    ):
        if template_uuid:
            db_template = (
                db.query(TemplateModel.Template)
                .filter(TemplateModel.Template.uuid == template_uuid)
                .first()
            )
            if db_template:
                db_template.name = template.name
                db_template.description = template.description
                db_template.content = template.content
                db_template.variables_schema = template.variables_schema
                db.commit()
                db.refresh(db_template)
                return db_template

        new_template = TemplateModel.Template(
            uuid=uuid4(),
            name=template.name,
            description=template.description,
            category=template.category,
            content=template.content,
            variables_schema=template.variables_schema,
        )
        db.add(new_template)

        try:
            db.commit()
            db.refresh(new_template)
        except Exception as e:
            db.rollback()
            message = {"status": "error", "message": f"{e}"}
            raise HTTPException(status_code=400, detail=message)

        return new_template

    def update_template(
        db: Session, template_uuid: UUID, template_update: TemplateSchema.TemplateUpdate
    ):
        db_template = (
            db.query(TemplateModel.Template)
            .filter(TemplateModel.Template.uuid == template_uuid)
            .first()
        )
        if not db_template:
            raise HTTPException(status_code=404, detail="Template not found")

        if template_update.name is not None:
            db_template.name = template_update.name
        if template_update.description is not None:
            db_template.description = template_update.description
        if template_update.content is not None:
            db_template.content = template_update.content
        if template_update.variables_schema is not None:
            db_template.variables_schema = template_update.variables_schema

        try:
            db.commit()
            db.refresh(db_template)
        except Exception as e:
            db.rollback()
            message = {"status": "error", "message": f"{e}"}
            raise HTTPException(status_code=400, detail=message)

        return db_template

    def get_template(db: Session, template_uuid: UUID):
        return (
            db.query(TemplateModel.Template)
            .filter(TemplateModel.Template.uuid == template_uuid)
            .first()
        )

    def get_templates(db: Session, skip: int = 0, limit: int = 100, category: str = None):
        query = db.query(TemplateModel.Template)
        if category:
            query = query.filter(TemplateModel.Template.category == category)
        return query.offset(skip).limit(limit).all()

    def delete_template(db: Session, template_uuid: UUID):
        db_template = (
            db.query(TemplateModel.Template)
            .filter(TemplateModel.Template.uuid == template_uuid)
            .first()
        )
        if not db_template:
            raise HTTPException(status_code=404, detail="Template not found")

        # Verificar se há component_template_configs associados
        associated_configs = (
            db.query(ComponentTemplateConfigModel.ComponentTemplateConfig)
            .filter(ComponentTemplateConfigModel.ComponentTemplateConfig.template_id == db_template.id)
            .all()
        )

        if associated_configs:
            # Deletar primeiro as configurações associadas
            for config in associated_configs:
                db.delete(config)

            try:
                db.flush()  # Flush para garantir que as deleções das configs sejam aplicadas
            except Exception as e:
                db.rollback()
                message = {"status": "error", "message": f"Failed to delete associated configurations: {e}"}
                raise HTTPException(status_code=400, detail=message)

        try:
            db.delete(db_template)
            db.commit()
        except Exception as e:
            db.rollback()
            message = {"status": "error", "message": f"{e}"}
            raise HTTPException(status_code=400, detail=message)

        return {"status": "success", "message": "Template deleted successfully"}

