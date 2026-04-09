# Smart Lab Management System

This repository now contains a security-first FastAPI scaffold for the CN230 Smart Lab project. The goal is to give you a clean backend baseline before you build the full product.

## What Is Included

- FastAPI project structure
- PostgreSQL-ready SQLAlchemy models
- Email/password registration and login baseline
- Session-based authentication for a web app
- Role-based access control for `Student`, `Staff`, `Technician`, and `Admin`
- Reservation, maintenance, borrowing, penalty, notification, admin, and reporting route skeletons
- Railway-ready configuration files
- Detailed documentation in the `docs/` folder

## Project Structure

```text
app/
  api/             HTTP routes and dependencies
  db/              SQLAlchemy base, session, and models
  schemas/         Request/response validation
  security/        Hashing, RBAC, sessions, rate limiting
  services/        Business logic layer
  static/          Static assets
  templates/       HTML templates
docs/              Architecture, security, deployment guides
migrations/        Alembic migration area
tests/             Test planning area
```

## Local Setup

1. Install Python 3.11 or newer.
2. Create and activate a virtual environment.
3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Create `.env` from `.env.example` and set a real `DATABASE_URL`.
5. Run migrations:

```powershell
alembic upgrade head
```

6. Run the app:

```powershell
uvicorn app.main:app --reload
```

7. Open:

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/healthz`

## Railway Setup

Set these variables in Railway before deployment:

- `DATABASE_URL`
- `SECRET_KEY`
- `APP_ENV=production`
- `DEBUG=false`
- `CORS_ORIGINS`
- `ALLOWED_HOSTS`

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Important Notes

- The app now expects a migrated database and will fail startup if required tables are missing.
- Browser-authenticated mutating requests now require the `X-CSRF-Token` header returned after login.
- Audit logs are recorded for high-risk admin and operational actions, but broader observability is still recommended.

## Documentation

- `docs/ARCHITECTURE.md`
- `docs/SECURITY.md`
- `docs/RAILWAY_DEPLOYMENT.md`
- `docs/STAGING_RUNBOOK.md`
- `docs/RBAC.md`
- `docs/IMPLEMENTATION_PLAN.md`
- `docs/PRODUCTION_HARDENING_REPORT.md`

## Legacy Utility

The old PostgreSQL table creation helper still exists as `create_tables.py`. It is now only a helper script and is no longer the main app entry point.
