from pydantic import BaseModel, ConfigDict, field_validator
from uuid import UUID
from typing import List, Literal, Optional


class TemplateSettingDefinition(BaseModel):
    name: str
    description: Optional[str] = None
    type: Literal["boolean", "string"]


class TemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    content: str
    variables_schema: Optional[str] = None
    template_settings: List[TemplateSettingDefinition] = []

    @field_validator("template_settings", mode="before")
    @classmethod
    def default_template_settings(cls, v):
        return v or []


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    variables_schema: Optional[str] = None
    template_settings: Optional[List[TemplateSettingDefinition]] = None


class Template(TemplateBase):
    uuid: UUID
    slug: str

    model_config = ConfigDict(
        from_attributes=True,
    )
