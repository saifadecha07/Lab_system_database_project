from pydantic import BaseModel, Field


class EquipmentCreateRequest(BaseModel):
    equipment_name: str = Field(min_length=1, max_length=150)
    lab_id: int | None = None
    category_id: int | None = None
    status: str = Field(default="Available", min_length=1, max_length=50)


class EquipmentUpdateRequest(BaseModel):
    equipment_name: str = Field(min_length=1, max_length=150)
    lab_id: int | None = None
    category_id: int | None = None
    status: str = Field(min_length=1, max_length=50)


class EquipmentResponse(BaseModel):
    equipment_id: int
    equipment_name: str
    lab_id: int | None
    category_id: int | None
    status: str

    model_config = {"from_attributes": True}
