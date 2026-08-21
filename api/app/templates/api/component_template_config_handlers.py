from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.shared.database.database import get_db
from app.templates.infra.component_template_config_repository import (
    ComponentTemplateConfigRepository,
)
from app.templates.infra.template_repository import TemplateRepository
from app.templates.core.component_template_config_service import (
    ComponentTemplateConfigService,
)
from app.templates.api.component_template_config_dto import (
    ComponentTemplateConfigCreate,
    ComponentTemplateConfigUpdate,
    ComponentTemplateConfig,
)
from app.templates.core.component_template_config_validators import (
    ComponentTemplateConfigNotFoundError,
    ComponentTemplateConfigAlreadyExistsError,
    TemplateNotFoundError,
)
from app.organizations.api.dependencies.organization_context import (
    getOrganizationContext,
)
from app.organizations.core.authorization import (
    OrganizationAccessContext,
    isOrgAdmin,
)
from app.templates.api.template_dto import TemplateSettingsGroup


router = APIRouter(
    prefix="/organizations/{organization_uuid}/component-template-configs",
    tags=["component-template-configs"],
)


def get_component_template_config_service(
    database_session: Session = Depends(get_db),
) -> ComponentTemplateConfigService:
    """Dependency to get ComponentTemplateConfigService instance."""
    config_repository = ComponentTemplateConfigRepository(database_session)
    template_repository = TemplateRepository(database_session)
    return ComponentTemplateConfigService(config_repository, template_repository)


@router.post("/", response_model=ComponentTemplateConfig)
def create_component_template_config(
    organization_uuid: UUID,
    config: ComponentTemplateConfigCreate,
    service: ComponentTemplateConfigService = Depends(
        get_component_template_config_service
    ),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
):
    """Create a new component template config. Only organization admins can create configs."""
    if not isOrgAdmin(ctx):
        raise HTTPException(
            status_code=403,
            detail="Only organization admins can create component template configs",
        )

    try:
        db_config = service.create_component_template_config(
            config, ctx.organization.id
        )
        # Serialize manually to include template_uuid
        return {
            "uuid": db_config.uuid,
            "component_type": db_config.component_type,
            "template_uuid": db_config.template.uuid,
            "render_order": db_config.render_order,
            "enabled": db_config.enabled == "true",
        }
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ComponentTemplateConfigAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{uuid}", response_model=ComponentTemplateConfig)
def update_component_template_config(
    organization_uuid: UUID,
    uuid: UUID,
    config: ComponentTemplateConfigUpdate,
    service: ComponentTemplateConfigService = Depends(
        get_component_template_config_service
    ),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
):
    """Update an existing component template config. Only organization admins can update configs."""
    if not isOrgAdmin(ctx):
        raise HTTPException(
            status_code=403,
            detail="Only organization admins can update component template configs",
        )

    # Verify config belongs to organization
    config_model = service.config_repository.find_by_uuid(uuid)
    if not config_model or config_model.organization_id != ctx.organization.id:
        raise HTTPException(
            status_code=404, detail="Component template config not found"
        )

    try:
        db_config = service.update_component_template_config(uuid, config)
        # Serialize manually to include template_uuid
        return {
            "uuid": db_config.uuid,
            "component_type": db_config.component_type,
            "template_uuid": db_config.template.uuid,
            "render_order": db_config.render_order,
            "enabled": db_config.enabled == "true",
        }
    except ComponentTemplateConfigNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[ComponentTemplateConfig])
def list_component_template_configs(
    organization_uuid: UUID,
    skip: int = 0,
    limit: int = 100,
    component_type: str = Query(None, description="Filter by component type"),
    service: ComponentTemplateConfigService = Depends(
        get_component_template_config_service
    ),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
):
    """List all component template configs for the organization."""
    if not isOrgAdmin(ctx):
        raise HTTPException(
            status_code=403,
            detail="Only organization admins can list component template configs",
        )

    configs = service.get_component_template_configs(
        component_type=component_type,
        skip=skip,
        limit=limit,
        organization_id=ctx.organization.id,
    )
    # Serialize manually to include template information
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


@router.get("/{uuid}", response_model=ComponentTemplateConfig)
def get_component_template_config(
    organization_uuid: UUID,
    uuid: UUID,
    service: ComponentTemplateConfigService = Depends(
        get_component_template_config_service
    ),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
):
    """Get component template config by UUID."""
    try:
        db_config = service.get_component_template_config(uuid)
        # Verify config belongs to organization
        if db_config.organization_id != ctx.organization.id:
            raise HTTPException(
                status_code=404, detail="Component template config not found"
            )
        # Serialize manually to include template_uuid
        return {
            "uuid": db_config.uuid,
            "component_type": db_config.component_type,
            "template_uuid": db_config.template.uuid,
            "render_order": db_config.render_order,
            "enabled": db_config.enabled == "true",
        }
    except ComponentTemplateConfigNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{uuid}", response_model=dict)
def delete_component_template_config(
    organization_uuid: UUID,
    uuid: UUID,
    service: ComponentTemplateConfigService = Depends(
        get_component_template_config_service
    ),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
):
    """Delete a component template config. Only organization admins can delete configs."""
    if not isOrgAdmin(ctx):
        raise HTTPException(
            status_code=403,
            detail="Only organization admins can delete component template configs",
        )

    # Verify config belongs to organization
    config_model = service.config_repository.find_by_uuid(uuid)
    if not config_model or config_model.organization_id != ctx.organization.id:
        raise HTTPException(
            status_code=404, detail="Component template config not found"
        )

    try:
        return service.delete_component_template_config(uuid)
    except ComponentTemplateConfigNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/component/{component_type}/template-settings",
    response_model=List[TemplateSettingsGroup],
)
def get_template_settings_for_component(
    organization_uuid: UUID,
    component_type: str,
    service: ComponentTemplateConfigService = Depends(
        get_component_template_config_service
    ),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
):
    """Return enabled templates' settings schema for a component type. Any org member can read."""
    return service.get_template_settings_for_component_type(
        component_type, organization_id=ctx.organization.id
    )


@router.get(
    "/component/{component_type}/templates",
    response_model=List[dict],
)
def get_templates_for_component(
    organization_uuid: UUID,
    component_type: str,
    service: ComponentTemplateConfigService = Depends(
        get_component_template_config_service
    ),
    ctx: OrganizationAccessContext = Depends(getOrganizationContext),
):
    """Get templates ordered by render_order for a specific component type in the organization."""
    templates = service.get_templates_for_component_type(
        component_type, organization_id=ctx.organization.id
    )
    return [
        {
            "uuid": str(template.uuid),
            "name": template.name,
            "content": template.content,
        }
        for template in templates
    ]
