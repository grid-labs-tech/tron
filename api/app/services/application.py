from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import delete
from uuid import uuid4, UUID

import app.models.application as ApplicationModel
import app.models.instance as InstanceModel
import app.schemas.application as ApplicationSchema
from app.services.instance import InstanceService


class ApplicationService:
    @staticmethod
    def upsert_application(
        db: Session, application: ApplicationSchema.ApplicationCreate, application_uuid: UUID = None
    ):
        if application_uuid:
            db_application = (
                db.query(ApplicationModel.Application)
                .filter(ApplicationModel.Application.uuid == application_uuid)
                .first()
            )
            if db_application is None:
                raise HTTPException(status_code=404, detail="Application not found")

            db_application.name = application.name
            db_application.repository = application.repository
            db_application.enabled = application.enabled
        else:
            # Check if name already exists
            existing_application = (
                db.query(ApplicationModel.Application)
                .filter(ApplicationModel.Application.name == application.name)
                .first()
            )
            if existing_application:
                raise HTTPException(status_code=400, detail="Application with this name already exists")

            db_application = ApplicationModel.Application(
                uuid=uuid4(),
                name=application.name,
                repository=application.repository,
                enabled=application.enabled,
            )
            db.add(db_application)

        db.commit()
        db.refresh(db_application)
        return db_application

    @staticmethod
    def update_application(
        db: Session, application_uuid: UUID, application: ApplicationSchema.ApplicationUpdate
    ):
        db_application = (
            db.query(ApplicationModel.Application)
            .filter(ApplicationModel.Application.uuid == application_uuid)
            .first()
        )
        if db_application is None:
            raise HTTPException(status_code=404, detail="Application not found")

        if application.name is not None:
            # Check if name already exists (excluding current application)
            existing_application = (
                db.query(ApplicationModel.Application)
                .filter(
                    ApplicationModel.Application.name == application.name,
                    ApplicationModel.Application.uuid != application_uuid
                )
                .first()
            )
            if existing_application:
                raise HTTPException(status_code=400, detail="Application with this name already exists")
            db_application.name = application.name

        if application.repository is not None:
            db_application.repository = application.repository

        if application.enabled is not None:
            db_application.enabled = application.enabled

        db.commit()
        db.refresh(db_application)
        return db_application

    @staticmethod
    def get_application(db: Session, uuid: UUID) -> ApplicationSchema.Application:
        db_application = (
            db.query(ApplicationModel.Application)
            .filter(ApplicationModel.Application.uuid == uuid)
            .first()
        )

        if db_application is None:
            raise HTTPException(status_code=404, detail="Application not found")

        return db_application

    @staticmethod
    def get_applications(
        db: Session, skip: int = 0, limit: int = 100
    ) -> list[ApplicationSchema.Application]:
        return db.query(ApplicationModel.Application).offset(skip).limit(limit).all()

    @staticmethod
    def delete_application(db: Session, uuid: UUID):
        db_application = (
            db.query(ApplicationModel.Application)
            .options(joinedload(ApplicationModel.Application.instances))
            .filter(ApplicationModel.Application.uuid == uuid)
            .first()
        )
        if db_application is None:
            raise HTTPException(status_code=404, detail="Application not found")

        # Buscar todas as instâncias associadas à aplicação
        instances = (
            db.query(InstanceModel.Instance)
            .filter(InstanceModel.Instance.application_id == db_application.id)
            .all()
        )

        # Deletar cada instância usando o serviço de instância
        # Isso garante que componentes, cluster_instances e recursos do Kubernetes sejam deletados
        for instance in instances:
            try:
                InstanceService.delete_instance(db, instance.uuid)
            except Exception as e:
                # Se houver erro ao deletar uma instância, fazer rollback e relançar
                db.rollback()
                print(f"Error deleting instance '{instance.uuid}': {e}")
                raise HTTPException(status_code=400, detail=f"Failed to delete instance '{instance.uuid}': {str(e)}")

        try:
            # Deletar a aplicação usando delete direto no banco
            # Isso evita que o SQLAlchemy tente atualizar a foreign key
            application_id = db_application.id
            stmt = delete(ApplicationModel.Application).where(
                ApplicationModel.Application.id == application_id
            )
            db.execute(stmt)
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Failed to delete application: {str(e)}")

        return {"detail": "Application deleted successfully"}

