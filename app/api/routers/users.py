from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.schemas.users import UserResponse


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user=Depends(get_current_user)):
    return UserResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role_name=current_user.role.role_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )

