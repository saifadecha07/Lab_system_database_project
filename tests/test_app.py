import importlib

from fastapi.testclient import TestClient

from conftest import _clear_app_modules, create_borrowing_graph, create_user, login


def test_registration_assigns_student_role_and_login_returns_csrf(client, db_session, model_bundle):
    response = client.post(
        "/auth/register",
        json={
            "email": "student@example.com",
            "first_name": "Test",
            "last_name": "Student",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["role_name"] == "Student"

    csrf_token = login(client, "student@example.com")
    assert csrf_token


def test_student_cannot_access_admin_routes(client, db_session, model_bundle):
    create_user(db_session, model_bundle, "Student", "student-admin-block@example.com")
    csrf_token = login(client, "student-admin-block@example.com")

    response = client.post(
        "/admin/labs",
        json={"room_name": "A-101", "capacity": 40, "status": "Available"},
        headers={"X-CSRF-Token": csrf_token},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_admin_create_lab_requires_csrf(client, db_session, model_bundle):
    create_user(db_session, model_bundle, "Admin", "admin-csrf@example.com")
    login(client, "admin-csrf@example.com")

    response = client.post(
        "/admin/labs",
        json={"room_name": "A-201", "capacity": 30, "status": "Available"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "CSRF validation failed"


def test_reservation_overlap_is_rejected(client, db_session, model_bundle):
    admin = create_user(db_session, model_bundle, "Admin", "admin-reservation@example.com")
    student = create_user(db_session, model_bundle, "Student", "student-reservation@example.com")

    admin_csrf = login(client, admin.email)
    lab_response = client.post(
        "/admin/labs",
        json={"room_name": "C-301", "capacity": 35, "status": "Available"},
        headers={"X-CSRF-Token": admin_csrf},
    )
    assert lab_response.status_code == 201, lab_response.text
    lab_id = lab_response.json()["lab_id"]

    client.post("/auth/logout", headers={"X-CSRF-Token": admin_csrf})

    student_csrf = login(client, student.email)
    first_response = client.post(
        "/reservations",
        json={
            "lab_id": lab_id,
            "start_time": "2026-04-10T09:00:00Z",
            "end_time": "2026-04-10T11:00:00Z",
        },
        headers={"X-CSRF-Token": student_csrf},
    )
    assert first_response.status_code == 201, first_response.text

    second_response = client.post(
        "/reservations",
        json={
            "lab_id": lab_id,
            "start_time": "2026-04-10T10:00:00Z",
            "end_time": "2026-04-10T12:00:00Z",
        },
        headers={"X-CSRF-Token": student_csrf},
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Reservation time overlaps existing booking"


def test_late_return_creates_penalty_and_audit_log(client, db_session, model_bundle):
    staff = create_user(db_session, model_bundle, "Staff", "staff-return@example.com")
    borrower = create_user(db_session, model_bundle, "Student", "borrower@example.com")
    borrowing, equipment = create_borrowing_graph(db_session, model_bundle, borrower.user_id)

    csrf_token = login(client, staff.email)
    response = client.patch(
        f"/borrowings/{borrowing.borrow_id}/return",
        headers={"X-CSRF-Token": csrf_token},
    )

    assert response.status_code == 200, response.text

    Penalty = model_bundle["Penalty"]
    AuditLog = model_bundle["AuditLog"]
    refreshed_penalty = db_session.query(Penalty).filter(Penalty.borrow_id == borrowing.borrow_id).one()
    audit_log = db_session.query(AuditLog).filter(AuditLog.target_id == borrowing.borrow_id).one()

    assert float(refreshed_penalty.fine_amount) == 50.0
    assert audit_log.action == "equipment.returned"


def test_healthz_is_live_even_when_schema_is_missing(tmp_path, monkeypatch):
    database_path = tmp_path / "missing.db"
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
    monkeypatch.setenv("CSRF_EXEMPT_PATHS", "/auth/login,/auth/register,/healthz,/readyz")
    monkeypatch.setenv("PENALTY_RATE_PER_HOUR", "25")

    _clear_app_modules()

    config_module = importlib.import_module("app.config")
    config_module.get_settings.cache_clear()
    main_module = importlib.import_module("app.main")

    with TestClient(main_module.app) as client:
        live_response = client.get("/healthz")
        ready_response = client.get("/readyz")

    assert live_response.status_code == 200, live_response.text
    assert live_response.json()["status"] == "ok"
    assert ready_response.status_code == 503, ready_response.text
    assert ready_response.json()["status"] == "degraded"


def test_favicon_route_returns_no_content(client):
    response = client.get("/favicon.ico")

    assert response.status_code == 204, response.text


def test_allowed_hosts_keeps_railway_healthcheck_host(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./settings-test.db")
    monkeypatch.setenv("ALLOWED_HOSTS", "smart-lab-production.up.railway.app")

    _clear_app_modules()

    config_module = importlib.import_module("app.config")
    config_module.get_settings.cache_clear()
    settings = config_module.get_settings()

    assert "smart-lab-production.up.railway.app" in settings.allowed_hosts
    assert "healthcheck.railway.app" in settings.allowed_hosts
