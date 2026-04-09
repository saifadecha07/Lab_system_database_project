from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.db.models.role import Role
from app.db.models.user import User
from app.schemas.auth import RegisterRequest
from app.security.hashing import hash_password, verify_password


def get_or_create_default_student_role(db: Session) -> Role:
    role = db.query(Role).filter(Role.role_name == "Student").first()
    if role:
        return role

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Default role is missing. Run database migrations and seed roles.",
    )


def register_user(db: Session, payload: RegisterRequest) -> User:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    student_role = get_or_create_default_student_role(db)
    user = User(
        role_id=student_role.role_id,
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).options(joinedload(User.role)).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive account")
    return user
