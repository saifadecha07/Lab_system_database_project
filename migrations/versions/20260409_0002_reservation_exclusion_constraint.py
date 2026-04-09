"""Add PostgreSQL exclusion constraint for reservation overlap.

Revision ID: 20260409_0002
Revises: 20260409_0001
Create Date: 2026-04-09 16:25:00
"""

from alembic import op


revision = "20260409_0002"
down_revision = "20260409_0001"
branch_labels = None
depends_on = None


CONSTRAINT_NAME = "ex_lab_reservations_no_overlap"


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute(
        f"""
        ALTER TABLE lab_reservations
        ADD CONSTRAINT {CONSTRAINT_NAME}
        EXCLUDE USING gist (
            lab_id WITH =,
            tsrange(start_time, end_time, '[)') WITH &&
        )
        WHERE (status IN ('Pending', 'Approved'))
        """
    )


def downgrade() -> None:
    op.execute(f"ALTER TABLE lab_reservations DROP CONSTRAINT IF EXISTS {CONSTRAINT_NAME}")
