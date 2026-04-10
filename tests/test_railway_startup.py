import importlib

from fastapi.testclient import TestClient

from conftest import _clear_app_modules


def test_startup_does_not_run_database_readiness_check(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_NAME", "Smart Lab Test")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./startup-test.db")
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

    def fail_readiness_check():
        raise AssertionError("startup should not perform a database readiness check")

    monkeypatch.setattr(main_module, "check_database_state", fail_readiness_check)

    with TestClient(main_module.app) as client:
        response = client.get("/healthz")

    assert response.status_code == 200, response.text
