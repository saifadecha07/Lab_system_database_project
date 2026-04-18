import importlib
import sys
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient


def _clear_app_modules() -> None:
    module_names = [name for name in sys.modules if name == "app" or name.startswith("app.")]
    for module_name in module_names:
        sys.modules.pop(module_name, None)


@pytest.fixture
def app_context(tmp_path, monkeypatch):
    database_path = tmp_path / "test.db"
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_NAME", "Smart Lab Test")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("SESSION_COOKIE_NAME", "smartlab_test_session")
    monkeypatch.setenv("SESSION_MAX_AGE", "3600")
    monkeypatch.setenv("SESSION_SAME_SITE", "lax")
    monkeypatch.setenv("SESSION_HTTPS_ONLY", "false")
    monkeypatch.setenv("RATE_LIMIT_LOGIN", "100/minute")
    monkeypatch.setenv("ALLOWED_HOSTS", "testserver,localhost,127.0.0.1")
    monkeypatch.setenv("CORS_ORIGINS", "http://testserver")
    monkeypatch.setenv("CSRF_EXEMPT_PATHS", "/auth/login,/auth/register,/healthz")
    monkeypatch.setenv("PENALTY_RATE_PER_HOUR", "25")

    _clear_app_modules()

    config_module = importlib.import_module("app.config")
    config_module.get_settings.cache_clear()
    base_module = importlib.import_module("app.db.base")
    session_module = importlib.import_module("app.db.session")
    importlib.import_module("app.db.models")
    bootstrap_module = importlib.import_module("app.services.bootstrap_service")

    base_module.Base.metadata.create_all(bind=session_module.engine)
    db = session_module.SessionLocal()
    try:
        bootstrap_module.seed_roles(db)
    finally:
        db.close()

    main_module = importlib.import_module("app.main")
    return {
        "main_module": main_module,
        "session_module": session_module,
    }


@pytest.fixture
def client(app_context):
    with TestClient(app_context["main_module"].app) as test_client:
        yield test_client


@pytest.fixture
def db_session(app_context):
    session_module = app_context["session_module"]
    db = session_module.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def model_bundle():
    user_module = importlib.import_module("app.db.models.user")
    role_module = importlib.import_module("app.db.models.role")
    lab_module = importlib.import_module("app.db.models.lab")
    equipment_module = importlib.import_module("app.db.models.equipment")
    borrowing_module = importlib.import_module("app.db.models.borrowing")
    maintenance_module = importlib.import_module("app.db.models.maintenance")
    penalty_module = importlib.import_module("app.db.models.penalty")
    audit_module = importlib.import_module("app.db.models.audit_log")
    hashing_module = importlib.import_module("app.security.hashing")
    return {
        "User": user_module.User,
        "Role": role_module.Role,
        "Lab": lab_module.Lab,
        "Equipment": equipment_module.Equipment,
        "EquipmentBorrowing": borrowing_module.EquipmentBorrowing,
        "MaintenanceRecord": maintenance_module.MaintenanceRecord,
        "Penalty": penalty_module.Penalty,
        "AuditLog": audit_module.AuditLog,
        "hash_password": hashing_module.hash_password,
    }


def create_user(db_session, model_bundle, role_name: str, email: str, password: str = "StrongPassword123!"):
    Role = model_bundle["Role"]
    User = model_bundle["User"]
    hash_password = model_bundle["hash_password"]

    role = db_session.query(Role).filter(Role.role_name == role_name).one()
    user = User(
        role_id=role.role_id,
        email=email,
        first_name=role_name,
        last_name="User",
        password_hash=hash_password(password),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def login(client: TestClient, email: str, password: str = "StrongPassword123!") -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.headers["X-CSRF-Token"]


def create_borrowing_graph(db_session, model_bundle, borrower_user_id: int):
    Lab = model_bundle["Lab"]
    Equipment = model_bundle["Equipment"]
    EquipmentBorrowing = model_bundle["EquipmentBorrowing"]

    lab = Lab(room_name="B-201", capacity=25, status="Available")
    db_session.add(lab)
    db_session.flush()

    equipment = Equipment(equipment_name="Oscilloscope", lab_id=lab.lab_id, status="Borrowed")
    db_session.add(equipment)
    db_session.flush()

    borrowing = EquipmentBorrowing(
        user_id=borrower_user_id,
        equipment_id=equipment.equipment_id,
        expected_return=datetime.now(timezone.utc) - timedelta(hours=2),
        status="Borrowed",
    )
    db_session.add(borrowing)
    db_session.commit()
    db_session.refresh(borrowing)
    db_session.refresh(equipment)
    return borrowing, equipment
