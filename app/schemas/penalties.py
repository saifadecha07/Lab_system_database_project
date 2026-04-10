from datetime import datetime

from pydantic import BaseModel


class PenaltyResponse(BaseModel):
    penalty_id: int
    user_id: int
    borrow_id: int
    fine_amount: float
    is_resolved: bool
    created_at: datetime

    model_config = {"from_attributes": True}
