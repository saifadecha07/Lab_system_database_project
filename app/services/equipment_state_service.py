from sqlalchemy.orm import Session

from app.db.models.borrowing import EquipmentBorrowing
from app.db.models.maintenance import MaintenanceRecord
from app.domain.constants import BorrowingStatus, EquipmentStatus, MaintenanceStatus


def has_active_borrowing(db: Session, equipment_id: int) -> bool:
    return (
        db.query(EquipmentBorrowing)
        .filter(
            EquipmentBorrowing.equipment_id == equipment_id,
            EquipmentBorrowing.status == BorrowingStatus.BORROWED,
        )
        .first()
        is not None
    )


def has_open_maintenance(db: Session, equipment_id: int) -> bool:
    return (
        db.query(MaintenanceRecord)
        .filter(
            MaintenanceRecord.equipment_id == equipment_id,
            MaintenanceRecord.status != MaintenanceStatus.FIXED,
        )
        .first()
        is not None
    )


def resolve_equipment_status(db: Session, equipment_id: int) -> EquipmentStatus:
    if has_active_borrowing(db, equipment_id):
        return EquipmentStatus.BORROWED
    if has_open_maintenance(db, equipment_id):
        return EquipmentStatus.IN_REPAIR
    return EquipmentStatus.AVAILABLE
