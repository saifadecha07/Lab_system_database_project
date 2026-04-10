"""
Demo Data Seeder — Smart Lab Management System
================================================
Run from the project root:
    python scripts/seed_demo.py

Creates demo accounts and sample records in the PostgreSQL database.
All demo users share the password:  Demo@1234567890

Demo accounts created
---------------------
Role         Email                        Password
-----------  ---------------------------  -------------------
Admin        admin@lab.demo               Demo@1234567890
Staff        staff@lab.demo               Demo@1234567890
Technician   tech@lab.demo                Demo@1234567890
Student      alice@lab.demo               Demo@1234567890
Student      bob@lab.demo                 Demo@1234567890
Student      carol@lab.demo               Demo@1234567890
Student      dave@lab.demo                Demo@1234567890
Student      eve@lab.demo                 Demo@1234567890
"""

import os
import sys
from datetime import datetime, timedelta, timezone

# Make sure the project root is on sys.path when run from anywhere
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv                                  # noqa: E402
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from app.db.base import Base                                    # noqa: E402
from app.db.session import SessionLocal, engine                 # noqa: E402
import app.db.models                                            # noqa: E402, F401  (register all models)
from app.db.models.audit_log import AuditLog                    # noqa: E402
from app.db.models.borrowing import EquipmentBorrowing          # noqa: E402
from app.db.models.equipment import Equipment, EquipmentCategory # noqa: E402
from app.db.models.lab import Lab, LabType                      # noqa: E402
from app.db.models.maintenance import MaintenanceRecord         # noqa: E402
from app.db.models.notification import Notification             # noqa: E402
from app.db.models.penalty import Penalty                       # noqa: E402
from app.db.models.reservation import LabReservation, ReservationParticipant  # noqa: E402
from app.db.models.role import Role                             # noqa: E402
from app.db.models.user import User                             # noqa: E402
from app.security.hashing import hash_password                  # noqa: E402

DEMO_PASSWORD = "Demo@1234567890"
NOW = datetime.now(timezone.utc)


def get_or_create(db, model, defaults=None, **kwargs):
    instance = db.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    params = {**kwargs, **(defaults or {})}
    instance = model(**params)
    db.add(instance)
    db.flush()
    return instance, True


