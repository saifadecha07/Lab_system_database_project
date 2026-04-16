from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.reservation import LabReservation
from app.db.session import get_db
from app.schemas.auth import MessageResponse
from app.schemas.reservations import (
    ReservationAvailabilityResponse,
    ReservationCreateRequest,
    ReservationResponse,
    ReservationUpdateRequest,
)
from app.security.rbac import require_roles
from app.services.reservation_service import cancel_reservation, create_reservation, get_reservation_availability


router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.get("/my", response_model=list[ReservationResponse])
def list_my_reservations(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(LabReservation).filter(LabReservation.reserved_by == current_user.user_id).all()


@router.get("", response_model=list[ReservationResponse])
def list_all_reservations(
    _: object = Depends(require_roles("Staff", "Admin")),
    db: Session = Depends(get_db),
):
    return db.query(LabReservation).order_by(LabReservation.start_time.desc()).all()


@router.get("/availability", response_model=ReservationAvailabilityResponse)
def availability(booking_date: date, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return get_reservation_availability(db, booking_date)


@router.post("", response_model=ReservationResponse, status_code=201)
def create(payload: ReservationCreateRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return create_reservation(db, current_user, payload)


@router.post("/{reservation_id}/cancel", response_model=ReservationResponse)
def cancel(reservation_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return cancel_reservation(db, current_user, reservation_id)


@router.patch("/{reservation_id}", response_model=ReservationResponse)
def update_reservation(
    reservation_id: int,
    payload: ReservationUpdateRequest,
    _: object = Depends(require_roles("Admin")),
    db: Session = Depends(get_db),
):
    reservation = db.query(LabReservation).filter(LabReservation.reservation_id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")

    reservation.status = payload.status
    db.commit()
    db.refresh(reservation)
    return reservation


@router.delete("/{reservation_id}", response_model=MessageResponse)
def delete_reservation(
    reservation_id: int,
    _: object = Depends(require_roles("Admin")),
    db: Session = Depends(get_db),
):
    reservation = db.query(LabReservation).filter(LabReservation.reservation_id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")

    db.delete(reservation)
    db.commit()
    return MessageResponse(message="Reservation deleted")
