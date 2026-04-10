from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.db.models.borrowing import EquipmentBorrowing
from app.db.models.equipment import Equipment
from app.db.models.lab import Lab
from app.db.models.maintenance import MaintenanceRecord
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.reports import SummaryReportResponse
from app.schemas.users import UserResponse
from app.security.rbac import require_roles


router = APIRouter(prefix="/staff", tags=["staff"])


@router.get("/users", response_model=list[UserResponse])
def list_users(
    _: object = Depends(require_roles("Staff", "Admin")),
    db: Session = Depends(get_db),
):
    users = db.query(User).options(joinedload(User.role)).order_by(User.created_at.desc()).all()
    return [
        UserResponse(
            user_id=user.user_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role_name=user.role.role_name,
            is_active=user.is_active,
            created_at=user.created_at,
        )
        for user in users
    ]


@router.get("/reports/summary", response_model=SummaryReportResponse)
def get_summary_report(
    _: object = Depends(require_roles("Staff", "Admin")),
    db: Session = Depends(get_db),
):
    return SummaryReportResponse(
        total_users=db.query(User).count(),
        total_labs=db.query(Lab).count(),
        total_equipments=db.query(Equipment).count(),
        active_borrowings=db.query(EquipmentBorrowing).filter(EquipmentBorrowing.status == "Borrowed").count(),
        active_repairs=db.query(MaintenanceRecord).filter(MaintenanceRecord.status != "Fixed").count(),
    )
