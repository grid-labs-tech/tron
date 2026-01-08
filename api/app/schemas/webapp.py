from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from enum import Enum
from typing import List, Any, Dict, Union
from uuid import UUID
from datetime import datetime
import shlex


class WebappProtocolType(str, Enum):
    http = "http"
    https = "https"
    tcp = "tcp"
    tls = "tls"


class WebappHealthcheckProtocolType(str, Enum):
    http = "http"
    tcp = "tcp"


class VisibilityType(str, Enum):
    public = "public"
    private = "private"
    cluster = "cluster"


class WebappExposure(BaseModel):
    type: str  # "http" | "tcp" | "udp"
    port: int
    visibility: VisibilityType  # "cluster" | "private" | "public"

    model_config = ConfigDict(
        from_attributes=True,
    )


class WebappEnvs(BaseModel):
    key: str
    value: str


class WebappCustomMetrics(BaseModel):
    enabled: bool = False
    path: str = "/metrics"
    port: int


class WebappHealthcheck(BaseModel):
    path: str = "/healthcheck"
    protocol: WebappHealthcheckProtocolType
    port: int = 80
    timeout: int = 3
    interval: int = 15
    initial_interval: int = 15
    failure_threshold: int = 2


class WebappAutoscaling(BaseModel):
    min: int = 2
    max: int = 10


class WebappSettings(BaseModel):
    custom_metrics: WebappCustomMetrics
    exposure: WebappExposure
    envs: List[WebappEnvs] = []
    command: Union[str, List[str], None] = None
    cpu_scaling_threshold: int = 80
    memory_scaling_threshold: int = 80
    healthcheck: WebappHealthcheck
    cpu: float
    memory: int
    autoscaling: WebappAutoscaling

    @model_validator(mode='before')
    @classmethod
    def migrate_exposure(cls, data: Any) -> Any:
        """Migrate endpoints to exposure format if needed"""
        if isinstance(data, dict):
            # Migrate from old endpoints format to exposure
            if 'endpoints' in data and 'exposure' not in data:
                endpoints = data['endpoints']
                # Handle array format (old)
                if isinstance(endpoints, list) and len(endpoints) > 0:
                    endpoints = endpoints[0]
                # Handle object format (old)
                if isinstance(endpoints, dict):
                    # Default to cluster if visibility not in exposure
                    visibility = 'cluster'
                    if 'exposure' in data and isinstance(data.get('exposure'), dict) and 'visibility' in data['exposure']:
                        visibility = data['exposure']['visibility']
                    elif isinstance(endpoints, dict) and 'visibility' in endpoints:
                        visibility = endpoints['visibility']

                    if isinstance(visibility, str):
                        visibility = visibility.lower()
                    else:
                        visibility = 'cluster'

                    # Map old format to new format
                    data['exposure'] = {
                        'type': endpoints.get('source_protocol', 'http'),
                        'port': endpoints.get('source_port', 80),
                        'visibility': visibility
                    }
                    # Remove old endpoints
                    del data['endpoints']
            # Ensure exposure exists with defaults
            if 'exposure' not in data:
                # Default to cluster (visibility não existe mais no nível do componente)
                data['exposure'] = {
                    'type': 'http',
                    'port': 80,
                    'visibility': 'cluster'
                }
            # Remover visibility do nível superior se existir (não é mais parte do modelo)
            if 'visibility' in data:
                del data['visibility']
        return data

    @model_validator(mode='after')
    def parse_command(self):
        """Parse command string into array if it's a string"""
        if isinstance(self.command, str):
            # Use shlex to properly parse the command string, handling quotes and spaces
            command_str = self.command.strip()
            if command_str:
                self.command = shlex.split(command_str)
            else:
                self.command = None
        # If it's already a list or None, keep it as is
        return self


class WebappBase(BaseModel):
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


class WebappCreate(WebappBase):
    instance_uuid: UUID
    name: str
    url: str | None = None
    enabled: bool = True
    settings: WebappSettings

    @model_validator(mode='after')
    def validate_url(self):
        """Validate that URL is required only when exposure.type is 'http' and visibility is not 'cluster'"""
        if self.settings and self.settings.exposure:
            exposure_type = self.settings.exposure.type
            exposure_visibility = self.settings.exposure.visibility

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


class WebappUpdate(BaseModel):
    url: str | None = None
    enabled: bool | None = None
    settings: WebappSettings | None = None

    @model_validator(mode='after')
    def validate_url(self):
        """Validate that URL is not allowed when exposure.type is not 'http' or visibility is 'cluster'"""
        # Only validate if settings is provided (when settings is updated)
        # Note: We don't validate if URL is required here because url might not be in the payload
        # when only settings is updated (it might exist in DB). That validation is done in the service layer.
        if self.settings and self.settings.exposure:
            exposure_type = self.settings.exposure.type
            exposure_visibility = self.settings.exposure.visibility

            # URL is not allowed if exposure.type is not 'http' or visibility is 'cluster'
            if (exposure_type != 'http' or exposure_visibility == 'cluster') and self.url is not None:
                if exposure_type != 'http':
                    raise ValueError(f"URL is not allowed for webapp components with exposure type '{exposure_type}'. URL is only allowed for HTTP exposure type.")
                else:
                    raise ValueError("URL is not allowed for webapp components with 'cluster' visibility. URL is only allowed for 'public' or 'private' visibility.")

        return self


class Webapp(WebappBase):
    uuid: UUID
    name: str
    url: str | None
    enabled: bool
    settings: Dict[str, Any] | None
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


class Pod(BaseModel):
    name: str
    status: str
    restarts: int
    cpu_requests: float
    cpu_limits: float
    memory_requests: int  # em MB
    memory_limits: int  # em MB
    age_seconds: int
    host_ip: str | None = None


class PodLogs(BaseModel):
    logs: str
    pod_name: str
    container_name: str | None = None


class PodCommandRequest(BaseModel):
    command: list[str]
    container_name: str | None = None


class PodCommandResponse(BaseModel):
    stdout: str
    stderr: str
    return_code: int

