from pydantic import BaseModel


class SummaryReportResponse(BaseModel):
    total_users: int
    total_labs: int
    total_equipments: int
    active_borrowings: int
    active_repairs: int
