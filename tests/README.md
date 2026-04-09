# Tests

Executable coverage now includes:

- registration assigns `Student`
- authenticated mutating routes require CSRF token
- students cannot access admin routes
- reservation overlap is rejected
- late return creates penalty and audit log

Recommended next additions:

- login rate limiting
- technician can close maintenance record
- audit log coverage for admin role changes
