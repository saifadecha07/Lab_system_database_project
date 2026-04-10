from datetime import datetime

from pydantic import BaseModel


class SummaryReportResponse(BaseModel):
    total_users: int
    total_labs: int
    total_equipments: int
    active_borrowings: int
    active_repairs: int


# --- Advanced Report Schemas (CN230 Query requirements) ---

class LateBorrowingRow(BaseModel):
    """Query 1: Late borrowings with user, equipment, lab, and penalty details (5-table JOIN)."""
    borrow_id: int
    borrower_name: str
    email: str
    equipment_name: str
    lab_name: str | None
    borrow_time: datetime
    expected_return: datetime
    actual_return: datetime | None
    status: str
    fine_amount: float | None
    hours_late: float | None

    model_config = {"from_attributes": True}


class TopBorrowerRow(BaseModel):
    """Query 2: Users ranked by borrowing activity and total penalties (GROUP BY + HAVING)."""
    user_id: int
    full_name: str
    email: str
    role_name: str
    total_borrowings: int
    penalty_count: int
    total_fines: float

    model_config = {"from_attributes": True}


class LabUtilizationRow(BaseModel):
    """Query 3: Lab utilisation with reservation counts and equipment inventory (4-table JOIN + GROUP BY)."""
    lab_id: int
    room_name: str
    lab_type: str | None
    capacity: int
    status: str
    total_reservations: int
    approved_reservations: int
    equipment_count: int

    model_config = {"from_attributes": True}


class EquipmentRepairRow(BaseModel):
    """Query 4: Equipment ranked by repair frequency with category and location (4-table JOIN + GROUP BY)."""
    equipment_id: int
    equipment_name: str
    current_status: str
    category_name: str | None
    lab_name: str | None
    repair_count: int
    last_reported: datetime | None
    open_repairs: int

    model_config = {"from_attributes": True}


class ReservationSummaryRow(BaseModel):
    """Query 5: Reservation details with participant count and computed duration (4-table JOIN + GROUP BY)."""
    reservation_id: int
    room_name: str
    capacity: int
    reserved_by_name: str
    email: str
    start_time: datetime
    end_time: datetime
    status: str
    participant_count: int
    duration_hours: float

    model_config = {"from_attributes": True}
