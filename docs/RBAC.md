# RBAC Guide

## 1. Roles

The system defines four roles:

- `Student`
- `Staff`
- `Technician`
- `Admin`

Newly registered users always receive `Student`.

## 2. Permission Matrix

### Student

- view available labs
- view available equipment
- create reservations
- cancel own reservations
- create maintenance reports
- view own borrowings
- view own penalties
- view own notifications

### Technician

- all Student-safe self-service permissions if you choose to allow them
- view maintenance queue
- update maintenance status
- mark repaired equipment as available

### Staff

- view operational summary reports
- update borrowing returns
- trigger penalty generation through return flow

### Admin

- create and manage labs
- create and manage equipment
- change user roles
- later: manage categories, lab types, audit review, and staff tooling

## 3. Enforcement Strategy

This scaffold uses dependency-based authorization.

Examples:

- `require_roles("Admin")`
- `require_roles("Staff", "Admin")`
- `require_roles("Technician", "Admin")`

This should be combined with ownership checks where needed.

## 4. Ownership Rules

Role checks alone are not enough.

Examples:

- a student can cancel only their own reservation
- a student can view only their own penalties
- a student can view only their own notifications

This pattern should be preserved when new endpoints are added.

## 5. Recommended Future Enhancements

- permission table for finer-grained auth
- audit logging for role changes
- approval flow for special reservations
- separate admin UI and operator UI

