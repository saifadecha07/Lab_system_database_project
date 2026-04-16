import importlib

from fastapi.testclient import TestClient

from conftest import _clear_app_modules, create_borrowing_graph, create_user, login


def test_root_page_contains_workspace_ui(client):
    response = client.get("/")

    assert response.status_code == 200, response.text
    assert "Enter The Workspace" in response.text
    assert "Student Workflows" in response.text


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
            "start_time": "2026-04-10T01:00:00Z",
            "end_time": "2026-04-10T05:00:00Z",
        },
        headers={"X-CSRF-Token": student_csrf},
    )
    assert first_response.status_code == 201, first_response.text

    second_response = client.post(
        "/reservations",
        json={
            "lab_id": lab_id,
            "start_time": "2026-04-10T01:00:00Z",
            "end_time": "2026-04-10T05:00:00Z",
        },
        headers={"X-CSRF-Token": student_csrf},
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Reservation time overlaps existing booking"


def test_reservation_rejects_non_fixed_slots(client, db_session, model_bundle):
    admin = create_user(db_session, model_bundle, "Admin", "admin-fixed-slot@example.com")
    student = create_user(db_session, model_bundle, "Student", "student-fixed-slot@example.com")

    admin_csrf = login(client, admin.email)
    lab_response = client.post(
        "/admin/labs",
        json={"room_name": "C-302", "capacity": 40, "status": "Available"},
        headers={"X-CSRF-Token": admin_csrf},
    )
    assert lab_response.status_code == 201, lab_response.text
    lab_id = lab_response.json()["lab_id"]

    client.post("/auth/logout", headers={"X-CSRF-Token": admin_csrf})

    student_csrf = login(client, student.email)
    response = client.post(
        "/reservations",
        json={
            "lab_id": lab_id,
            "start_time": "2026-04-10T02:00:00Z",
            "end_time": "2026-04-10T06:00:00Z",
        },
        headers={"X-CSRF-Token": student_csrf},
    )

    assert response.status_code == 422
    assert "fixed slots" in response.text


def test_reservation_availability_groups_slots_by_booking_date(client, db_session, model_bundle):
    admin = create_user(db_session, model_bundle, "Admin", "admin-availability@example.com")
    student = create_user(db_session, model_bundle, "Student", "student-availability@example.com")

    admin_csrf = login(client, admin.email)
    first_lab = client.post(
        "/admin/labs",
        json={"room_name": "L-101", "capacity": 24, "status": "Available"},
        headers={"X-CSRF-Token": admin_csrf},
    ).json()
    second_lab = client.post(
        "/admin/labs",
        json={"room_name": "L-102", "capacity": 32, "status": "Maintenance"},
        headers={"X-CSRF-Token": admin_csrf},
    ).json()
    client.post("/auth/logout", headers={"X-CSRF-Token": admin_csrf})

    student_csrf = login(client, student.email)
    reservation_response = client.post(
        "/reservations",
        json={
            "lab_id": first_lab["lab_id"],
            "start_time": "2026-04-10T01:00:00Z",
            "end_time": "2026-04-10T05:00:00Z",
        },
        headers={"X-CSRF-Token": student_csrf},
    )
    assert reservation_response.status_code == 201, reservation_response.text

    response = client.get("/reservations/availability?booking_date=2026-04-10")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["timezone"] == "Asia/Bangkok"
    assert [slot["label"] for slot in payload["slots"]] == ["08:00-12:00", "12:00-16:00", "16:00-20:00"]

    first_lab_slots = next(lab["slots"] for lab in payload["labs"] if lab["lab_id"] == first_lab["lab_id"])
    second_lab_slots = next(lab["slots"] for lab in payload["labs"] if lab["lab_id"] == second_lab["lab_id"])

    assert first_lab_slots[0]["is_available"] is False
    assert first_lab_slots[1]["is_available"] is True
    assert second_lab_slots[0]["is_available"] is False


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


def test_staff_can_create_and_list_borrowing(client, db_session, model_bundle):
    staff = create_user(db_session, model_bundle, "Staff", "staff-borrow@example.com")
    borrower = create_user(db_session, model_bundle, "Student", "student-borrow@example.com")

    Lab = model_bundle["Lab"]
    Equipment = model_bundle["Equipment"]

    lab = Lab(room_name="D-401", capacity=20, status="Available")
    db_session.add(lab)
    db_session.flush()

    equipment = Equipment(equipment_name="Signal Generator", lab_id=lab.lab_id, status="Available")
    db_session.add(equipment)
    db_session.commit()
    db_session.refresh(equipment)

    csrf_token = login(client, staff.email)
    create_response = client.post(
        "/borrowings",
        json={
            "user_id": borrower.user_id,
            "equipment_id": equipment.equipment_id,
            "expected_return": "2026-04-10T18:00:00Z",
        },
        headers={"X-CSRF-Token": csrf_token},
    )

    assert create_response.status_code == 201, create_response.text
    assert create_response.json()["status"] == "Borrowed"

    list_response = client.get("/borrowings?status_filter=Borrowed")
    assert list_response.status_code == 200, list_response.text
    assert len(list_response.json()) == 1


def test_admin_can_list_users_and_roles(client, db_session, model_bundle):
    admin = create_user(db_session, model_bundle, "Admin", "admin-directory@example.com")
    create_user(db_session, model_bundle, "Technician", "tech-directory@example.com")

    login(client, admin.email)

    users_response = client.get("/admin/users")
    roles_response = client.get("/admin/roles")

    assert users_response.status_code == 200, users_response.text
    assert len(users_response.json()) >= 2
    assert roles_response.status_code == 200, roles_response.text
    assert {role["role_name"] for role in roles_response.json()} == {"Admin", "Staff", "Student", "Technician"}


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
