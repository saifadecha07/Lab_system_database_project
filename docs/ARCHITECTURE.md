# Architecture Guide

## 1. Purpose

This scaffold is a security-first baseline for the CN230 Smart Lab Management System. It is structured to support:

- Email/password authentication
- Session-based login for a web application
- Role-based access control (RBAC)
- Reservation, borrowing, maintenance, penalty, and notification workflows
- PostgreSQL on Railway

The repository is intentionally organized so that security-sensitive logic is separated from routing and persistence logic.

## 2. Why FastAPI

FastAPI is recommended over Flask for this project because it gives you:

- Strong request and response validation through Pydantic
- A clean dependency system for auth and RBAC
- Better project scaling when routes grow into multiple modules
- Automatic API documentation at `/docs`

This project is still simple enough to understand, but it is also ready for later expansion into a production-style service.

## 3. Folder Responsibilities

### `app/main.py`

Application entry point. It:

- creates the FastAPI app
- wires middleware
- includes routers
- exposes `/healthz`
- validates that required tables already exist before serving traffic

Schema changes now belong in Alembic migrations only.

### `app/config.py`

Centralized application settings. Every important deployment value comes from environment variables:

- `DATABASE_URL`
- `SECRET_KEY`
- cookie settings
- allowed origins
- rate limit values
- penalty rate

This keeps secrets out of source code and makes Railway deployment predictable.

### `app/db/`

Database foundation.

- `base.py` contains the SQLAlchemy base class
- `session.py` creates the engine and session factory
- `models/` stores normalized ORM models

### `app/schemas/`

Pydantic schemas define request/response contracts. This reduces malformed input and accidental data leakage.

### `app/api/routers/`

HTTP endpoints only. Routers should stay thin and delegate important logic to services.

### `app/services/`

Business logic layer. Sensitive behaviors such as overlap checks, maintenance transitions, and penalty generation belong here.

### `app/security/`

Security-specific code:

- password hashing
- rate limiting
- RBAC dependencies
- session helpers

## 4. Data Flow

Typical request path:

1. Request enters router
2. Router validates payload through Pydantic schema
3. Auth dependency loads current user from session
4. RBAC dependency verifies role
5. Service layer runs business logic
6. SQLAlchemy persists changes to PostgreSQL
7. Router returns controlled response model

## 5. Current Feature Coverage

The scaffold includes baseline routes for:

- `auth`
- `users`
- `labs`
- `equipments`
- `reservations`
- `maintenance`
- `borrowings`
- `penalties`
- `notifications`
- `admin`
- `staff`

## 6. Known Simplifications

This scaffold is intentionally conservative and incomplete in a few places:

- it uses session middleware rather than a full custom session store
- it still relies on application-level handling around database constraint failures for reservation conflicts

## 7. Recommended Next Engineering Steps

1. Expand audit log coverage and retention policy
2. Add integration tests for RBAC and critical workflows
3. Add staging environment on Railway before production rollout
4. Add structured operational logging and alerting
5. Add end-to-end tests against PostgreSQL migrations in CI
