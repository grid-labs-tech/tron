from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from .. import database
from app.services.template import TemplateService
from app.schemas import template as schemas
from app.models.user import UserRole, User
from app.dependencies.auth import require_role, get_current_user
from uuid import UUID

router = APIRouter()


@router.post("/templates/", response_model=schemas.Template)
def create_template(
    template: schemas.TemplateCreate,
    db: Session = Depends(database.get_db),
    current_user = Depends(require_role([UserRole.ADMIN])),
):
    return TemplateService.upsert_template(db, template)


@router.put("/templates/{uuid}", response_model=schemas.Template)
def update_template(
    uuid: UUID,
    template: schemas.TemplateUpdate,
    db: Session = Depends(database.get_db),
    current_user = Depends(require_role([UserRole.ADMIN])),
):
    return TemplateService.update_template(db, uuid, template)


@router.get("/templates/", response_model=list[schemas.Template])
def list_templates(
    skip: int = 0,
    limit: int = 100,
    category: str = Query(None, description="Filter by category"),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    return TemplateService.get_templates(db, skip=skip, limit=limit, category=category)


@router.get("/templates/{uuid}", response_model=schemas.Template)
def get_template(
    uuid: UUID,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    db_template = TemplateService.get_template(db, uuid)
    if db_template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return db_template


@router.delete("/templates/{uuid}", response_model=dict)
def delete_template(
    uuid: UUID,
    db: Session = Depends(database.get_db),
    current_user = Depends(require_role([UserRole.ADMIN])),
):
    return TemplateService.delete_template(db, uuid)

