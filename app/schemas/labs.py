from pydantic import BaseModel, Field


class LabCreateRequest(BaseModel):
    room_name: str = Field(min_length=1, max_length=100)
    capacity: int = Field(gt=0)
    status: str = Field(default="Available", min_length=1, max_length=50)


class LabUpdateRequest(BaseModel):
    room_name: str = Field(min_length=1, max_length=100)
    capacity: int = Field(gt=0)
    status: str = Field(min_length=1, max_length=50)


class LabResponse(BaseModel):
    lab_id: int
    room_name: str
    capacity: int
    status: str

    model_config = {"from_attributes": True}
