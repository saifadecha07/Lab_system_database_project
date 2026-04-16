from datetime import datetime

from pydantic import BaseModel


class NotificationUpdateRequest(BaseModel):
    is_read: bool = True


class NotificationResponse(BaseModel):
    notification_id: int
    user_id: int
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}
