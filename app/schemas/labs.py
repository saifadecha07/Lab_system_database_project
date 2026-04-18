from pydantic import BaseModel, Field

from app.domain.constants import LabStatus


class LabCreateRequest(BaseModel):
    room_name: str = Field(min_length=1, max_length=100)
    capacity: int = Field(gt=0)
    status: LabStatus = LabStatus.AVAILABLE


class LabUpdateRequest(BaseModel):
    room_name: str = Field(min_length=1, max_length=100)
    capacity: int = Field(gt=0)
    status: LabStatus


class LabResponse(BaseModel):
    lab_id: int
    room_name: str
    capacity: int
    status: LabStatus

    model_config = {"from_attributes": True}
