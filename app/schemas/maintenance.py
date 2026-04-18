from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.constants import MaintenanceStatus


class MaintenanceCreateRequest(BaseModel):
    equipment_id: int
    issue_detail: str = Field(min_length=5)


class MaintenanceUpdateRequest(BaseModel):
    status: MaintenanceStatus


class MaintenanceResponse(BaseModel):
    repair_id: int
    equipment_id: int
    reported_by: int
    technician_id: int | None
    report_date: datetime
    resolved_date: datetime | None
    issue_detail: str
    status: MaintenanceStatus

    model_config = {"from_attributes": True}
