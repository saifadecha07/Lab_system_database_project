from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models.equipment import Equipment
from app.db.session import get_db
from app.schemas.equipments import EquipmentResponse


router = APIRouter(prefix="/equipments", tags=["equipments"])


@router.get("", response_model=list[EquipmentResponse])
def list_available_equipments(db: Session = Depends(get_db)):
    equipments = db.query(Equipment).filter(Equipment.status == "Available").all()
    return equipments

