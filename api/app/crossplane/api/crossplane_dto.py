from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class CrossplaneConfigUpdate(BaseModel):
    enabled: bool = False
    cluster_uuid: UUID | None = None
    aws_region: str = ""
    aws_account_id: str = ""
    provider_config: str = ""

    @field_validator("cluster_uuid", mode="before")
    @classmethod
    def empty_cluster_uuid_to_none(cls, value):
        if value == "" or value is None:
            return None
        return value

    @field_validator("aws_region", "aws_account_id", "provider_config", mode="before")
    @classmethod
    def none_string_to_empty(cls, value):
        if value is None:
            return ""
        return value


class CrossplaneConfigResponse(BaseModel):
    enabled: bool = False
    cluster_uuid: UUID | None = None
    aws_region: str = ""
    aws_account_id: str = ""
    provider_config: str = ""

    model_config = ConfigDict(from_attributes=True)


class CrossplaneProviderStatus(BaseModel):
    name: str = ""
    healthy: bool = False


class CrossplaneFeatures(BaseModel):
    """Live Crossplane probe status owned by the Crossplane bounded context."""

    available: bool = False
    healthy: bool = False
    providers: list[CrossplaneProviderStatus] = []
