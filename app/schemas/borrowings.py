from datetime import datetime

from pydantic import BaseModel, Field


class BorrowingCreateRequest(BaseModel):
    user_id: int
    equipment_id: int
    expected_return: datetime = Field(description="Expected return timestamp in ISO 8601 format")


class BorrowingResponse(BaseModel):
    borrow_id: int
    user_id: int
    equipment_id: int
    borrow_time: datetime
    expected_return: datetime
    actual_return: datetime | None
    status: str

    model_config = {"from_attributes": True}
