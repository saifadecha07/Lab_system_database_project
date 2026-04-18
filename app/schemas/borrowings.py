from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.domain.constants import BorrowingStatus


class BorrowingCreateRequest(BaseModel):
    user_id: int
    equipment_id: int
    expected_return: datetime = Field(description="Expected return timestamp in ISO 8601 format")

    @model_validator(mode="after")
    def validate_expected_return(self):
        if self.expected_return.tzinfo is None:
            raise ValueError("expected_return must include a timezone offset")
        return self


class BorrowingResponse(BaseModel):
    borrow_id: int
    user_id: int
    equipment_id: int
    borrow_time: datetime
    expected_return: datetime
    actual_return: datetime | None
    status: BorrowingStatus

    model_config = {"from_attributes": True}
