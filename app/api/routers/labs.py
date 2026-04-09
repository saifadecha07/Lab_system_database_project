from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models.lab import Lab
from app.db.session import get_db
from app.schemas.labs import LabResponse


router = APIRouter(prefix="/labs", tags=["labs"])


@router.get("", response_model=list[LabResponse])
def list_available_labs(db: Session = Depends(get_db)):
    labs = db.query(Lab).filter(Lab.status == "Available").all()
    return labs

