from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class EquipmentCategory(Base):
    __tablename__ = "equipment_categories"

    category_id: Mapped[int] = mapped_column(primary_key=True)
    category_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


class Equipment(TimestampMixin, Base):
    __tablename__ = "equipments"

    equipment_id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("equipment_categories.category_id"))
    lab_id: Mapped[int | None] = mapped_column(ForeignKey("labs.lab_id"))
    equipment_name: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Available", nullable=False, index=True)

    lab = relationship("Lab", back_populates="equipments")
    borrowings = relationship("EquipmentBorrowing", back_populates="equipment")

