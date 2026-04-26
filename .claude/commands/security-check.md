---
name: security-check
description: >
  Security audit for this NestJS REST API. Trigger before PR merge, after
  auth changes, or when handling sensitive data. Checks OWASP Top 10,
  JWT/auth hardening, SQL injection, and input validation.
---

# Security Check — NestJS API

Adapted from Trail of Bits audit methodology + OWASP Top 10.

---

## Scope

```bash
# See what changed
git diff main...HEAD --name-only | grep -E "\.(ts|sql|env)$"
```

---

## Checklist — run through every changed file

### Authentication & Authorization
- [ ] All non-public endpoints have `@UseGuards(JwtAuthGuard)`
- [ ] JWT secret is from `ConfigService` — never hardcoded
- [ ] Role/scope checks are done server-side (never trust client claims)
- [ ] Token expiry is set (no `expiresIn: '100y'`)
- [ ] Refresh token rotation is implemented if used

### Input Validation
- [ ] All controller params use `class-validator` decorators (`@IsUUID`, `@IsString`, `@IsEmail`, etc.)
- [ ] `ValidationPipe({ whitelist: true, forbidNonWhitelisted: true })` is active globally
- [ ] No raw user input passed to TypeORM `query()` or `createQueryBuilder().where(raw_string)`
- [ ] File uploads (if any) have size + type limits

### SQL / Injection
- [ ] Use TypeORM query builder parameterized queries — never string concatenation
- [ ] Search/filter inputs are validated before use in `.where()` clauses
- [ ] Check `db/seeds/` and `db/scripts/` — no raw SQL with user data

### Sensitive Data
- [ ] Passwords hashed with bcrypt (min cost 10) — never stored plain
- [ ] No passwords/tokens returned in API responses
- [ ] Error messages don't leak stack traces or DB schema to clients
- [ ] `.env` not committed — check `.gitignore`

### Rate Limiting & Abuse
- [ ] Auth endpoints (`/login`, `/register`, `/invite`) have rate limiting
- [ ] No endpoint allows bulk enumeration without pagination

### Dependencies
```bash
npm audit --audit-level=high
```
Fix any HIGH or CRITICAL vulnerabilities before merge.

---

## Output Format

```
## Security Audit — [scope]

| # | Severity | Finding | File | Remediation |
|---|----------|---------|------|-------------|
| 1 | 🔴 CRITICAL | Raw query with user input | member.repository.ts:45 | Use query builder params |
| 2 | 🟠 HIGH | Missing JWT guard | member.controller.ts:78 | Add @UseGuards(JwtAuthGuard) |
| 3 | 🟡 MEDIUM | Token expiry not set | auth.service.ts:12 | Add expiresIn: '1h' |
```

---

## Quick Fixes

```typescript
// SQL injection — WRONG
.where(`member.name LIKE '%${search}%'`)

// SQL injection — RIGHT
.where('member.name LIKE :search', { search: `%${search}%` })

// Missing guard
@UseGuards(JwtAuthGuard)
@Get(':id')
async getOne(@Param('id', ParseUUIDPipe) id: string) { ... }

// Expose sensitive field — WRONG
return member; // includes passwordHash

// Expose sensitive field — RIGHT
const { passwordHash, ...safeData } = member;
return safeData;

// Rate limiting (install @nestjs/throttler)
@Throttle(5, 60) // 5 requests per 60 seconds
@Post('login')
```

---

## Verify

```bash
npm audit --audit-level=high
npm run test
npm run build
```

No security fixes should break existing tests. If they do, the tests were wrong — fix both.
