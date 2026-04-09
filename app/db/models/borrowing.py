from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class EquipmentBorrowing(TimestampMixin, Base):
    __tablename__ = "equipment_borrowings"

    borrow_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False, index=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipments.equipment_id"), nullable=False, index=True)
    borrow_time: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    expected_return: Mapped[datetime] = mapped_column(nullable=False)
    actual_return: Mapped[datetime | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="Borrowed", nullable=False, index=True)

    user = relationship("User", back_populates="borrowings")
    equipment = relationship("Equipment", back_populates="borrowings")
    penalties = relationship("Penalty", back_populates="borrowing")

