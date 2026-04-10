from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.notification import Notification
from app.db.session import get_db
from app.schemas.notifications import NotificationResponse


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/my", response_model=list[NotificationResponse])
def my_notifications(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Notification).filter(Notification.user_id == current_user.user_id).all()
