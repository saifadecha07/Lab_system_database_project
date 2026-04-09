# Production Hardening Report

## Scope

This document summarizes the production-readiness work completed for the CN230 Smart Lab backend during this session.

## Summary

The project was upgraded from a development-oriented scaffold into a safer staging/production baseline with:

- migration-first database startup validation
- CSRF protection for authenticated mutating requests
- trusted host validation
- stronger session configuration controls
- audit logging for high-risk actions
- PostgreSQL reservation overlap exclusion protection
- executable tests for key security and workflow paths
- deployment and architecture documentation updates

## Completed Changes

### 1. Application Startup and Deployment Safety

Files:

- `app/main.py`
- `app/db/session.py`
- `migrations/env.py`
- `migrations/script.py.mako`
- `migrations/versions/20260409_0001_initial_schema.py`
- `README.md`
- `docs/RAILWAY_DEPLOYMENT.md`
- `docs/ARCHITECTURE.md`

Changes:

- Removed runtime schema creation from app startup.
- Added startup validation that fails fast when required tables are missing.
- Switched the app to `lifespan` startup handling.
- Added Alembic environment files and an initial migration with baseline role seeding.
- Updated setup instructions so migrations run before starting the app.
- Improved SQLAlchemy engine construction so SQLite test databases work correctly.

Impact:

- Prevents accidental schema drift from `create_all()`.
- Makes deployment behavior predictable across environments.
- Forces schema management through migrations.

### 2. Security Hardening

Files:

- `app/config.py`
- `app/security/session.py`
- `app/security/csrf.py`
- `app/main.py`
- `docs/SECURITY.md`

Changes:

- Set `debug` default to `false`.
- Added configurable session controls:
  - `SESSION_SAME_SITE`
  - `SESSION_HTTPS_ONLY`
- Added CSRF support for authenticated mutating requests.
- Added CSRF token generation at login and response header propagation.
- Added trusted host enforcement using `ALLOWED_HOSTS`.
- Fixed settings parsing so list-like env vars work from CSV values.

Impact:

- Reduces browser attack surface for authenticated users.
- Prevents host-header abuse in deployment.
- Makes configuration safer and more consistent with real deployment practices.

### 3. Audit Logging

Files:

- `app/db/models/audit_log.py`
- `app/services/audit_service.py`
- `app/schemas/audit.py`
- `app/db/models/__init__.py`
- `app/api/routers/admin.py`
- `app/services/maintenance_service.py`
- `app/services/borrowing_service.py`

Changes:

- Added an `audit_logs` table and ORM model.
- Added audit log service helper.
- Added admin endpoint to inspect audit logs.
- Recorded audit events for:
  - lab creation
  - equipment creation
  - role changes
  - maintenance report creation
  - maintenance status updates
  - equipment returns

Impact:

- Adds traceability for sensitive operational and administrative changes.
- Improves incident review and accountability.

### 4. Validation and Data Integrity Fixes

Files:

- `app/services/auth_service.py`
- `app/services/penalty_service.py`
- `app/api/routers/borrowings.py`
- `app/api/routers/admin.py`

Changes:

- Registration now fails clearly if default roles are missing instead of silently creating them at runtime.
- Equipment creation now validates referenced lab and category IDs.
- Borrowing return audit entries now record the acting staff/admin user.
- Fixed timezone handling in penalty calculation to prevent naive/aware datetime comparison crashes.
- Reservation creation now converts database integrity conflicts into a `409` API response.

Impact:

- Removes hidden production side effects.
- Prevents invalid references.
- Fixes a real runtime bug found during test execution.

### 5. Automated Tests

Files:

- `tests/conftest.py`
- `tests/test_app.py`
- `tests/README.md`

Coverage added:

- registration assigns `Student`
- authenticated mutating routes require CSRF token
- students cannot access admin routes
- reservation overlap is rejected
- late return creates penalty and audit log

Impact:

- Adds executable proof for core auth/security flows.
- Caught and confirmed the penalty timezone bug fix.

### 6. Reservation Protection at Database Level

Files:

- `migrations/versions/20260409_0002_reservation_exclusion_constraint.py`
- `docs/SECURITY.md`
- `docs/ARCHITECTURE.md`
- `docs/RAILWAY_DEPLOYMENT.md`

Changes:

- Added a PostgreSQL migration that enables `btree_gist`.
- Added an exclusion constraint to block overlapping reservations for the same lab while status is `Pending` or `Approved`.
- Updated deployment and security documentation to reflect the new database-level protection.

Impact:

- Prevents race-condition reservation overlaps even when concurrent requests bypass application-level checks.
- Moves a critical integrity guarantee into the database where it belongs.

### 7. Staging and Deployment Runbook

Files:

- `docs/STAGING_RUNBOOK.md`
- `railway.json`

Changes:

- Added a staging runbook with environment variables, migration steps, startup commands, smoke tests, and rollback guidance.
- Added `railway.json` with start command, pre-deploy migration command, and health check path.

Impact:

- Gives you a readable deployment checklist for staging and pre-production verification.

## Verification Performed

### Import Check

Verified that the app imports successfully with a test configuration after the changes.

### Test Suite

Executed the automated tests and confirmed:

```text
5 passed in 3.96s
```

## Key Files Added

- `app/security/csrf.py`
- `app/db/models/audit_log.py`
- `app/services/audit_service.py`
- `app/schemas/audit.py`
- `migrations/env.py`
- `migrations/script.py.mako`
- `migrations/versions/20260409_0001_initial_schema.py`
- `migrations/versions/20260409_0002_reservation_exclusion_constraint.py`
- `tests/conftest.py`
- `tests/test_app.py`
- `docs/STAGING_RUNBOOK.md`
- `docs/PRODUCTION_HARDENING_REPORT.md`

## Remaining Gaps

These are still recommended before calling the system fully production-ready:

- expand audit log coverage to more routes and add retention/archival policy
- add staging and production monitoring/alerting
- verify deployment with the intended Python runtime and recreate the broken local `.venv`
- add more end-to-end tests for maintenance, notifications, penalties, and role management

## Recommended Next Steps

1. Rebuild the project virtual environment so local development uses a healthy interpreter.
2. Run `alembic upgrade head` against the real database.
3. Deploy to staging and verify register/login/admin flows.
4. Add operational logging and health monitoring.
5. Add PostgreSQL-backed CI tests for migration and constraint behavior.
