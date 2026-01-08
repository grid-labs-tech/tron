from fastapi import HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
from uuid import UUID

import app.models.application_components as ApplicationComponentModel
import app.models.instance as InstanceModel
import app.schemas.application_components as ApplicationComponentSchema


class ApplicationComponentService:
    def upsert_webapp(
        db: Session,
        webapp_deploy: ApplicationComponentSchema.ApplicationComponentCreate,
        uuid: UUID = None,
    ):
        # Validate URL based on exposure.type and visibility for webapp
        if webapp_deploy.type == ApplicationComponentSchema.WebappType.webapp:
            settings_dict = webapp_deploy.settings or {}
            exposure_type = settings_dict.get('exposure', {}).get('type', 'http')
            exposure_visibility = settings_dict.get('exposure', {}).get('visibility', 'cluster')

            # URL is required only if exposure.type is 'http' AND visibility is not 'cluster'
            if exposure_type == 'http' and exposure_visibility != 'cluster' and not webapp_deploy.url:
                raise HTTPException(
                    status_code=400,
                    detail="URL is required when type is 'webapp' with HTTP exposure type and visibility 'public' or 'private'"
                )
            # URL is not allowed if exposure.type is not 'http' or visibility is 'cluster'
            if (exposure_type != 'http' or exposure_visibility == 'cluster') and webapp_deploy.url:
                if exposure_type != 'http':
                    raise HTTPException(
                        status_code=400,
                        detail=f"URL is not allowed for webapp components with exposure type '{exposure_type}'. URL is only allowed for HTTP exposure type."
                    )
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="URL is not allowed for webapp components with 'cluster' visibility. URL is only allowed for 'public' or 'private' visibility."
                    )

        # Get instance by uuid
        instance = (
            db.query(InstanceModel.Instance)
            .filter(InstanceModel.Instance.uuid == webapp_deploy.instance_uuid)
            .first()
        )
        if instance is None:
            raise HTTPException(status_code=404, detail="Instance not found")

        if uuid:

            db_webapp_deploy = (
                db.query(ApplicationComponentModel.ApplicationComponent)
                .filter(ApplicationComponentModel.ApplicationComponent.uuid == uuid)
                .first()
            )

            if db_webapp_deploy is None:
                raise HTTPException(status_code=404, detail="Webapp Deploy not found")

            if webapp_deploy.name is not None:
                db_webapp_deploy.name = webapp_deploy.name
            if webapp_deploy.type is not None:
                db_webapp_deploy.type = webapp_deploy.type
            # Verificar se o campo url foi enviado no payload
            url_present_in_payload = 'url' in webapp_deploy.model_fields_set if hasattr(webapp_deploy, 'model_fields_set') else webapp_deploy.url is not None

            if webapp_deploy.settings is not None:
                settings_dict = webapp_deploy.settings
                db_webapp_deploy.settings = settings_dict

                # Obter exposure_type e visibility após atualizar settings
                exposure_type = settings_dict.get('exposure', {}).get('type', 'http')
                exposure_visibility = settings_dict.get('exposure', {}).get('visibility', 'cluster')

                # Se exposure.type não for HTTP ou visibility for cluster, limpar URL automaticamente
                if exposure_type != 'http' or exposure_visibility == 'cluster':
                    db_webapp_deploy.url = None
                elif url_present_in_payload:
                    # Se o campo url veio no payload, atualizar/limpar conforme o valor
                    if webapp_deploy.url is not None:
                        # Se for HTTP e visibility não for cluster e URL foi enviada, atualizar
                        db_webapp_deploy.url = webapp_deploy.url
                    else:
                        # Se url veio como None no payload, remover do banco
                        db_webapp_deploy.url = None
                # Se url não veio no payload, manter o valor atual do banco (não fazer nada)
            elif url_present_in_payload:
                # Se settings não foi atualizado mas URL foi enviada no payload
                final_settings = db_webapp_deploy.settings or {}
                exposure_type = final_settings.get('exposure', {}).get('type', 'http')
                exposure_visibility = final_settings.get('exposure', {}).get('visibility', 'cluster')
                if webapp_deploy.url is not None:
                    # Se URL foi enviada com valor, atualizar apenas se for HTTP e visibility não for cluster
                    if exposure_type == 'http' and exposure_visibility != 'cluster':
                        db_webapp_deploy.url = webapp_deploy.url
                    else:
                        # Se não for HTTP ou visibility for cluster, limpar URL
                        db_webapp_deploy.url = None
                else:
                    # Se url veio como None no payload, remover do banco
                    db_webapp_deploy.url = None

            if webapp_deploy.enabled is not None:
                db_webapp_deploy.enabled = webapp_deploy.enabled

            # Validate that webapp requires url only if exposure.type is 'http' and visibility is not 'cluster' (check final state after all updates)
            final_type = db_webapp_deploy.type
            if final_type == ApplicationComponentSchema.WebappType.webapp:
                final_settings = db_webapp_deploy.settings or {}
                exposure_type = final_settings.get('exposure', {}).get('type', 'http')
                exposure_visibility = final_settings.get('exposure', {}).get('visibility', 'cluster')
                final_url = db_webapp_deploy.url
                if exposure_type == 'http' and exposure_visibility != 'cluster' and not final_url:
                    raise HTTPException(
                        status_code=400,
                        detail="URL is required when type is 'webapp' with HTTP exposure type and visibility 'public' or 'private'"
                    )

            db.commit()
            db.refresh(db_webapp_deploy)

        else:
            # Garantir que settings tenha exposure se for webapp
            settings_dict = webapp_deploy.settings or {}
            if webapp_deploy.type == ApplicationComponentSchema.WebappType.webapp:
                if 'exposure' not in settings_dict:
                    settings_dict['exposure'] = {
                        'type': 'http',
                        'port': 80,
                        'visibility': 'cluster'
                    }
                elif 'visibility' not in settings_dict.get('exposure', {}):
                    settings_dict['exposure']['visibility'] = 'cluster'

                # Validar URL baseado no exposure.type e visibility
                exposure_type = settings_dict.get('exposure', {}).get('type', 'http')
                exposure_visibility = settings_dict.get('exposure', {}).get('visibility', 'cluster')

                # URL is required only if exposure.type is 'http' AND visibility is not 'cluster'
                if exposure_type == 'http' and exposure_visibility != 'cluster' and not webapp_deploy.url:
                    raise HTTPException(
                        status_code=400,
                        detail="URL is required when type is 'webapp' with HTTP exposure type and visibility 'public' or 'private'"
                    )
                # URL is not allowed if exposure.type is not 'http' or visibility is 'cluster'
                if (exposure_type != 'http' or exposure_visibility == 'cluster') and webapp_deploy.url:
                    if exposure_type != 'http':
                        raise HTTPException(
                            status_code=400,
                            detail=f"URL is not allowed for webapp components with exposure type '{exposure_type}'. URL is only allowed for HTTP exposure type."
                        )
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail="URL is not allowed for webapp components with 'cluster' visibility. URL is only allowed for 'public' or 'private' visibility."
                        )

            db_webapp_deploy = ApplicationComponentModel.ApplicationComponent(
                uuid=uuid4(),
                instance_id=instance.id,
                name=webapp_deploy.name,
                type=webapp_deploy.type,
                settings=settings_dict,
                url=webapp_deploy.url,
                enabled=webapp_deploy.enabled,
            )
            db.add(db_webapp_deploy)

            try:
                db.commit()
                db.refresh(db_webapp_deploy)
            except Exception as e:
                db.rollback()
                message = {"status": "error", "message": f"{e._sql_message}"}
                raise HTTPException(status_code=400, detail=message)

        return db_webapp_deploy

    def get_webapp_deploy(
        db: Session, uuid: int
    ) -> ApplicationComponentSchema.ApplicationComponentCompletedResponse:
        db_webapp_deploy = (
            db.query(ApplicationComponentModel.ApplicationComponent)
            .filter(ApplicationComponentModel.ApplicationComponent.uuid == uuid)
            .first()
        )
        if db_webapp_deploy is None:
            raise HTTPException(status_code=404, detail="Webapp Deploy not found")
        return ApplicationComponentSchema.ApplicationComponentCompletedResponse.model_validate(
            db_webapp_deploy
        )

    def get_webapp_deploys(
        db: Session, skip: int = 0, limit: int = 100
    ) -> ApplicationComponentSchema.ApplicationComponentReducedResponse:
        return db.query(ApplicationComponentModel.ApplicationComponent).offset(skip).limit(limit).all()

    def delete_webapp_deploy(db: Session, uuid: UUID):
        db_webapp_deploy = (
            db.query(ApplicationComponentModel.ApplicationComponent)
            .filter(ApplicationComponentModel.ApplicationComponent.uuid == uuid)
            .first()
        )
        if db_webapp_deploy is None:
            raise HTTPException(status_code=404, detail="Webapp Deploy not found")

        try:
            db.delete(db_webapp_deploy)
            db.commit()
        except Exception as e:
            db.rollback()
            message = {"status": "error", "message": f"{e._sql_message}"}
            print(dir(e))
            raise HTTPException(status_code=400, detail=message)

        return {"detail": "Webapp Deploy deleted successfully"}
