from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from .. import database
from app.services.component_template_config import ComponentTemplateConfigService
from app.schemas import component_template_config as schemas
from app.models.user import UserRole, User
from app.dependencies.auth import require_role, get_current_user
from uuid import UUID

router = APIRouter()


@router.post("/component-template-configs/", response_model=schemas.ComponentTemplateConfig)
def create_component_template_config(
    config: schemas.ComponentTemplateConfigCreate,
    db: Session = Depends(database.get_db),
    current_user = Depends(require_role([UserRole.ADMIN])),
):
    db_config = ComponentTemplateConfigService.upsert_component_template_config(db, config)
    # Serializar manualmente para incluir template_uuid
    return {
        "uuid": db_config.uuid,
        "component_type": db_config.component_type,
        "template_uuid": db_config.template.uuid,
        "render_order": db_config.render_order,
        "enabled": db_config.enabled == "true",
    }


@router.put("/component-template-configs/{uuid}", response_model=schemas.ComponentTemplateConfig)
def update_component_template_config(
    uuid: UUID,
    config: schemas.ComponentTemplateConfigUpdate,
    db: Session = Depends(database.get_db),
    current_user = Depends(require_role([UserRole.ADMIN])),
):
    db_config = ComponentTemplateConfigService.update_component_template_config(db, uuid, config)
    # Serializar manualmente para incluir template_uuid
    return {
        "uuid": db_config.uuid,
        "component_type": db_config.component_type,
        "template_uuid": db_config.template.uuid,
        "render_order": db_config.render_order,
        "enabled": db_config.enabled == "true",
    }


@router.get("/component-template-configs/", response_model=list[schemas.ComponentTemplateConfig])
def list_component_template_configs(
    skip: int = 0,
    limit: int = 100,
    component_type: str = Query(None, description="Filter by component type"),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    configs = ComponentTemplateConfigService.get_component_template_configs(
        db, component_type=component_type, skip=skip, limit=limit
    )
    # Adicionar informações do template
    result = []
    for config in configs:
        config_dict = {
            "uuid": str(config.uuid),
            "component_type": config.component_type,
            "template_uuid": str(config.template.uuid),
            "render_order": config.render_order,
            "enabled": config.enabled == "true",
            "template_name": config.template.name if config.template else None,
        }
        result.append(config_dict)
    return result


@router.get("/component-template-configs/{uuid}", response_model=schemas.ComponentTemplateConfig)
def get_component_template_config(
    uuid: UUID,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    db_config = ComponentTemplateConfigService.get_component_template_config(db, uuid)
    if db_config is None:
        raise HTTPException(status_code=404, detail="Component template config not found")
    # Serializar manualmente para incluir template_uuid
    return {
        "uuid": db_config.uuid,
        "component_type": db_config.component_type,
        "template_uuid": db_config.template.uuid,
        "render_order": db_config.render_order,
        "enabled": db_config.enabled == "true",
    }


@router.delete("/component-template-configs/{uuid}", response_model=dict)
def delete_component_template_config(
    uuid: UUID,
    db: Session = Depends(database.get_db),
    current_user = Depends(require_role([UserRole.ADMIN])),
):
    return ComponentTemplateConfigService.delete_component_template_config(db, uuid)


@router.get("/component-template-configs/component/{component_type}/templates", response_model=list)
def get_templates_for_component(
    component_type: str,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    """Get templates ordered by render_order for a specific component type"""
    templates = ComponentTemplateConfigService.get_templates_for_component(db, component_type)
    return [
        {
            "uuid": str(template.uuid),
            "name": template.name,
            "content": template.content,
        }
        for template in templates
    ]

