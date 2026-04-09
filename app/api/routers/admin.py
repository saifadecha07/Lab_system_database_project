from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.db.models.audit_log import AuditLog
from app.db.models.equipment import Equipment
from app.db.models.equipment import EquipmentCategory
from app.db.models.lab import Lab
from app.db.models.role import Role
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.audit import AuditLogResponse
from app.schemas.equipments import EquipmentCreateRequest, EquipmentResponse
from app.schemas.labs import LabCreateRequest, LabResponse
from app.schemas.users import UpdateUserRoleRequest, UserResponse
from app.security.rbac import require_roles
from app.services.audit_service import create_audit_log


router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/labs", response_model=LabResponse, status_code=201)
def create_lab(
    payload: LabCreateRequest,
    current_user=Depends(require_roles("Admin")),
    db: Session = Depends(get_db),
):
    lab = Lab(room_name=payload.room_name, capacity=payload.capacity, status=payload.status)
    db.add(lab)
    db.flush()
    create_audit_log(
        db,
        "lab.created",
        "lab",
        actor_user_id=current_user.user_id,
        target_id=lab.lab_id,
        details={"room_name": lab.room_name, "status": lab.status},
    )
    db.commit()
    db.refresh(lab)
    return lab


@router.post("/equipments", response_model=EquipmentResponse, status_code=201)
def create_equipment(
    payload: EquipmentCreateRequest,
    current_user=Depends(require_roles("Admin")),
    db: Session = Depends(get_db),
):
    if payload.lab_id is not None:
        lab = db.query(Lab).filter(Lab.lab_id == payload.lab_id).first()
        if not lab:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab not found")
    if payload.category_id is not None:
        category = db.query(EquipmentCategory).filter(EquipmentCategory.category_id == payload.category_id).first()
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment category not found")

    equipment = Equipment(
        equipment_name=payload.equipment_name,
        lab_id=payload.lab_id,
        category_id=payload.category_id,
        status=payload.status,
    )
    db.add(equipment)
    db.flush()
    create_audit_log(
        db,
        "equipment.created",
        "equipment",
        actor_user_id=current_user.user_id,
        target_id=equipment.equipment_id,
        details={"equipment_name": equipment.equipment_name, "status": equipment.status},
    )
    db.commit()
    db.refresh(equipment)
    return equipment


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def change_user_role(
    user_id: int,
    payload: UpdateUserRoleRequest,
    current_user=Depends(require_roles("Admin")),
    db: Session = Depends(get_db),
):
    user = db.query(User).options(joinedload(User.role)).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    role = db.query(Role).filter(Role.role_name == payload.role_name).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    previous_role = user.role.role_name if user.role else None
    user.role_id = role.role_id
    create_audit_log(
        db,
        "user.role_changed",
        "user",
        actor_user_id=current_user.user_id,
        target_id=user.user_id,
        details={"from_role": previous_role, "to_role": role.role_name},
    )
    db.commit()
    db.refresh(user)
    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role_name=role.role_name,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.get("/audit-logs", response_model=list[AuditLogResponse])
def list_audit_logs(
    limit: int = 100,
    _: object = Depends(require_roles("Admin")),
    db: Session = Depends(get_db),
):
    safe_limit = max(1, min(limit, 500))
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(safe_limit).all()
