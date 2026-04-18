from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.equipment import Equipment
from app.db.models.maintenance import MaintenanceRecord
from app.db.models.user import User
from app.domain.constants import MaintenanceStatus
from app.schemas.maintenance import MaintenanceCreateRequest
from app.services.audit_service import create_audit_log
from app.services.equipment_state_service import resolve_equipment_status
from app.services.notification_service import create_notification


def create_maintenance_report(db: Session, current_user: User, payload: MaintenanceCreateRequest) -> MaintenanceRecord:
    equipment = (
        db.query(Equipment)
        .filter(Equipment.equipment_id == payload.equipment_id)
        .with_for_update()
        .first()
    )
    if not equipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")

    record = MaintenanceRecord(
        equipment_id=payload.equipment_id,
        reported_by=current_user.user_id,
        issue_detail=payload.issue_detail,
        status=MaintenanceStatus.REPORTED,
    )
    db.add(record)
    db.flush()
    equipment.status = resolve_equipment_status(db, equipment.equipment_id)
    create_audit_log(
        db,
        "maintenance.reported",
        "maintenance",
        actor_user_id=current_user.user_id,
        target_id=record.repair_id,
        details={"equipment_id": payload.equipment_id, "status": record.status},
    )
    db.commit()
    db.refresh(record)
    return record


def update_maintenance_status(db: Session, repair_id: int, technician_id: int, new_status: str) -> MaintenanceRecord:
    record = db.query(MaintenanceRecord).filter(MaintenanceRecord.repair_id == repair_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance record not found")

    equipment = (
        db.query(Equipment)
        .filter(Equipment.equipment_id == record.equipment_id)
        .with_for_update()
        .first()
    )
    if not equipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")

    record.technician_id = technician_id
    record.status = new_status
    if new_status == MaintenanceStatus.FIXED:
        record.resolved_date = datetime.now(timezone.utc)
        create_notification(db, record.reported_by, "Your maintenance request has been completed.")
    else:
        record.resolved_date = None
    equipment.status = resolve_equipment_status(db, equipment.equipment_id)
    create_audit_log(
        db,
        "maintenance.updated",
        "maintenance",
        actor_user_id=technician_id,
        target_id=record.repair_id,
        details={"equipment_id": record.equipment_id, "status": new_status},
    )

    db.commit()
    db.refresh(record)
    return record
