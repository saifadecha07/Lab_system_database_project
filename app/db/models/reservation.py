from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class LabReservation(TimestampMixin, Base):
    __tablename__ = "lab_reservations"

    reservation_id: Mapped[int] = mapped_column(primary_key=True)
    lab_id: Mapped[int] = mapped_column(ForeignKey("labs.lab_id"), nullable=False, index=True)
    reserved_by: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False, index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Approved", nullable=False, index=True)

    lab = relationship("Lab", back_populates="reservations")
    reserved_by_user = relationship("User", back_populates="reservations")
    participants = relationship("ReservationParticipant", back_populates="reservation")


class ReservationParticipant(Base):
    __tablename__ = "reservation_participants"

    reservation_id: Mapped[int] = mapped_column(ForeignKey("lab_reservations.reservation_id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), primary_key=True)

    reservation = relationship("LabReservation", back_populates="participants")
