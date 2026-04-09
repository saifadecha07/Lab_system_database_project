from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.maintenance import MaintenanceRecord
from app.db.session import get_db
from app.schemas.maintenance import MaintenanceCreateRequest, MaintenanceResponse, MaintenanceUpdateRequest
from app.security.rbac import require_roles
from app.services.maintenance_service import create_maintenance_report, update_maintenance_status


router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.get("/queue", response_model=list[MaintenanceResponse])
def list_queue(_: object = Depends(require_roles("Technician", "Admin")), db: Session = Depends(get_db)):
    return db.query(MaintenanceRecord).all()


@router.post("", response_model=MaintenanceResponse, status_code=201)
def create(payload: MaintenanceCreateRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return create_maintenance_report(db, current_user, payload)


@router.patch("/{repair_id}", response_model=MaintenanceResponse)
def update_status(
    repair_id: int,
    payload: MaintenanceUpdateRequest,
    current_user=Depends(require_roles("Technician", "Admin")),
    db: Session = Depends(get_db),
):
    return update_maintenance_status(db, repair_id, current_user.user_id, payload.status)
