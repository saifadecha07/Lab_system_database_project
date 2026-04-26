---
name: debug-fix
description: >
  Systematic debugging for this NestJS backend. Use when a test fails, an
  endpoint returns wrong data, or behavior doesn't match the API spec.
  Follows Reproduce → Localize → Root-Cause → Fix → Guard pattern.
---

# Debug & Fix — NestJS Backend

## Scientific Method: Never guess. Prove each step.

---

## Phase 1 — Reproduce

Get a minimal reproduction before touching any code.

```bash
# Run all tests — find failing ones
npm run test 2>&1 | grep -E "(FAIL|✕|×)"

# Run specific test file
npm run test -- src/modules/member/...spec.ts --verbose

# Run e2e tests
npm run test:e2e

# Check Docker services are up
docker-compose ps
docker-compose logs --tail=50 backend
```

**Write down the exact failure:**
```
FAILURE: [exact error message + stack trace line]
EXPECTED: [what should happen]
ACTUAL: [what is happening]
REPRODUCES: [yes/no — can you trigger it consistently?]
```

---

## Phase 2 — Localize

Find the smallest unit that fails.

For **runtime errors**:
1. Read the stack trace — find the first line inside `src/` (not `node_modules/`)
2. Read that file + the 3 files it imports
3. Check if the error is in domain, application, or infrastructure layer

For **wrong HTTP response**:
1. Check controller → use-case → repository chain
2. Read the TypeORM query — is it returning what you expect?
3. Check if error filter is swallowing errors silently

For **test failures**:
1. Read the test file to understand what it expects
2. Read the implementation it's testing
3. Check if mocks/stubs match the real interface

---

## Phase 3 — Form Hypothesis

State the hypothesis explicitly:
```
HYPOTHESIS: The bug is in [file:line] because [reason].
EVIDENCE: [what you observed that points here]
PREDICTION: If I fix [X], the test/behavior will [Y].
```

Do not fix until the hypothesis is specific enough to make a prediction.

---

## Phase 4 — Fix

Apply the **minimal** fix:
- Fix the root cause, not the symptom
- Don't add try/catch to hide errors — fix the actual issue
- Don't change unrelated code

Common NestJS fixes:
```typescript
// Missing await — most common async bug
const member = await this.memberRepo.findById(id); // not: this.memberRepo.findById(id)

// TypeORM relation not loaded
const member = await this.repo.findOne({ where: { id }, relations: ['subscription'] });

// DTO not validated — add to main.ts if missing
app.useGlobalPipes(new ValidationPipe({ whitelist: true, forbidNonWhitelisted: true }));

// Guard missing
@UseGuards(JwtAuthGuard)
@Get(':id')

// Wrong error thrown (use domain error, not generic Error)
throw new MemberNotFoundError(id); // not: throw new Error('not found')
```

---

## Phase 5 — Guard (prevent regression)

After fixing:
1. Add or update the test that would have caught this bug
2. Run the full test suite — confirm it passes
3. State what the regression test covers

```bash
npm run test -- --testPathPattern=member --verbose
npm run build
```

---

## Common Bugs in This Project

| Symptom | Likely Cause | Where to Look |
|---------|-------------|--------------|
| 401 on valid token | Missing JwtAuthGuard or wrong guard order | `*.controller.ts` |
| 404 but record exists | Wrong query or missing scope filter | `*.repository.ts` |
| DTO fields ignored | Missing ValidationPipe or `@Body()` | `main.ts`, `*.controller.ts` |
| TypeORM relation undefined | Missing `relations` option | `*.repository.ts` |
| Test passes alone, fails together | Shared DB state, missing cleanup | `*.spec.ts` beforeEach/afterEach |
| Domain error not returned as HTTP error | Missing error filter binding | `*.module.ts`, `*.controller.ts` |
