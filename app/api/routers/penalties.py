from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.penalty import Penalty
from app.db.session import get_db
from app.schemas.penalties import PenaltyResponse


router = APIRouter(prefix="/penalties", tags=["penalties"])


@router.get("/my", response_model=list[PenaltyResponse])
def my_penalties(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Penalty).filter(Penalty.user_id == current_user.user_id).all()
