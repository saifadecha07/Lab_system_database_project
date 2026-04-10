from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.borrowing import EquipmentBorrowing
from app.db.session import get_db
from app.schemas.borrowings import BorrowingCreateRequest, BorrowingResponse
from app.security.rbac import require_roles
from app.services.borrowing_service import create_borrowing, mark_equipment_returned


router = APIRouter(prefix="/borrowings", tags=["borrowings"])


@router.get("/my", response_model=list[BorrowingResponse])
def my_borrowings(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(EquipmentBorrowing).filter(EquipmentBorrowing.user_id == current_user.user_id).all()


@router.get("", response_model=list[BorrowingResponse])
def list_borrowings(
    status_filter: str | None = None,
    _: object = Depends(require_roles("Staff", "Admin")),
    db: Session = Depends(get_db),
):
    query = db.query(EquipmentBorrowing)
    if status_filter:
        query = query.filter(EquipmentBorrowing.status == status_filter)
    return query.order_by(EquipmentBorrowing.borrow_time.desc()).all()


@router.post("", response_model=BorrowingResponse, status_code=201)
def create(
    payload: BorrowingCreateRequest,
    current_user=Depends(require_roles("Staff", "Admin")),
    db: Session = Depends(get_db),
):
    return create_borrowing(db, current_user.user_id, payload)


@router.patch("/{borrow_id}/return", response_model=BorrowingResponse)
def return_equipment(
    borrow_id: int,
    current_user=Depends(require_roles("Staff", "Admin")),
    db: Session = Depends(get_db),
):
    return mark_equipment_returned(db, borrow_id, current_user.user_id)
