from sqlalchemy.orm import Session

from app.db.models.role import Role


DEFAULT_ROLES = ["Student", "Staff", "Technician", "Admin"]


def seed_roles(db: Session) -> None:
    existing = {role.role_name for role in db.query(Role).all()}
    missing_roles = [role_name for role_name in DEFAULT_ROLES if role_name not in existing]
    if not missing_roles:
        return

    for role_name in missing_roles:
        db.add(Role(role_name=role_name))
    db.commit()
