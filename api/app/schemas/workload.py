from pydantic import BaseModel, ConfigDict
from uuid import UUID


class WorkloadBase(BaseModel):
    name: str


class WorkloadCreate(WorkloadBase):
    pass


class Workload(WorkloadBase):
    uuid: UUID

    model_config = ConfigDict(
        from_attributes=True,
    )
