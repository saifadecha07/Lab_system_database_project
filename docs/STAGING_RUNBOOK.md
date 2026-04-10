# Staging Runbook

## Purpose

This runbook defines the minimum steps to deploy and verify the Smart Lab backend in a staging environment before production rollout.

## Prerequisites

- a PostgreSQL database for staging
- application service/container configured to run `uvicorn`
- environment variables set for staging
- Alembic migrations available from this repository

## Required Environment Variables

Set these values in staging:

```env
APP_ENV=production
DEBUG=false
SECRET_KEY=<strong-random-secret>
DATABASE_URL=<postgres-connection-string>
SESSION_COOKIE_NAME=smartlab_session
SESSION_MAX_AGE=3600
SESSION_SAME_SITE=lax
SESSION_HTTPS_ONLY=true
RATE_LIMIT_LOGIN=5/minute
ALLOWED_HOSTS=staging.example.com,healthcheck.railway.app,*.railway.app,*.up.railway.app
CORS_ORIGINS=https://staging.example.com
CSRF_EXEMPT_PATHS=/auth/login,/auth/register,/healthz
PENALTY_RATE_PER_HOUR=25
```

## Deploy Sequence

This repository already includes `railway.json`, so Railway can pick up:

- start command
- pre-deploy migration command
- health check path

### 1. Install dependencies

```powershell
pip install -r requirements.txt
```

### 2. Run migrations

```powershell
alembic upgrade head
```

Expected outcome:

- base schema exists
- default roles are seeded
- PostgreSQL `btree_gist` extension is enabled
- reservation overlap exclusion constraint exists

### 3. Start the app

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Verify health endpoint

```powershell
curl http://127.0.0.1:8000/healthz
```

Expected response:

```json
{"status":"ok","app":"Smart Lab Management System"}
```

## Functional Smoke Test

### 1. Register a student

- `POST /auth/register`
- verify returned role is `Student`

### 2. Log in

- `POST /auth/login`
- capture the `X-CSRF-Token` response header
- ensure session cookie is present

### 3. Verify CSRF enforcement

- call an authenticated mutating route without `X-CSRF-Token`
- expect `403 CSRF validation failed`

### 4. Verify admin flow

- log in as an admin
- create a lab with `POST /admin/labs`
- check `GET /admin/audit-logs` to confirm an audit entry exists

### 5. Verify reservation overlap protection

- create a reservation for a lab
- attempt a second overlapping reservation on the same lab
- expect rejection

If the rejection happens at the database layer, the API should still treat it as a failed reservation and return an error response.

## Rollback

To roll back the last migration:

```powershell
alembic downgrade -1
```

Use rollback only after checking whether newer code depends on the current schema.

## Post-Deploy Checks

- confirm `/healthz` is reachable through the staging host
- confirm session cookies are marked secure when served over HTTPS
- confirm reservation overlap attempts are blocked
- confirm audit log rows are created for admin actions
- confirm login and logout work from the browser frontend

## Known Follow-Up Work

- add monitoring and alerting around failed logins and 5xx responses
- add deeper end-to-end coverage for maintenance and penalties
- rebuild the local `.venv` used by the project so development verification does not depend on the temporary `.deps` setup