def seed(db):
    print("── Ensuring tables exist …")
    Base.metadata.create_all(bind=engine)

    # ------------------------------------------------------------------
    # Roles
    # ------------------------------------------------------------------
    print("── Seeding roles …")
    for name in ("Student", "Staff", "Technician", "Admin"):
        get_or_create(db, Role, role_name=name)
    db.flush()

    def role(name):
        return db.query(Role).filter_by(role_name=name).one()

    # ------------------------------------------------------------------
    # Lab Types
    # ------------------------------------------------------------------
    print("── Seeding lab types …")
    for t in ("Computer Lab", "Science Lab", "General Purpose", "Electronics Lab"):
        get_or_create(db, LabType, type_name=t)
    db.flush()

    def lab_type(name):
        return db.query(LabType).filter_by(type_name=name).one()

    # ------------------------------------------------------------------
    # Equipment Categories
    # ------------------------------------------------------------------
    print("── Seeding equipment categories …")
    for c in ("Computer", "Microscope", "Chemistry Equipment", "Electronics", "Projector / AV"):
        get_or_create(db, EquipmentCategory, category_name=c)
    db.flush()

    def cat(name):
        return db.query(EquipmentCategory).filter_by(category_name=name).one()

    # ------------------------------------------------------------------
    # Labs
    # ------------------------------------------------------------------
    print("── Seeding labs …")
    labs_data = [
        ("CS-101", 30, "Available",    lab_type("Computer Lab")),
        ("CS-102", 30, "Available",    lab_type("Computer Lab")),
        ("SCI-201", 20, "Available",   lab_type("Science Lab")),
        ("GP-301",  40, "Available",   lab_type("General Purpose")),
        ("EL-401",  15, "Maintenance", lab_type("Electronics Lab")),
    ]
    lab_objs = {}
    for room_name, capacity, status, lt in labs_data:
        obj, _ = get_or_create(
            db, Lab,
            defaults=dict(capacity=capacity, status=status, lab_type_id=lt.lab_type_id),
            room_name=room_name,
        )
        lab_objs[room_name] = obj
    db.flush()

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------
    print("── Seeding users …")
    users_data = [
        ("Admin",      "admin@lab.demo",  "Adam",  "Admin"),
        ("Staff",      "staff@lab.demo",  "Sara",  "Staff"),
        ("Technician", "tech@lab.demo",   "Tom",   "Tech"),
        ("Student",    "alice@lab.demo",  "Alice", "Tonkla"),
        ("Student",    "bob@lab.demo",    "Bob",   "Salee"),
        ("Student",    "carol@lab.demo",  "Carol", "Manee"),
        ("Student",    "dave@lab.demo",   "Dave",  "Somchai"),
        ("Student",    "eve@lab.demo",    "Eve",   "Wanida"),
    ]
    user_objs = {}
    for role_name, email, first, last in users_data:
        obj, created = get_or_create(
            db, User,
            defaults=dict(
                role_id=role(role_name).role_id,
                first_name=first,
                last_name=last,
                password_hash=hash_password(DEMO_PASSWORD),
                is_active=True,
            ),
            email=email,
        )
        if created:
            print(f"   Created {role_name}: {email}")
        user_objs[email] = obj
    db.flush()

    admin_user  = user_objs["admin@lab.demo"]
    staff_user  = user_objs["staff@lab.demo"]
    tech_user   = user_objs["tech@lab.demo"]
    alice       = user_objs["alice@lab.demo"]
    bob         = user_objs["bob@lab.demo"]
    carol       = user_objs["carol@lab.demo"]
    dave        = user_objs["dave@lab.demo"]
    eve         = user_objs["eve@lab.demo"]

    # ------------------------------------------------------------------
    # Equipment
    # ------------------------------------------------------------------
    print("── Seeding equipment …")
    equip_data = [
        ("PC-Workstation-01", cat("Computer"),            lab_objs["CS-101"],  "Available"),
        ("PC-Workstation-02", cat("Computer"),            lab_objs["CS-101"],  "Available"),
        ("PC-Workstation-03", cat("Computer"),            lab_objs["CS-102"],  "Borrowed"),
        ("Projector-A",       cat("Projector / AV"),      lab_objs["GP-301"],  "Available"),
        ("Oscilloscope-01",   cat("Electronics"),         lab_objs["EL-401"],  "In_Repair"),
        ("Oscilloscope-02",   cat("Electronics"),         lab_objs["EL-401"],  "Available"),
        ("Microscope-01",     cat("Microscope"),          lab_objs["SCI-201"], "Available"),
        ("Microscope-02",     cat("Microscope"),          lab_objs["SCI-201"], "Borrowed"),
        ("Bunsen-Burner-01",  cat("Chemistry Equipment"), lab_objs["SCI-201"], "Available"),
        ("Bunsen-Burner-02",  cat("Chemistry Equipment"), lab_objs["SCI-201"], "Available"),
    ]
    equip_objs = {}
    for name, category, lab, status in equip_data:
        obj, _ = get_or_create(
            db, Equipment,
            defaults=dict(
                category_id=category.category_id,
                lab_id=lab.lab_id,
                status=status,
            ),
            equipment_name=name,
        )
        equip_objs[name] = obj
    db.flush()

    # ------------------------------------------------------------------
    # Lab Reservations
    # ------------------------------------------------------------------
    print("── Seeding lab reservations …")
    reservations_data = [
        (alice, lab_objs["CS-101"],  NOW + timedelta(days=1),  NOW + timedelta(days=1, hours=2),  "Approved"),
        (bob,   lab_objs["CS-102"],  NOW + timedelta(days=2),  NOW + timedelta(days=2, hours=3),  "Pending"),
        (carol, lab_objs["SCI-201"], NOW - timedelta(days=1),  NOW - timedelta(hours=22),         "Approved"),
        (dave,  lab_objs["GP-301"],  NOW + timedelta(days=3),  NOW + timedelta(days=3, hours=4),  "Approved"),
        (eve,   lab_objs["CS-101"],  NOW - timedelta(days=3),  NOW - timedelta(days=3) + timedelta(hours=2), "Cancelled"),
        (alice, lab_objs["GP-301"],  NOW + timedelta(days=5),  NOW + timedelta(days=5, hours=1),  "Pending"),
    ]
    res_objs = []
    for user, lab, start, end, status in reservations_data:
        res = LabReservation(
            lab_id=lab.lab_id,
            reserved_by=user.user_id,
            start_time=start,
            end_time=end,
            status=status,
        )
        db.add(res)
        db.flush()
        # Add booker as a participant
        db.add(ReservationParticipant(reservation_id=res.reservation_id, user_id=user.user_id))
        res_objs.append(res)

    # Add an extra participant to a reservation
    db.add(ReservationParticipant(reservation_id=res_objs[0].reservation_id, user_id=bob.user_id))
    db.add(ReservationParticipant(reservation_id=res_objs[0].reservation_id, user_id=carol.user_id))
    db.flush()

    # ------------------------------------------------------------------
    # Equipment Borrowings
    # ------------------------------------------------------------------
    print("── Seeding equipment borrowings …")

    def make_borrowing(user, equip, borrow_offset_h, expected_offset_h, actual_offset_h, status):
        return EquipmentBorrowing(
            user_id=user.user_id,
            equipment_id=equip.equipment_id,
            borrow_time=NOW + timedelta(hours=borrow_offset_h),
            expected_return=NOW + timedelta(hours=expected_offset_h),
            actual_return=(NOW + timedelta(hours=actual_offset_h)) if actual_offset_h is not None else None,
            status=status,
        )

    borrowings = [
        # Returned on time
        make_borrowing(alice, equip_objs["PC-Workstation-01"], -48, -24, -20, "Returned"),
        # Returned late  (2 h overdue)
        make_borrowing(bob,   equip_objs["Microscope-01"],     -72, -48, -46, "Returned"),
        # Still borrowed — overdue now
        make_borrowing(carol, equip_objs["PC-Workstation-03"], -10,  -2, None, "Borrowed"),
        # Still borrowed — within due time
        make_borrowing(dave,  equip_objs["Microscope-02"],      -5,  48, None, "Borrowed"),
        # Returned on time
        make_borrowing(eve,   equip_objs["PC-Workstation-02"], -96, -72, -70, "Returned"),
    ]
    borrow_objs = []
    for b in borrowings:
        db.add(b)
        db.flush()
        borrow_objs.append(b)

    # ------------------------------------------------------------------
    # Penalties
    # ------------------------------------------------------------------
    print("── Seeding penalties …")
    # Bob returned Microscope-01 2 h late  → 2 × 25 = 50 THB
    p1 = Penalty(
        user_id=bob.user_id,
        borrow_id=borrow_objs[1].borrow_id,
        fine_amount=50.00,
        is_resolved=False,
    )
    db.add(p1)
    db.flush()

    # Carol still overdue — penalty created immediately (7 h × 25 = 175 THB)
    p2 = Penalty(
        user_id=carol.user_id,
        borrow_id=borrow_objs[2].borrow_id,
        fine_amount=175.00,
        is_resolved=False,
    )
    db.add(p2)
    db.flush()

    # ------------------------------------------------------------------
    # Maintenance Records
    # ------------------------------------------------------------------
    print("── Seeding maintenance records …")
    m1 = MaintenanceRecord(
        equipment_id=equip_objs["Oscilloscope-01"].equipment_id,
        reported_by=alice.user_id,
        technician_id=tech_user.user_id,
        report_date=NOW - timedelta(days=5),
        resolved_date=None,
        issue_detail="Power supply unit not starting. Sparks observed on startup.",
        status="In Progress",
    )
    m2 = MaintenanceRecord(
        equipment_id=equip_objs["Microscope-02"].equipment_id,
        reported_by=bob.user_id,
        technician_id=tech_user.user_id,
        report_date=NOW - timedelta(days=2),
        resolved_date=None,
        issue_detail="Left eyepiece lens cracked. Needs replacement.",
        status="Reported",
    )
    m3 = MaintenanceRecord(
        equipment_id=equip_objs["Projector-A"].equipment_id,
        reported_by=carol.user_id,
        technician_id=tech_user.user_id,
        report_date=NOW - timedelta(days=10),
        resolved_date=NOW - timedelta(days=8),
        issue_detail="Lamp expired. Replaced with new lamp.",
        status="Fixed",
    )
    # Second repair on Oscilloscope-01 (demonstrates GROUP BY repair_count > 1)
    m4 = MaintenanceRecord(
        equipment_id=equip_objs["Oscilloscope-01"].equipment_id,
        reported_by=dave.user_id,
        technician_id=None,
        report_date=NOW - timedelta(days=30),
        resolved_date=NOW - timedelta(days=25),
        issue_detail="Probe calibration drift. Recalibrated and tested.",
        status="Fixed",
    )
    for m in (m1, m2, m3, m4):
        db.add(m)
    db.flush()

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------
    print("── Seeding notifications …")
    notifs = [
        Notification(user_id=bob.user_id,   message="A penalty of 50.00 THB has been created for late return of Microscope-01.", is_read=False),
        Notification(user_id=carol.user_id, message="A penalty of 175.00 THB has been created for late return of PC-Workstation-03.", is_read=False),
        Notification(user_id=alice.user_id, message="Your reservation for CS-101 has been approved.", is_read=True),
        Notification(user_id=dave.user_id,  message="Your reservation for GP-301 has been approved.", is_read=False),
    ]
    for n in notifs:
        db.add(n)
    db.flush()

    # ------------------------------------------------------------------
    # Audit Logs
    # ------------------------------------------------------------------
    print("── Seeding audit logs …")
    audit_entries = [
        AuditLog(actor_user_id=admin_user.user_id, action="lab.created",        target_type="lab",       target_id=lab_objs["CS-101"].lab_id,  details={"room_name": "CS-101"}),
        AuditLog(actor_user_id=admin_user.user_id, action="lab.created",        target_type="lab",       target_id=lab_objs["CS-102"].lab_id,  details={"room_name": "CS-102"}),
        AuditLog(actor_user_id=admin_user.user_id, action="equipment.created",  target_type="equipment", target_id=equip_objs["PC-Workstation-01"].equipment_id, details={"equipment_name": "PC-Workstation-01"}),
        AuditLog(actor_user_id=staff_user.user_id, action="equipment.borrowed", target_type="borrowing", target_id=borrow_objs[0].borrow_id, details={"borrower_user_id": alice.user_id}),
        AuditLog(actor_user_id=staff_user.user_id, action="equipment.returned", target_type="borrowing", target_id=borrow_objs[1].borrow_id, details={"borrower_user_id": bob.user_id, "status": "Returned"}),
    ]
    for a in audit_entries:
        db.add(a)
    db.flush()

    db.commit()
    print("\n✓  Demo seed completed successfully!")
    print(f"   Login URL: http://localhost:8000")
    print(f"   Admin:      admin@lab.demo / {DEMO_PASSWORD}")
    print(f"   Staff:      staff@lab.demo / {DEMO_PASSWORD}")
    print(f"   Technician: tech@lab.demo  / {DEMO_PASSWORD}")
    print(f"   Student:    alice@lab.demo / {DEMO_PASSWORD}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed(db)
    except Exception as exc:
        db.rollback()
        print(f"\n✗  Seed failed: {exc}")
        raise
    finally:
        db.close()
