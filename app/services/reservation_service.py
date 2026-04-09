from fastapi import HTTPException, status
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.lab import Lab
from app.db.models.reservation import LabReservation
from app.db.models.user import User
from app.schemas.reservations import ReservationCreateRequest


def create_reservation(db: Session, current_user: User, payload: ReservationCreateRequest) -> LabReservation:
    lab = db.query(Lab).filter(Lab.lab_id == payload.lab_id, Lab.status == "Available").first()
    if not lab:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Available lab not found")

    overlap = (
        db.query(LabReservation)
        .filter(
            LabReservation.lab_id == payload.lab_id,
            LabReservation.status.in_(["Pending", "Approved"]),
            and_(LabReservation.start_time < payload.end_time, LabReservation.end_time > payload.start_time),
        )
        .first()
    )
    if overlap:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Reservation time overlaps existing booking")

    reservation = LabReservation(
        lab_id=payload.lab_id,
        reserved_by=current_user.user_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        status="Pending",
    )
    db.add(reservation)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Reservation time overlaps existing booking",
        ) from exc
    db.refresh(reservation)
    return reservation


def cancel_reservation(db: Session, current_user: User, reservation_id: int) -> LabReservation:
    reservation = db.query(LabReservation).filter(LabReservation.reservation_id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")
    if reservation.reserved_by != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot cancel another user's reservation")

    reservation.status = "Cancelled"
    db.commit()
    db.refresh(reservation)
    return reservation
