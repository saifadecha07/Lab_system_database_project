from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models.borrowing import EquipmentBorrowing
from app.db.models.equipment import Equipment
from app.db.models.lab import Lab
from app.db.models.maintenance import MaintenanceRecord
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.reports import SummaryReportResponse
from app.security.rbac import require_roles


router = APIRouter(prefix="/staff", tags=["staff"])


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

