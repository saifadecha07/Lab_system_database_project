"""
Advanced Report Endpoints — CN230 Database Systems Project
==========================================================
Five complex SQL queries demonstrating:
  Q1  late_borrowings       — 5-table JOIN (equipment_borrowings, users, equipments, labs, penalties)
  Q2  top_borrowers         — 4-table JOIN + GROUP BY + HAVING + aggregate functions
  Q3  lab_utilization       — 4-table JOIN + GROUP BY + conditional COUNT (CASE)
  Q4  equipment_repairs     — 4-table JOIN + GROUP BY + conditional COUNT
  Q5  reservation_summary   — 4-table JOIN + GROUP BY + computed column (EXTRACT)
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.reports import (
    EquipmentRepairRow,
    LabUtilizationRow,
    LateBorrowingRow,
    ReservationSummaryRow,
    TopBorrowerRow,
)
from app.security.rbac import require_roles

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/late-borrowings", response_model=list[LateBorrowingRow])
def late_borrowings_report(
    _: object = Depends(require_roles("Staff", "Admin")),
    db: Session = Depends(get_db),
):
    """
    Query 1 — Late Borrowings
    -------------------------
    Returns every borrowing where the item was (or still is) returned late,
    joined with borrower info, equipment name, lab location, and any penalty.

    Tables: equipment_borrowings ⟶ users ⟶ equipments ⟶ labs ⟶ penalties
    Key SQL:  JOIN + LEFT JOIN + WHERE with OR condition
    """
    sql = text("""
        SELECT
            eb.borrow_id,
            u.first_name || ' ' || u.last_name                        AS borrower_name,
            u.email,
            e.equipment_name,
            l.room_name                                                AS lab_name,
            eb.borrow_time,
            eb.expected_return,
            eb.actual_return,
            eb.status,
            p.fine_amount,
            ROUND(
                EXTRACT(EPOCH FROM (
                    COALESCE(eb.actual_return, NOW()) - eb.expected_return
                )) / 3600.0
            , 2)                                                       AS hours_late
        FROM  equipment_borrowings  eb
        JOIN  users                 u   ON u.user_id      = eb.user_id
        JOIN  equipments            e   ON e.equipment_id = eb.equipment_id
        LEFT JOIN labs              l   ON l.lab_id       = e.lab_id
        LEFT JOIN penalties         p   ON p.borrow_id    = eb.borrow_id
        WHERE eb.actual_return > eb.expected_return
           OR (eb.actual_return IS NULL AND eb.expected_return < NOW())
        ORDER BY eb.expected_return ASC
    """)
    rows = db.execute(sql).mappings().all()
    return [LateBorrowingRow(**row) for row in rows]


@router.get("/top-borrowers", response_model=list[TopBorrowerRow])
def top_borrowers_report(
    _: object = Depends(require_roles("Staff", "Admin")),
    db: Session = Depends(get_db),
):
    """
    Query 2 — Top Borrowers with Penalty Summary
    ---------------------------------------------
    Ranks every user who has at least one borrowing by total fine amount,
    grouped by user and role.

    Tables: users ⟶ roles ⟶ equipment_borrowings ⟶ penalties
    Key SQL:  GROUP BY + HAVING COUNT(...) > 0 + SUM + COUNT(DISTINCT ...)
    """
    sql = text("""
        SELECT
            u.user_id,
            u.first_name || ' ' || u.last_name  AS full_name,
            u.email,
            r.role_name,
            COUNT(DISTINCT eb.borrow_id)         AS total_borrowings,
            COUNT(DISTINCT p.penalty_id)         AS penalty_count,
            COALESCE(SUM(p.fine_amount), 0)      AS total_fines
        FROM  users                 u
        JOIN  roles                 r   ON r.role_id  = u.role_id
        LEFT JOIN equipment_borrowings eb ON eb.user_id = u.user_id
        LEFT JOIN penalties         p   ON p.user_id  = u.user_id
        GROUP BY u.user_id, u.first_name, u.last_name, u.email, r.role_name
        HAVING COUNT(DISTINCT eb.borrow_id) > 0
        ORDER BY total_fines DESC, total_borrowings DESC
    """)
    rows = db.execute(sql).mappings().all()
    return [TopBorrowerRow(**row) for row in rows]


@router.get("/lab-utilization", response_model=list[LabUtilizationRow])
def lab_utilization_report(
    _: object = Depends(require_roles("Staff", "Admin")),
    db: Session = Depends(get_db),
):
    """
    Query 3 — Lab Utilisation
    -------------------------
    Shows every lab with its type, total/approved reservation counts, and
    equipment inventory size to assess how heavily each room is used.

    Tables: labs ⟶ lab_types ⟶ lab_reservations ⟶ equipments
    Key SQL:  GROUP BY + COUNT(DISTINCT ...) + conditional COUNT (CASE WHEN)
    """
    sql = text("""
        SELECT
            l.lab_id,
            l.room_name,
            lt.type_name                                               AS lab_type,
            l.capacity,
            l.status,
            COUNT(DISTINCT lr.reservation_id)                          AS total_reservations,
            COUNT(DISTINCT CASE WHEN lr.status = 'Approved'
                           THEN lr.reservation_id END)                 AS approved_reservations,
            COUNT(DISTINCT e.equipment_id)                             AS equipment_count
        FROM  labs              l
        LEFT JOIN lab_types         lt ON lt.lab_type_id = l.lab_type_id
        LEFT JOIN lab_reservations  lr ON lr.lab_id      = l.lab_id
        LEFT JOIN equipments        e  ON e.lab_id       = l.lab_id
        GROUP BY l.lab_id, l.room_name, lt.type_name, l.capacity, l.status
        ORDER BY total_reservations DESC, l.room_name ASC
    """)
    rows = db.execute(sql).mappings().all()
    return [LabUtilizationRow(**row) for row in rows]


@router.get("/equipment-repairs", response_model=list[EquipmentRepairRow])
def equipment_repairs_report(
    _: object = Depends(require_roles("Staff", "Admin")),
    db: Session = Depends(get_db),
):
    """
    Query 4 — Equipment Repair Frequency
    -------------------------------------
    Ranks every piece of equipment by total repair events and shows how many
    repair tickets are still open, along with category and lab location.

    Tables: equipments ⟶ equipment_categories ⟶ labs ⟶ maintenance_records
    Key SQL:  GROUP BY + COUNT + MAX + conditional COUNT (CASE WHEN)
    """
    sql = text("""
        SELECT
            e.equipment_id,
            e.equipment_name,
            e.status                                                   AS current_status,
            ec.category_name,
            l.room_name                                                AS lab_name,
            COUNT(mr.repair_id)                                        AS repair_count,
            MAX(mr.report_date)                                        AS last_reported,
            COUNT(CASE WHEN mr.status != 'Fixed' THEN 1 END)          AS open_repairs
        FROM  equipments            e
        LEFT JOIN equipment_categories ec ON ec.category_id = e.category_id
        LEFT JOIN labs               l   ON l.lab_id        = e.lab_id
        LEFT JOIN maintenance_records mr  ON mr.equipment_id = e.equipment_id
        GROUP BY e.equipment_id, e.equipment_name, e.status,
                 ec.category_name, l.room_name
        ORDER BY repair_count DESC, e.equipment_name ASC
    """)
    rows = db.execute(sql).mappings().all()
    return [EquipmentRepairRow(**row) for row in rows]


@router.get("/reservation-summary", response_model=list[ReservationSummaryRow])
def reservation_summary_report(
    _: object = Depends(require_roles("Staff", "Admin")),
    db: Session = Depends(get_db),
):
    """
    Query 5 — Reservation Details with Participant Headcount
    ---------------------------------------------------------
    Lists every reservation with the lab name, booker details, participant
    count, and computed session duration in hours.

    Tables: lab_reservations ⟶ labs ⟶ users ⟶ reservation_participants
    Key SQL:  GROUP BY + COUNT + EXTRACT(EPOCH ...) computed column
    """
    sql = text("""
        SELECT
            lr.reservation_id,
            l.room_name,
            l.capacity,
            u.first_name || ' ' || u.last_name                        AS reserved_by_name,
            u.email,
            lr.start_time,
            lr.end_time,
            lr.status,
            COUNT(rp.user_id)                                          AS participant_count,
            ROUND(
                EXTRACT(EPOCH FROM (lr.end_time - lr.start_time)) / 3600.0
            , 2)                                                       AS duration_hours
        FROM  lab_reservations      lr
        JOIN  labs                  l   ON l.lab_id  = lr.lab_id
        JOIN  users                 u   ON u.user_id = lr.reserved_by
        LEFT JOIN reservation_participants rp ON rp.reservation_id = lr.reservation_id
        GROUP BY lr.reservation_id, l.room_name, l.capacity,
                 u.first_name, u.last_name, u.email,
                 lr.start_time, lr.end_time, lr.status
        ORDER BY lr.start_time DESC
    """)
    rows = db.execute(sql).mappings().all()
    return [ReservationSummaryRow(**row) for row in rows]
