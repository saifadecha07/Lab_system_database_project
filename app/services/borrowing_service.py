from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.borrowing import EquipmentBorrowing
from app.db.models.equipment import Equipment
from app.db.models.user import User
from app.domain.constants import BorrowingStatus, EquipmentStatus
from app.schemas.borrowings import BorrowingCreateRequest
from app.services.audit_service import create_audit_log
from app.services.equipment_state_service import has_active_borrowing, has_open_maintenance, resolve_equipment_status
from app.services.notification_service import create_notification
from app.services.penalty_service import build_penalty


def create_borrowing(db: Session, actor_user_id: int, payload: BorrowingCreateRequest) -> EquipmentBorrowing:
    borrower = db.query(User).filter(User.user_id == payload.user_id, User.is_active.is_(True)).first()
    if not borrower:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Borrower not found")

    equipment = (
        db.query(Equipment)
        .filter(Equipment.equipment_id == payload.equipment_id)
        .with_for_update()
        .first()
    )
    if not equipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    if equipment.status != EquipmentStatus.AVAILABLE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Equipment is not available")
    if has_active_borrowing(db, payload.equipment_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Equipment already has an active borrowing")
    if has_open_maintenance(db, payload.equipment_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Equipment is under maintenance")
    if payload.expected_return <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Expected return must be in the future")

    borrowing = EquipmentBorrowing(
        user_id=payload.user_id,
        equipment_id=payload.equipment_id,
        expected_return=payload.expected_return,
        status=BorrowingStatus.BORROWED,
    )
    db.add(borrowing)
    db.flush()
    equipment.status = resolve_equipment_status(db, equipment.equipment_id)
    create_audit_log(
        db,
        "equipment.borrowed",
        "borrowing",
        actor_user_id=actor_user_id,
        target_id=borrowing.borrow_id,
        details={"borrower_user_id": borrowing.user_id, "equipment_id": borrowing.equipment_id, "status": borrowing.status},
    )
    db.commit()
    db.refresh(borrowing)
    return borrowing


def mark_equipment_returned(db: Session, borrow_id: int, actor_user_id: int) -> EquipmentBorrowing:
    borrowing = db.query(EquipmentBorrowing).filter(EquipmentBorrowing.borrow_id == borrow_id).first()
    if not borrowing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Borrowing not found")
    if borrowing.status != BorrowingStatus.BORROWED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Borrowing is not active")

    equipment = (
        db.query(Equipment)
        .filter(Equipment.equipment_id == borrowing.equipment_id)
        .with_for_update()
        .first()
    )
    if not equipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")

    borrowing.actual_return = datetime.now(timezone.utc)
    borrowing.status = BorrowingStatus.RETURNED
    equipment.status = resolve_equipment_status(db, equipment.equipment_id)

    penalty = build_penalty(
        user_id=borrowing.user_id,
        borrow_id=borrowing.borrow_id,
        expected_return=borrowing.expected_return,
        actual_return=borrowing.actual_return,
    )
    if penalty:
        db.add(penalty)
        create_notification(
            db,
            borrowing.user_id,
            f"A penalty of {penalty.fine_amount:.2f} has been created for late return.",
        )
    create_audit_log(
        db,
        "equipment.returned",
        "borrowing",
        actor_user_id=actor_user_id,
        target_id=borrowing.borrow_id,
        details={"borrower_user_id": borrowing.user_id, "equipment_id": borrowing.equipment_id, "status": borrowing.status},
    )

    db.commit()
    db.refresh(borrowing)
    return borrowing
