from fastapi import HTTPException
import app.models.component_template_config as ComponentTemplateConfigModel
import app.models.template as TemplateModel
import app.schemas.component_template_config as ComponentTemplateConfigSchema
from sqlalchemy.orm import Session
from uuid import uuid4
from uuid import UUID


class ComponentTemplateConfigService:
    def upsert_component_template_config(
        db: Session,
        config: ComponentTemplateConfigSchema.ComponentTemplateConfigCreate,
        config_uuid: UUID = None,
    ):
        # Verificar se template existe
        template = (
            db.query(TemplateModel.Template)
            .filter(TemplateModel.Template.uuid == config.template_uuid)
            .first()
        )
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        if config_uuid:
            db_config = (
                db.query(ComponentTemplateConfigModel.ComponentTemplateConfig)
                .filter(ComponentTemplateConfigModel.ComponentTemplateConfig.uuid == config_uuid)
                .first()
            )
            if db_config:
                db_config.render_order = config.render_order
                db_config.enabled = str(config.enabled).lower()
                db.commit()
                db.refresh(db_config)
                # Carregar template para serialização
                from sqlalchemy.orm import joinedload
                db.refresh(db_config, ["template"])
                return db_config

        # Verificar se já existe configuração para este component_type e template
        existing_config = (
            db.query(ComponentTemplateConfigModel.ComponentTemplateConfig)
            .filter(
                ComponentTemplateConfigModel.ComponentTemplateConfig.component_type == config.component_type,
                ComponentTemplateConfigModel.ComponentTemplateConfig.template_id == template.id,
            )
            .first()
        )
        if existing_config:
            raise HTTPException(
                status_code=400,
                detail=f"Configuration for component_type '{config.component_type}' and template '{config.template_uuid}' already exists",
            )

        new_config = ComponentTemplateConfigModel.ComponentTemplateConfig(
            uuid=uuid4(),
            component_type=config.component_type,
            template_id=template.id,
            render_order=config.render_order,
            enabled=str(config.enabled).lower(),
        )
        db.add(new_config)

        try:
            db.commit()
            db.refresh(new_config)
            # Carregar template para serialização
            from sqlalchemy.orm import joinedload
            db.refresh(new_config, ["template"])
        except Exception as e:
            db.rollback()
            message = {"status": "error", "message": f"{e}"}
            raise HTTPException(status_code=400, detail=message)

        return new_config

    def update_component_template_config(
        db: Session,
        config_uuid: UUID,
        config_update: ComponentTemplateConfigSchema.ComponentTemplateConfigUpdate,
    ):
        db_config = (
            db.query(ComponentTemplateConfigModel.ComponentTemplateConfig)
            .filter(ComponentTemplateConfigModel.ComponentTemplateConfig.uuid == config_uuid)
            .first()
        )
        if not db_config:
            raise HTTPException(status_code=404, detail="Component template config not found")

        if config_update.render_order is not None:
            db_config.render_order = config_update.render_order
        if config_update.enabled is not None:
            db_config.enabled = str(config_update.enabled).lower()

        try:
            db.commit()
            db.refresh(db_config)
            # Carregar template para serialização
            from sqlalchemy.orm import joinedload
            db.refresh(db_config, ["template"])
        except Exception as e:
            db.rollback()
            message = {"status": "error", "message": f"{e}"}
            raise HTTPException(status_code=400, detail=message)

        return db_config

    def get_component_template_config(db: Session, config_uuid: UUID):
        from sqlalchemy.orm import joinedload
        return (
            db.query(ComponentTemplateConfigModel.ComponentTemplateConfig)
            .options(joinedload(ComponentTemplateConfigModel.ComponentTemplateConfig.template))
            .filter(ComponentTemplateConfigModel.ComponentTemplateConfig.uuid == config_uuid)
            .first()
        )

    def get_component_template_configs(
        db: Session, component_type: str = None, skip: int = 0, limit: int = 100
    ):
        from sqlalchemy.orm import joinedload

        query = db.query(ComponentTemplateConfigModel.ComponentTemplateConfig).options(
            joinedload(ComponentTemplateConfigModel.ComponentTemplateConfig.template)
        )
        if component_type:
            query = query.filter(
                ComponentTemplateConfigModel.ComponentTemplateConfig.component_type == component_type
            )
        query = query.order_by(ComponentTemplateConfigModel.ComponentTemplateConfig.render_order)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_templates_for_component(db: Session, component_type: str):
        """Retorna templates ordenados por render_order para um tipo de componente"""
        configs = (
            db.query(ComponentTemplateConfigModel.ComponentTemplateConfig)
            .join(TemplateModel.Template)
            .filter(
                ComponentTemplateConfigModel.ComponentTemplateConfig.component_type == component_type,
                ComponentTemplateConfigModel.ComponentTemplateConfig.enabled == "true",
            )
            .order_by(ComponentTemplateConfigModel.ComponentTemplateConfig.render_order)
            .all()
        )
        return [config.template for config in configs]

    def delete_component_template_config(db: Session, config_uuid: UUID):
        db_config = (
            db.query(ComponentTemplateConfigModel.ComponentTemplateConfig)
            .filter(ComponentTemplateConfigModel.ComponentTemplateConfig.uuid == config_uuid)
            .first()
        )
        if not db_config:
            raise HTTPException(status_code=404, detail="Component template config not found")

        try:
            db.delete(db_config)
            db.commit()
        except Exception as e:
            db.rollback()
            message = {"status": "error", "message": f"{e}"}
            raise HTTPException(status_code=400, detail=message)

        return {"status": "success", "message": "Component template config deleted successfully"}

