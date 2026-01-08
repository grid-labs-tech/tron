from fastapi import HTTPException

import app.models.settings as SettingsModel
import app.models.environment as EnvironmentModel
import app.schemas.settings as SettingstSchema

from sqlalchemy.orm import Session
from uuid import uuid4
from uuid import UUID


class SettingsService:
    def get(db: Session, uuid: int):
        db_settings = (
            db.query(SettingsModel.Settings)
            .filter(SettingsModel.Settings.uuid == uuid)
            .first()
        )

        if db_settings is None:
            raise HTTPException(status_code=404, detail="Settings not found")

        setting_data = {
            "uuid": db_settings.uuid,
            "key": db_settings.key,
            "value": db_settings.value,
            "description": db_settings.description,
            "environment": {
                "name": db_settings.environment.name,
                "uuid": db_settings.environment.uuid,
            }
        }

        return SettingstSchema.SettingsWithEnvironment.model_validate(setting_data)

    def list(db: Session, skip: int = 0, limit: int = 100):
        db_settings = db.query(SettingsModel.Settings).offset(skip).limit(limit).all()

        serialized_data = []

        for setting in db_settings:
            setting_data = {
                "uuid": setting.uuid,
                "key": setting.key,
                "value": setting.value,
                "description": setting.description,
                "environment": {
                    "name": setting.environment.name,
                    "uuid": setting.environment.uuid,
                },
            }

            settings_response = SettingstSchema.SettingsWithEnvironment.model_validate(setting_data)
            serialized_data.append(settings_response)

        return serialized_data

    def delete(db: Session, uuid: UUID):

        db_settings = (
            db.query(SettingsModel.Settings)
            .filter(SettingsModel.Settings.uuid == uuid)
            .first()
        )

        if db_settings is None:
            raise HTTPException(status_code=404, detail="Settings not found")

        try:
            db.delete(db_settings)
            db.commit()
        except Exception as e:
            db.rollback()
            message = {"status": "error", "message": f"{e._sql_message}"}
            raise HTTPException(status_code=400, detail=message)

        return {"detail": "Settings deleted successfully"}

    def upsert(
        db: Session,
        setting: SettingstSchema.SettingsBase,
        uuid: UUID = None,
    ):
        if uuid:
            db_settings = (
                db.query(SettingsModel.Settings)
                .filter(SettingsModel.Settings.uuid == uuid)
                .first()
            )

            if db_settings is None:
                raise HTTPException(status_code=404, detail="Setting not found")

            db_settings.key = setting.key
            db_settings.value = setting.value
            db_settings.description = setting.description

            try:
                db.commit()
                db.refresh(db_settings)
            except Exception as e:
                db.rollback()
                message = {"status": "error", "message": f"{e}"}

                raise HTTPException(status_code=400, detail=message)
        else:

            environment = (
                db.query(EnvironmentModel.Environment)
                .filter(EnvironmentModel.Environment.uuid == setting.environment_uuid)
                .first()
            )

            if environment is None:
                raise HTTPException(status_code=404, detail="Environment not found")

            db_settings = SettingsModel.Settings(
                uuid=uuid4(),
                key=setting.key,
                value=setting.value,
                description=setting.description,
                environment_id=environment.id
            )
            db.add(db_settings)

            try:
                db.commit()
                db.refresh(db_settings)
            except Exception as e:
                db.rollback()
                message = {"status": "error", "message": f"{e._sql_message}"}
                raise HTTPException(status_code=400, detail=message)

        return db_settings
