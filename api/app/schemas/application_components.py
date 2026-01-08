from pydantic import BaseModel, ConfigDict, model_validator, field_validator
from enum import Enum
from typing import Any, Dict
from uuid import UUID
from datetime import datetime


class WebappType(str, Enum):
    webapp = "webapp"
    worker = "worker"
    cron = "cron"


class VisibilityType(str, Enum):
    public = "public"
    private = "private"
    cluster = "cluster"


class ApplicationComponent(BaseModel):
    name: str

    @field_validator('name')
    @classmethod
    def validate_name_no_spaces(cls, v: str) -> str:
        if ' ' in v:
            raise ValueError("Component name cannot contain spaces")
        return v

    model_config = ConfigDict(
        from_attributes=True,
    )


class ApplicationComponentCreate(ApplicationComponent):
    instance_uuid: UUID
    name: str
    type: WebappType = WebappType.webapp
    settings: Dict[str, Any] | None = None
    url: str | None = None
    enabled: bool = True

    @model_validator(mode='after')
    def validate_url(self):
        """Validate that URL is required only when type is webapp, exposure.type is 'http' and visibility is not 'cluster'"""
        if self.type == WebappType.webapp and self.settings:
            exposure = self.settings.get('exposure', {})
            exposure_type = exposure.get('type', 'http')
            exposure_visibility = exposure.get('visibility', 'cluster')

            # URL is required only if exposure.type is 'http' AND visibility is not 'cluster'
            if exposure_type == 'http' and exposure_visibility != 'cluster' and not self.url:
                raise ValueError("Webapp components with HTTP exposure type and visibility 'public' or 'private' must have a URL")

            # URL is not allowed if exposure.type is not 'http' or visibility is 'cluster'
            if (exposure_type != 'http' or exposure_visibility == 'cluster') and self.url:
                if exposure_type != 'http':
                    raise ValueError(f"URL is not allowed for webapp components with exposure type '{exposure_type}'. URL is only allowed for HTTP exposure type.")
                else:
                    raise ValueError("URL is not allowed for webapp components with 'cluster' visibility. URL is only allowed for 'public' or 'private' visibility.")

        return self


class ApplicationComponentUpdate(BaseModel):
    type: WebappType | None = None
    settings: Dict[str, Any] | None = None
    url: str | None = None
    enabled: bool | None = None

    @model_validator(mode='after')
    def validate_url(self):
        """Validate that URL is not allowed when exposure.type is not 'http' or visibility is 'cluster'"""
        # Only validate if settings is provided
        # Note: We don't validate if URL is required here because url might not be in the payload
        # when only settings is updated (it might exist in DB). That validation is done in the service layer.
        if self.settings:
            exposure = self.settings.get('exposure', {})
            exposure_type = exposure.get('type', 'http')
            exposure_visibility = exposure.get('visibility', 'cluster')

            # URL is not allowed if exposure.type is not 'http' or visibility is 'cluster'
            if (exposure_type != 'http' or exposure_visibility == 'cluster') and self.url is not None:
                if exposure_type != 'http':
                    raise ValueError(f"URL is not allowed for webapp components with exposure type '{exposure_type}'. URL is only allowed for HTTP exposure type.")
                else:
                    raise ValueError("URL is not allowed for webapp components with 'cluster' visibility. URL is only allowed for 'public' or 'private' visibility.")

        return self


class ApplicationComponentCompletedResponse(ApplicationComponent):
    uuid: UUID
    name: str
    type: WebappType
    settings: Dict[str, Any] | None
    url: str | None
    enabled: bool
    created_at: str
    updated_at: str

    @model_validator(mode='before')
    @classmethod
    def convert_datetime_to_string(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if 'created_at' in data and isinstance(data['created_at'], datetime):
                data['created_at'] = data['created_at'].isoformat()
            if 'updated_at' in data and isinstance(data['updated_at'], datetime):
                data['updated_at'] = data['updated_at'].isoformat()
            # Remover visibility se existir (não é mais parte do modelo)
            if 'visibility' in data:
                del data['visibility']
        elif hasattr(data, '__dict__'):
            if hasattr(data, 'created_at') and isinstance(data.created_at, datetime):
                data.created_at = data.created_at.isoformat()
            if hasattr(data, 'updated_at') and isinstance(data.updated_at, datetime):
                data.updated_at = data.updated_at.isoformat()
            # Remover visibility se existir (não é mais parte do modelo)
            if hasattr(data, 'visibility'):
                delattr(data, 'visibility')
        return data

    model_config = ConfigDict(
        from_attributes=True,
    )


class ApplicationComponentReducedResponse(ApplicationComponent):
    uuid: UUID
    created_at: str
    updated_at: str

    @model_validator(mode='before')
    @classmethod
    def convert_datetime_to_string(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if 'created_at' in data and isinstance(data['created_at'], datetime):
                data['created_at'] = data['created_at'].isoformat()
            if 'updated_at' in data and isinstance(data['updated_at'], datetime):
                data['updated_at'] = data['updated_at'].isoformat()
            # Remover visibility se existir (não é mais parte do modelo)
            if 'visibility' in data:
                del data['visibility']
        elif hasattr(data, '__dict__'):
            if hasattr(data, 'created_at') and isinstance(data.created_at, datetime):
                data.created_at = data.created_at.isoformat()
            if hasattr(data, 'updated_at') and isinstance(data.updated_at, datetime):
                data.updated_at = data.updated_at.isoformat()
            # Remover visibility se existir (não é mais parte do modelo)
            if hasattr(data, 'visibility'):
                delattr(data, 'visibility')
        return data

    model_config = ConfigDict(
        from_attributes=True,
    )

