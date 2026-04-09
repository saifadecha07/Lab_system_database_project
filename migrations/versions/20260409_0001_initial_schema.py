"""Initial schema with baseline seed data.

Revision ID: 20260409_0001
Revises:
Create Date: 2026-04-09 15:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260409_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "equipment_categories",
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("category_name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("category_id"),
        sa.UniqueConstraint("category_name"),
    )
    op.create_table(
        "lab_types",
        sa.Column("lab_type_id", sa.Integer(), nullable=False),
        sa.Column("type_name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("lab_type_id"),
        sa.UniqueConstraint("type_name"),
    )
    op.create_table(
        "roles",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("role_name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("role_id"),
        sa.UniqueConstraint("role_name"),
    )
    op.create_table(
        "labs",
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("lab_type_id", sa.Integer(), nullable=True),
        sa.Column("room_name", sa.String(length=100), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("capacity > 0", name="ck_labs_capacity_positive"),
        sa.PrimaryKeyConstraint("lab_id"),
        sa.UniqueConstraint("room_name"),
    )
    op.create_index(op.f("ix_labs_status"), "labs", ["status"], unique=False)
    op.create_table(
        "users",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.role_id"]),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_table(
        "audit_logs",
        sa.Column("audit_log_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("target_type", sa.String(length=100), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("audit_log_id"),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_actor_user_id"), "audit_logs", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_target_id"), "audit_logs", ["target_id"], unique=False)
    op.create_table(
        "equipments",
        sa.Column("equipment_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("lab_id", sa.Integer(), nullable=True),
        sa.Column("equipment_name", sa.String(length=150), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["equipment_categories.category_id"]),
        sa.ForeignKeyConstraint(["lab_id"], ["labs.lab_id"]),
        sa.PrimaryKeyConstraint("equipment_id"),
    )
    op.create_index(op.f("ix_equipments_status"), "equipments", ["status"], unique=False)
    op.create_table(
        "equipment_borrowings",
        sa.Column("borrow_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("equipment_id", sa.Integer(), nullable=False),
        sa.Column("borrow_time", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("expected_return", sa.DateTime(), nullable=False),
        sa.Column("actual_return", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipments.equipment_id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("borrow_id"),
    )
    op.create_index(op.f("ix_equipment_borrowings_equipment_id"), "equipment_borrowings", ["equipment_id"], unique=False)
    op.create_index(op.f("ix_equipment_borrowings_status"), "equipment_borrowings", ["status"], unique=False)
    op.create_index(op.f("ix_equipment_borrowings_user_id"), "equipment_borrowings", ["user_id"], unique=False)
    op.create_table(
        "lab_reservations",
        sa.Column("reservation_id", sa.Integer(), nullable=False),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("reserved_by", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["lab_id"], ["labs.lab_id"]),
        sa.ForeignKeyConstraint(["reserved_by"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("reservation_id"),
    )
    op.create_index(op.f("ix_lab_reservations_lab_id"), "lab_reservations", ["lab_id"], unique=False)
    op.create_index(op.f("ix_lab_reservations_reserved_by"), "lab_reservations", ["reserved_by"], unique=False)
    op.create_index(op.f("ix_lab_reservations_status"), "lab_reservations", ["status"], unique=False)
    op.create_table(
        "maintenance_records",
        sa.Column("repair_id", sa.Integer(), nullable=False),
        sa.Column("equipment_id", sa.Integer(), nullable=False),
        sa.Column("reported_by", sa.Integer(), nullable=False),
        sa.Column("technician_id", sa.Integer(), nullable=True),
        sa.Column("report_date", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("resolved_date", sa.DateTime(), nullable=True),
        sa.Column("issue_detail", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipments.equipment_id"]),
        sa.ForeignKeyConstraint(["reported_by"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["technician_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("repair_id"),
    )
    op.create_index(op.f("ix_maintenance_records_equipment_id"), "maintenance_records", ["equipment_id"], unique=False)
    op.create_index(op.f("ix_maintenance_records_status"), "maintenance_records", ["status"], unique=False)
    op.create_table(
        "notifications",
        sa.Column("notification_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("notification_id"),
    )
    op.create_index(op.f("ix_notifications_user_id"), "notifications", ["user_id"], unique=False)
    op.create_table(
        "penalties",
        sa.Column("penalty_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("borrow_id", sa.Integer(), nullable=False),
        sa.Column("fine_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_resolved", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["borrow_id"], ["equipment_borrowings.borrow_id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("penalty_id"),
    )
    op.create_index(op.f("ix_penalties_borrow_id"), "penalties", ["borrow_id"], unique=False)
    op.create_index(op.f("ix_penalties_user_id"), "penalties", ["user_id"], unique=False)
    op.create_table(
        "reservation_participants",
        sa.Column("reservation_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["reservation_id"], ["lab_reservations.reservation_id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("reservation_id", "user_id"),
    )

    role_table = sa.table("roles", sa.column("role_name", sa.String(length=50)))
    op.bulk_insert(
        role_table,
        [
            {"role_name": "Student"},
            {"role_name": "Staff"},
            {"role_name": "Technician"},
            {"role_name": "Admin"},
        ],
    )


def downgrade() -> None:
    op.drop_table("reservation_participants")
    op.drop_index(op.f("ix_penalties_user_id"), table_name="penalties")
    op.drop_index(op.f("ix_penalties_borrow_id"), table_name="penalties")
    op.drop_table("penalties")
    op.drop_index(op.f("ix_notifications_user_id"), table_name="notifications")
    op.drop_table("notifications")
    op.drop_index(op.f("ix_maintenance_records_status"), table_name="maintenance_records")
    op.drop_index(op.f("ix_maintenance_records_equipment_id"), table_name="maintenance_records")
    op.drop_table("maintenance_records")
    op.drop_index(op.f("ix_lab_reservations_status"), table_name="lab_reservations")
    op.drop_index(op.f("ix_lab_reservations_reserved_by"), table_name="lab_reservations")
    op.drop_index(op.f("ix_lab_reservations_lab_id"), table_name="lab_reservations")
    op.drop_table("lab_reservations")
    op.drop_index(op.f("ix_equipment_borrowings_user_id"), table_name="equipment_borrowings")
    op.drop_index(op.f("ix_equipment_borrowings_status"), table_name="equipment_borrowings")
    op.drop_index(op.f("ix_equipment_borrowings_equipment_id"), table_name="equipment_borrowings")
    op.drop_table("equipment_borrowings")
    op.drop_index(op.f("ix_equipments_status"), table_name="equipments")
    op.drop_table("equipments")
    op.drop_index(op.f("ix_audit_logs_target_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_actor_user_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_labs_status"), table_name="labs")
    op.drop_table("labs")
    op.drop_table("roles")
    op.drop_table("lab_types")
    op.drop_table("equipment_categories")
