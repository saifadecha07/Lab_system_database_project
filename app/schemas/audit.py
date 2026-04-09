from datetime import datetime

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    audit_log_id: int
    actor_user_id: int | None
    action: str
    target_type: str
    target_id: int | None
    details: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}
