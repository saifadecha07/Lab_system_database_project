from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, model_validator

BOOKING_TIMEZONE = ZoneInfo("Asia/Bangkok")
FIXED_RESERVATION_SLOTS = (
    {"slot_key": "morning", "label": "08:00-12:00", "start": time(8, 0), "end": time(12, 0)},
    {"slot_key": "afternoon", "label": "12:00-16:00", "start": time(12, 0), "end": time(16, 0)},
    {"slot_key": "evening", "label": "16:00-20:00", "start": time(16, 0), "end": time(20, 0)},
)


def to_booking_timezone(value: datetime) -> datetime:
    if value.tzinfo:
        return value.astimezone(BOOKING_TIMEZONE)
    return value.replace(tzinfo=BOOKING_TIMEZONE)


def resolve_fixed_slot(start_time: datetime, end_time: datetime) -> dict:
    local_start = to_booking_timezone(start_time)
    local_end = to_booking_timezone(end_time)

    if local_end <= local_start:
        raise ValueError("end_time must be greater than start_time")
    if local_start.date() != local_end.date():
        raise ValueError("Reservation must stay within a single day")

    for slot in FIXED_RESERVATION_SLOTS:
        if local_start.time() == slot["start"] and local_end.time() == slot["end"]:
            return slot

    raise ValueError("Reservation must match one of the fixed slots: 08:00-12:00, 12:00-16:00, 16:00-20:00")


class ReservationCreateRequest(BaseModel):
    lab_id: int
    start_time: datetime
    end_time: datetime

    @model_validator(mode="after")
    def validate_range(self):
        resolve_fixed_slot(self.start_time, self.end_time)
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


class ReservationUpdateRequest(BaseModel):
    status: str = Field(min_length=1, max_length=50)


class ReservationSlotAvailability(BaseModel):
    slot_key: str
    label: str
    start_time: datetime
    end_time: datetime
    is_available: bool
    reservation_id: int | None = None


class LabReservationAvailability(BaseModel):
    lab_id: int
    room_name: str
    status: str
    capacity: int
    slots: list[ReservationSlotAvailability]


class ReservationAvailabilityResponse(BaseModel):
    booking_date: date
    timezone: str
    slots: list[dict[str, str]]
    labs: list[LabReservationAvailability]
