from fastapi import HTTPException

import app.models.environment as EnvironmentModel
import app.models.application_components as ApplicationComponentModel
import app.models.instance as InstanceModel
import app.schemas.environment as EnvironmentSchema

from sqlalchemy.orm import Session
from uuid import uuid4
from uuid import UUID


class EnvironmentService:
    def get_environment(db: Session, environment_uuid: int):
        db_environment = (
            db.query(EnvironmentModel.Environment)
            .filter(EnvironmentModel.Environment.uuid == environment_uuid)
            .first()
        )

        if db_environment is None:
            raise HTTPException(status_code=404, detail="Environment not found")

        serialized_data = {
            "uuid": db_environment.uuid,
            "name": db_environment.name,
            "clusters": [cluster.name for cluster in db_environment.clusters],
            "settings": [{"key": settings.key, "value": settings.value, "description": settings.description} for settings in db_environment.settings],
            "created_at": db_environment.created_at,
            "updated_at": db_environment.updated_at
        }

        return EnvironmentSchema.EnvironmentWithClusters.model_validate(serialized_data)

    def get_environments(db: Session, skip: int = 0, limit: int = 100):
        db_environments = db.query(EnvironmentModel.Environment).offset(skip).limit(limit).all()

        serialized_data = []

        for environment in db_environments:
            environment_data = {
                "uuid": environment.uuid,
                "name": environment.name,
                "clusters": [cluster.name for cluster in environment.clusters],
                "settings": [{"key": settings.key, "value": settings.value, "description": settings.description} for settings in environment.settings],
                "created_at": environment.created_at,
                "updated_at": environment.updated_at
            }

            environment_response = EnvironmentSchema.EnvironmentWithClusters.model_validate(environment_data)
            serialized_data.append(environment_response)

        return serialized_data

    def delete_environment(db: Session, environment_uuid: UUID):

        db_environment = (
            db.query(EnvironmentModel.Environment)
            .filter(EnvironmentModel.Environment.uuid == environment_uuid)
            .first()
        )
        if db_environment is None:
            raise HTTPException(status_code=404, detail="Environment not found")

        associated_webapp_deploys = (
            db.query(ApplicationComponentModel.ApplicationComponent)
            .join(InstanceModel.Instance)
            .filter(InstanceModel.Instance.environment_id == db_environment.id)
            .all()
        )
        if associated_webapp_deploys:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete environment with associated webapps",
            )

        db.delete(db_environment)
        db.commit()
        return {"detail": "Environment deleted successfully"}

    def upsert_environment(
        db: Session,
        environment: EnvironmentSchema.EnvironmentCreate,
        environment_uuid: UUID = None,
    ):
        if environment_uuid:
            db_environment = (
                db.query(EnvironmentModel.Environment)
                .filter(EnvironmentModel.Environment.uuid == environment_uuid)
                .first()
            )
            if db_environment:
                db_environment.name = environment.name
                db.commit()
                db.refresh(db_environment)
                return db_environment

        new_environment = EnvironmentModel.Environment(
            uuid=uuid4(), name=environment.name
        )
        db.add(new_environment)
        db.commit()
        db.refresh(new_environment)
        return new_environment
