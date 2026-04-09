# Security Guide

## 1. Security Goals

The Smart Lab system stores user identities, reservation history, borrowing records, maintenance activity, and penalties. The baseline must protect:

- credentials
- session integrity
- authorization boundaries
- resource state integrity
- sensitive operational actions

## 2. Authentication Model

### Registration

- New users register with email and password
- Every newly registered user receives the `Student` role by default
- Higher privileges are assigned only by Admin

### Password Storage

Passwords are hashed with Argon2 through `pwdlib`.

Rules:

- never store plain text passwords
- never log passwords
- never expose `password_hash` in response models

### Login

Login is rate-limited to reduce brute-force pressure.

Current baseline:

- 5 attempts per minute per client address

Recommended upgrades:

- account-based throttling
- temporary lockout or progressive delay
- suspicious login monitoring

## 3. Session Security

This scaffold uses cookie-backed sessions because this is a web app, not a multi-client token platform.

Current controls:

- `SameSite=lax`
- `https_only` in production
- configurable session lifetime
- CSRF token required on authenticated mutating requests
- trusted host validation through `ALLOWED_HOSTS`

Recommended upgrades:

- rotate session on login
- force re-auth for high-risk admin actions
- add idle timeout and absolute timeout policy

## 4. Authorization Model

Authorization is enforced in two layers:

1. role checks
2. ownership checks

Examples:

- A `Student` can cancel only their own reservation
- A `Technician` can update maintenance queues
- A `Staff` user can mark returns
- An `Admin` can change roles and manage master data

Never rely only on frontend hiding. Every protected action must be enforced on the backend.

## 5. Threat Model

### Threat: Brute Force Login

Mitigations:

- login rate limiting
- strong password policy
- monitoring failed login bursts

### Threat: Broken Access Control

Mitigations:

- centralized RBAC dependency
- ownership checks
- tests for each protected route

### Threat: SQL Injection

Mitigations:

- ORM queries
- request validation
- no dynamic SQL from user input

### Threat: XSS

Mitigations:

- auto-escaped templates
- no direct raw HTML rendering from user input
- later add CSP headers

### Threat: CSRF

Mitigations:

- same-site cookies
- CSRF tokens for authenticated mutating requests

### Threat: Session Theft

Mitigations:

- secure cookie settings
- HTTPS only in production
- session rotation

### Threat: Race Conditions in Reservations

Mitigations:

- service-layer overlap check now
- PostgreSQL exclusion constraint through migration
- transaction-aware implementation

### Threat: Privilege Escalation

Mitigations:

- default `Student` role on registration
- admin-only role assignment
- audit logging for role changes and operational updates

## 6. Security Checklist Before Production

- replace development secret key
- enforce HTTPS only
- add database migrations
- add role seeding migration
- add structured logging
- add monitoring for login abuse
- separate staging and production environments
