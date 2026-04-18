from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class LabType(Base):
    __tablename__ = "lab_types"

    lab_type_id: Mapped[int] = mapped_column(primary_key=True)
    type_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


class Lab(TimestampMixin, Base):
    __tablename__ = "labs"
    __table_args__ = (CheckConstraint("capacity > 0", name="ck_labs_capacity_positive"),)

    lab_id: Mapped[int] = mapped_column(primary_key=True)
    lab_type_id: Mapped[int | None] = mapped_column(ForeignKey("lab_types.lab_type_id"), nullable=True)
    room_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    capacity: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Available", nullable=False, index=True)

    reservations = relationship("LabReservation", back_populates="lab")
    equipments = relationship("Equipment", back_populates="lab")
