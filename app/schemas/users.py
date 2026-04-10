from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    user_id: int
    email: EmailStr
    first_name: str
    last_name: str
    role_name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateUserRoleRequest(BaseModel):
    role_name: str


class RoleResponse(BaseModel):
    role_id: int
    role_name: str

    model_config = {"from_attributes": True}
