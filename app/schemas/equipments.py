from pydantic import BaseModel, Field

from app.domain.constants import EquipmentStatus


class EquipmentCreateRequest(BaseModel):
    equipment_name: str = Field(min_length=1, max_length=150)
    lab_id: int | None = None
    category_id: int | None = None
    status: EquipmentStatus = EquipmentStatus.AVAILABLE


class EquipmentUpdateRequest(BaseModel):
    equipment_name: str = Field(min_length=1, max_length=150)
    lab_id: int | None = None
    category_id: int | None = None
    status: EquipmentStatus


class EquipmentResponse(BaseModel):
    equipment_id: int
    equipment_name: str
    lab_id: int | None
    category_id: int | None
    status: EquipmentStatus

    model_config = {"from_attributes": True}
