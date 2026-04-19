from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.lab import Lab
from app.db.models.reservation import LabReservation
from app.db.models.user import User
from app.schemas.reservations import (
    BOOKING_TIMEZONE,
    FIXED_RESERVATION_SLOTS,
    ReservationAvailabilityResponse,
    ReservationCreateRequest,
    to_utc_timezone,
)


def _normalize_for_compare(value: datetime) -> datetime:
    if value.tzinfo:
        return value.astimezone(BOOKING_TIMEZONE)
    return value.replace(tzinfo=timezone.utc).astimezone(BOOKING_TIMEZONE)


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
        start_time=to_utc_timezone(payload.start_time),
        end_time=to_utc_timezone(payload.end_time),
        status="Approved",
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


def get_reservation_availability(db: Session, booking_date: date) -> ReservationAvailabilityResponse:
    labs = db.query(Lab).order_by(Lab.room_name.asc()).all()
    reservations = (
        db.query(LabReservation)
        .filter(LabReservation.status.in_(["Pending", "Approved"]))
        .all()
    )

    reservations_by_lab: dict[int, list[LabReservation]] = {}
    for reservation in reservations:
        reservations_by_lab.setdefault(reservation.lab_id, []).append(reservation)

    lab_rows = []
    for lab in labs:
        slot_rows = []
        for slot in FIXED_RESERVATION_SLOTS:
            slot_start = datetime.combine(booking_date, slot["start"], tzinfo=BOOKING_TIMEZONE)
            slot_end = datetime.combine(booking_date, slot["end"], tzinfo=BOOKING_TIMEZONE)
            reserved = next(
                (
                    item
                    for item in reservations_by_lab.get(lab.lab_id, [])
                    if _normalize_for_compare(item.start_time) < slot_end
                    and _normalize_for_compare(item.end_time) > slot_start
                ),
                None,
            )
            slot_rows.append(
                {
                    "slot_key": slot["slot_key"],
                    "label": slot["label"],
                    "start_time": slot_start.astimezone(BOOKING_TIMEZONE),
                    "end_time": slot_end.astimezone(BOOKING_TIMEZONE),
                    "is_available": reserved is None and lab.status == "Available",
                    "reservation_id": reserved.reservation_id if reserved else None,
                }
            )

        lab_rows.append(
            {
                "lab_id": lab.lab_id,
                "room_name": lab.room_name,
                "status": lab.status,
                "capacity": lab.capacity,
                "slots": slot_rows,
            }
        )

    return ReservationAvailabilityResponse(
        booking_date=booking_date,
        timezone="Asia/Bangkok",
        slots=[{"slot_key": slot["slot_key"], "label": slot["label"]} for slot in FIXED_RESERVATION_SLOTS],
        labs=lab_rows,
    )


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
