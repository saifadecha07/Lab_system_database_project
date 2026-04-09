from fastapi import Depends, HTTPException, status

from app.api.deps import get_current_user
from app.db.models.user import User


def require_roles(*role_names: str):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        current_role = current_user.role.role_name if current_user.role else None
        if current_role not in role_names:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return dependency

