from sqlalchemy import Boolean, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class Penalty(TimestampMixin, Base):
    __tablename__ = "penalties"

    penalty_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False, index=True)
    borrow_id: Mapped[int] = mapped_column(ForeignKey("equipment_borrowings.borrow_id"), nullable=False, index=True)
    fine_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    borrowing = relationship("EquipmentBorrowing", back_populates="penalties")

