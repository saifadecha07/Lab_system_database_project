from enum import Enum


class LabStatus(str, Enum):
    AVAILABLE = "Available"
    RESERVED = "Reserved"
    MAINTENANCE = "Maintenance"
    CLOSED = "Closed"


class EquipmentStatus(str, Enum):
    AVAILABLE = "Available"
    BORROWED = "Borrowed"
    IN_REPAIR = "In_Repair"


class BorrowingStatus(str, Enum):
    BORROWED = "Borrowed"
    RETURNED = "Returned"


class MaintenanceStatus(str, Enum):
    REPORTED = "Reported"
    IN_PROGRESS = "In Progress"
    FIXED = "Fixed"


class ReservationStatus(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    CANCELLED = "Cancelled"
