---
name: code-review
description: >
  Five-axis code review for this NestJS/TypeScript project. Trigger for any
  review request, before merging, or after implementing a feature. Checks
  correctness, security, architecture (DDD layers), performance, and readability.
  Produces a severity-classified findings table.
---

# Code Review — NestJS / TypeScript

Adapted from CodeRabbit code-review skill, tuned for this project.

---

## Step 1 — Scope

```bash
# What changed on this branch vs main?
git diff main...HEAD --name-only
git diff main...HEAD --stat
```

If reviewing a specific file, read it first before making any findings.

---

## Step 2 — Five-Axis Review

For each changed file, evaluate:

| Axis | What to check |
|------|--------------|
| **Correctness** | Logic errors, off-by-one, unhandled null/undefined, missing await on async calls |
| **Security** | SQL injection (raw queries), missing auth guards, exposed sensitive data in responses, unvalidated inputs, JWT scope leaks |
| **Architecture** | DDD layer violations (e.g., TypeORM entity in domain layer, HTTP types in use-case), circular imports, missing repository interface |
| **Performance** | N+1 queries (missing `relations` in TypeORM), missing indexes, loading entire table without pagination |
| **Readability** | Misleading names, dead code, duplicated logic that should be extracted |

---

## Step 3 — Output Findings Table

```
## Code Review — [branch or PR name]

| # | Severity | File | Finding | Recommendation |
|---|----------|------|---------|----------------|
| 1 | 🔴 CRITICAL | src/modules/member/... | SQL injection via raw query | Use TypeORM query builder |
| 2 | 🟠 HIGH | src/modules/... | Missing @UseGuards(JwtAuthGuard) | Add guard to endpoint |
| 3 | 🟡 MEDIUM | src/modules/... | N+1 query in findAll | Add relations: ['subscription'] |
| 4 | 🔵 LOW | src/modules/... | Variable name 'data' too generic | Rename to 'memberProfile' |
```

Severity:
- 🔴 CRITICAL — security vulnerability, data corruption, crash
- 🟠 HIGH — bug, auth bypass, wrong behavior
- 🟡 MEDIUM — performance issue, DDD violation, missing validation
- 🔵 LOW — naming, style, minor improvement

---

## Step 4 — Fix Workflow

For CRITICAL and HIGH findings, fix immediately:
1. Read the file
2. Apply the minimal correct fix
3. Re-check the surrounding code for the same pattern
4. Run `npm run build` to confirm no TypeScript errors
5. Run `npm run test` to confirm tests still pass

For MEDIUM/LOW, list as recommendations — don't fix without user approval.

---

## Step 5 — Verify Clean

After fixes:
```bash
npm run build
npm run test
git diff --stat  # confirm only intended files changed
```

---

## Project-Specific Checks

- All new endpoints have `@UseGuards(JwtAuthGuard)` unless intentionally public
- All DTOs use `class-validator` decorators
- No `any` type in use-case or domain layer
- No direct `MemberEntity` (TypeORM) imports inside `application/` or `domain/`
- Error filter `MemberErrorFilter` handles domain errors — don't swallow them with try/catch
- Pagination: `findAll` endpoints must accept `page` and `limit` params
- Swagger: every endpoint has `@ApiOperation` and `@ApiResponse`
