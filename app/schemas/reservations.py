from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class ReservationCreateRequest(BaseModel):
    lab_id: int
    start_time: datetime
    end_time: datetime

    @model_validator(mode="after")
    def validate_range(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be greater than start_time")
        return self


class ReservationResponse(BaseModel):
    reservation_id: int
    lab_id: int
    reserved_by: int
    start_time: datetime
    end_time: datetime
    status: str

    model_config = {"from_attributes": True}


class ReservationCancelRequest(BaseModel):
    reason: str = Field(default="User cancelled", max_length=255)

