from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import get_settings
from app.db.session import get_db
from app.schemas.auth import LoginRequest, MessageResponse, RegisterRequest
from app.schemas.users import UserResponse
from app.security.rate_limit import limiter
from app.security.session import clear_user_session, start_user_session
from app.services.auth_service import authenticate_user, register_user


settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = register_user(db, payload)
    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role_name="Student",
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/login", response_model=MessageResponse)
@limiter.limit(settings.rate_limit_login)
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.email, payload.password)
    start_user_session(request, user.user_id)
    return MessageResponse(message="Login successful")


@router.post("/logout", response_model=MessageResponse)
def logout(request: Request, response: Response):
    clear_user_session(request, response, settings.session_cookie_name)
    return MessageResponse(message="Logout successful")


@router.get("/me", response_model=UserResponse)
def me(current_user=Depends(get_current_user)):
    return UserResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role_name=current_user.role.role_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )
