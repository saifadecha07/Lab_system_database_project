from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.borrowing import EquipmentBorrowing
from app.db.session import get_db
from app.security.rbac import require_roles
from app.services.borrowing_service import mark_equipment_returned


router = APIRouter(prefix="/borrowings", tags=["borrowings"])


@router.get("/my")
def my_borrowings(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(EquipmentBorrowing).filter(EquipmentBorrowing.user_id == current_user.user_id).all()


@router.patch("/{borrow_id}/return")
def return_equipment(
    borrow_id: int,
    current_user=Depends(require_roles("Staff", "Admin")),
    db: Session = Depends(get_db),
):
    return mark_equipment_returned(db, borrow_id, current_user.user_id)
