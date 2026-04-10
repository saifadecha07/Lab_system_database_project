# Railway Deployment Guide

## 1. Services

Recommended Railway services:

- `web` service for FastAPI app
- `postgres` service for PostgreSQL

Keep at least two environments:

- `staging`
- `production`

## 2. Required Variables

Set these on Railway:

- `DATABASE_URL`
- `SECRET_KEY`
- `APP_ENV=production`
- `DEBUG=false`
- `SESSION_COOKIE_NAME`
- `SESSION_MAX_AGE`
- `RATE_LIMIT_LOGIN`
- `CORS_ORIGINS`
- `ALLOWED_HOSTS`
- `PENALTY_RATE_PER_HOUR`

For `ALLOWED_HOSTS`, include:

- `healthcheck.railway.app`
- your Railway public domain
- any custom domain you attach

The application now always preserves Railway platform hosts even if you provide a custom `ALLOWED_HOSTS` value, which avoids accidental 400 responses on Railway health checks.

## 3. Railway Start Command

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

It is included in:

- `Procfile`
- `railway.json`

Current `railway.json` also configures:

- `preDeployCommand=alembic upgrade head`
- `healthcheckPath=/healthz`
- restart on failure
- `/healthz` stays process-only so Railway can mark the replica live even if PostgreSQL is still warming up
- `/readyz` remains available for database/schema readiness checks

## 4. PostgreSQL Notes

Railway PostgreSQL gives you a managed connection string through `DATABASE_URL`.

Current SQLAlchemy settings are conservative:

- `pool_size=5`
- `max_overflow=10`
- `pool_pre_ping=True`
- `pool_recycle=1800`

## 5. Secrets Management

Use Railway Variables for secrets.

Rules:

- never store secrets in source code
- never commit `.env`
- use `.env.example` for placeholders only

## 6. Deployment Sequence

1. Provision PostgreSQL service
2. Set `DATABASE_URL` into web service
3. Set application secrets
4. Deploy app
5. Run `alembic upgrade head`
6. Seed baseline roles
7. Verify `/healthz`
8. Verify `/readyz`
9. Test register/login/admin role flow in staging

The current migration chain also enables the PostgreSQL `btree_gist` extension and adds a reservation overlap exclusion constraint.
