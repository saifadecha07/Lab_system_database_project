from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.borrowing import EquipmentBorrowing
from app.db.models.equipment import Equipment
from app.services.audit_service import create_audit_log
from app.services.notification_service import create_notification
from app.services.penalty_service import build_penalty


def mark_equipment_returned(db: Session, borrow_id: int, actor_user_id: int) -> EquipmentBorrowing:
    borrowing = db.query(EquipmentBorrowing).filter(EquipmentBorrowing.borrow_id == borrow_id).first()
    if not borrowing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Borrowing not found")
    if borrowing.status != "Borrowed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Borrowing is not active")

    equipment = db.query(Equipment).filter(Equipment.equipment_id == borrowing.equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")

    borrowing.actual_return = datetime.now(timezone.utc)
    borrowing.status = "Returned"
    equipment.status = "Available"

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
