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
from app.schemas.equipments import EquipmentCreateRequest, EquipmentResponse, EquipmentUpdateRequest
from app.schemas.labs import LabCreateRequest, LabResponse, LabUpdateRequest
from app.schemas.auth import MessageResponse
from app.schemas.users import RoleResponse, UpdateUserRoleRequest, UpdateUserStatusRequest, UserResponse
from app.security.rbac import require_roles
from app.services.audit_service import create_audit_log


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserResponse])
def list_users(
    _: object = Depends(require_roles("Admin")),
    db: Session = Depends(get_db),
):
    users = db.query(User).options(joinedload(User.role)).order_by(User.created_at.desc()).all()
    return [
        UserResponse(
            user_id=user.user_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role_name=user.role.role_name,
            is_active=user.is_active,
            created_at=user.created_at,
        )
        for user in users
    ]


@router.get("/roles", response_model=list[RoleResponse])
def list_roles(
    _: object = Depends(require_roles("Admin")),
    db: Session = Depends(get_db),
):
    return db.query(Role).order_by(Role.role_name.asc()).all()


@router.get("/labs", response_model=list[LabResponse])
def list_labs(
    _: object = Depends(require_roles("Admin")),
    db: Session = Depends(get_db),
):
    return db.query(Lab).order_by(Lab.room_name.asc()).all()


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


@router.patch("/labs/{lab_id}", response_model=LabResponse)
def update_lab(
    lab_id: int,
    payload: LabUpdateRequest,
    current_user=Depends(require_roles("Admin")),
    db: Session = Depends(get_db),
):
    lab = db.query(Lab).filter(Lab.lab_id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab not found")

    previous_state = {"room_name": lab.room_name, "capacity": lab.capacity, "status": lab.status}
    lab.room_name = payload.room_name
    lab.capacity = payload.capacity
    lab.status = payload.status
    create_audit_log(
        db,
        "lab.updated",
        "lab",
        actor_user_id=current_user.user_id,
        target_id=lab.lab_id,
        details={"before": previous_state, "after": {"room_name": lab.room_name, "capacity": lab.capacity, "status": lab.status}},
    )
    db.commit()
    db.refresh(lab)
    return lab


@router.delete("/labs/{lab_id}", response_model=MessageResponse)
def delete_lab(
    lab_id: int,
    current_user=Depends(require_roles("Admin")),
    db: Session = Depends(get_db),
):
    lab = db.query(Lab).filter(Lab.lab_id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab not found")
    if lab.reservations or lab.equipments:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete lab with related reservations or equipments",
        )

    create_audit_log(
        db,
        "lab.deleted",
        "lab",
        actor_user_id=current_user.user_id,
        target_id=lab.lab_id,
        details={"room_name": lab.room_name},
    )
    db.delete(lab)
    db.commit()
    return MessageResponse(message="Lab deleted")


@router.get("/equipments", response_model=list[EquipmentResponse])
def list_equipments(
    _: object = Depends(require_roles("Admin")),
    db: Session = Depends(get_db),
):
    return db.query(Equipment).order_by(Equipment.equipment_name.asc()).all()


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


@router.patch("/equipments/{equipment_id}", response_model=EquipmentResponse)
def update_equipment(
    equipment_id: int,
    payload: EquipmentUpdateRequest,
    current_user=Depends(require_roles("Admin")),
    db: Session = Depends(get_db),
):
    equipment = db.query(Equipment).filter(Equipment.equipment_id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    if payload.lab_id is not None:
        lab = db.query(Lab).filter(Lab.lab_id == payload.lab_id).first()
        if not lab:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab not found")
    if payload.category_id is not None:
        category = db.query(EquipmentCategory).filter(EquipmentCategory.category_id == payload.category_id).first()
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment category not found")

    previous_state = {
        "equipment_name": equipment.equipment_name,
        "lab_id": equipment.lab_id,
        "category_id": equipment.category_id,
        "status": equipment.status,
    }
    equipment.equipment_name = payload.equipment_name
    equipment.lab_id = payload.lab_id
    equipment.category_id = payload.category_id
    equipment.status = payload.status
    create_audit_log(
        db,
        "equipment.updated",
        "equipment",
        actor_user_id=current_user.user_id,
        target_id=equipment.equipment_id,
        details={
            "before": previous_state,
            "after": {
                "equipment_name": equipment.equipment_name,
                "lab_id": equipment.lab_id,
                "category_id": equipment.category_id,
                "status": equipment.status,
            },
        },
    )
    db.commit()
    db.refresh(equipment)
    return equipment


@router.delete("/equipments/{equipment_id}", response_model=MessageResponse)
def delete_equipment(
    equipment_id: int,
    current_user=Depends(require_roles("Admin")),
    db: Session = Depends(get_db),
):
    equipment = db.query(Equipment).filter(Equipment.equipment_id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    if equipment.borrowings:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete equipment with borrowing history",
        )

    create_audit_log(
        db,
        "equipment.deleted",
        "equipment",
        actor_user_id=current_user.user_id,
        target_id=equipment.equipment_id,
        details={"equipment_name": equipment.equipment_name},
    )
    db.delete(equipment)
    db.commit()
    return MessageResponse(message="Equipment deleted")


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


@router.patch("/users/{user_id}/status", response_model=UserResponse)
def change_user_status(
    user_id: int,
    payload: UpdateUserStatusRequest,
    current_user=Depends(require_roles("Admin")),
    db: Session = Depends(get_db),
):
    user = db.query(User).options(joinedload(User.role)).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    previous_status = user.is_active
    user.is_active = payload.is_active
    create_audit_log(
        db,
        "user.status_changed",
        "user",
        actor_user_id=current_user.user_id,
        target_id=user.user_id,
        details={"from_active": previous_status, "to_active": user.is_active},
    )
    db.commit()
    db.refresh(user)
    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role_name=user.role.role_name,
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
