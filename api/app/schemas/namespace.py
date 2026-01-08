from pydantic import BaseModel, ConfigDict, field_validator
from uuid import UUID
from datetime import datetime


class NamespaceBase(BaseModel):
    name: str

    @field_validator("name")
    def no_spaces_allowed(cls, value):
        if " " in value:
            raise ValueError("Name must not contain spaces.")
        return value

class NamespaceCreate(NamespaceBase):
    pass


class Namespace(NamespaceBase):
    uuid: UUID
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
