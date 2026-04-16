from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.notification import Notification
from app.db.session import get_db
from app.schemas.notifications import NotificationResponse, NotificationUpdateRequest


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/my", response_model=list[NotificationResponse])
def my_notifications(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Notification).filter(Notification.user_id == current_user.user_id).all()


@router.patch("/{notification_id}", response_model=NotificationResponse)
def update_notification(
    notification_id: int,
    payload: NotificationUpdateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification = (
        db.query(Notification)
        .filter(Notification.notification_id == notification_id, Notification.user_id == current_user.user_id)
        .first()
    )
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    notification.is_read = payload.is_read
    db.commit()
    db.refresh(notification)
    return notification
