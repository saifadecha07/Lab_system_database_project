from sqlalchemy.orm import Session

from app.db.models.audit_log import AuditLog


def create_audit_log(
    db: Session,
    action: str,
    target_type: str,
    *,
    actor_user_id: int | None = None,
    target_id: int | None = None,
    details: dict | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
    )
    db.add(audit_log)
    db.flush()
    return audit_log
