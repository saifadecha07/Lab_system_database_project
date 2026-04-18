from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class MaintenanceRecord(TimestampMixin, Base):
    __tablename__ = "maintenance_records"

    repair_id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipments.equipment_id"), nullable=False, index=True)
    reported_by: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    technician_id: Mapped[int | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    report_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    issue_detail: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Reported", nullable=False, index=True)
