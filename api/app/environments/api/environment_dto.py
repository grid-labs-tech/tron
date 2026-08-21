from pydantic import BaseModel, ConfigDict, model_validator
from uuid import UUID
from datetime import datetime
from typing import Any, Union


class EnvironmentBase(BaseModel):
    name: str


class EnvironmentCreate(EnvironmentBase):
    pass


class Environment(EnvironmentBase):
    uuid: UUID

    model_config = ConfigDict(
        from_attributes=True,
    )


class EnvironmentSettingItem(BaseModel):
    """Single item in environment settings array."""

    key: str
    value: Union[str, int, float, bool, list, dict]
    description: str = ""
    type: str = "string"


class EnvironmentSettingsUpdate(BaseModel):
    """
    Payload to update environment settings (idempotent).
    Only values are updated; key, description and type are read-only.
    Body is a flat object: setting key -> new value. Extra keys allowed.
    """

    model_config = ConfigDict(extra="allow")

    def get_settings_dict(self) -> dict:
        """Return key -> value dict for merging."""
        return self.model_dump(exclude_none=True)


class EnvironmentClusterSummary(BaseModel):
    uuid: UUID
    name: str


class EnvironmentWithClusters(Environment):
    name: str
    clusters: list[EnvironmentClusterSummary]
    settings: list
    created_at: str
    updated_at: str

    @model_validator(mode="before")
    @classmethod
    def convert_datetime_to_string(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "created_at" in data and isinstance(data["created_at"], datetime):
                data["created_at"] = data["created_at"].isoformat()
            if "updated_at" in data and isinstance(data["updated_at"], datetime):
                data["updated_at"] = data["updated_at"].isoformat()
        elif hasattr(data, "__dict__"):
            if hasattr(data, "created_at") and isinstance(data.created_at, datetime):
                data.created_at = data.created_at.isoformat()
            if hasattr(data, "updated_at") and isinstance(data.updated_at, datetime):
                data.updated_at = data.updated_at.isoformat()
        return data

    model_config = ConfigDict(
        from_attributes=True,
    )
