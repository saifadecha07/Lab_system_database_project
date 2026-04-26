---
name: devops
description: >
  DevOps workflow for this project: Docker, database migrations, seeding,
  environment setup, and deployment checks. Use when setting up the dev
  environment, running migrations, or preparing for deployment.
---

# DevOps — Docker / PostgreSQL / NestJS

---

## Local Dev Setup

```bash
# Start all services (Postgres + backend)
docker-compose up -d

# Verify services
docker-compose ps

# Check backend logs
docker-compose logs -f backend

# Stop
docker-compose down
```

---

## Database Workflow

### Migrations

```bash
# Generate migration from entity changes
npx typeorm migration:generate src/migrations/MigrationName -d src/data-source.ts

# Run pending migrations
npx typeorm migration:run -d src/data-source.ts

# Revert last migration
npx typeorm migration:revert -d src/data-source.ts

# Show migration status
npx typeorm migration:show -d src/data-source.ts
```

**Rules:**
- Never use `synchronize: true` in production or staging
- Every schema change needs a migration — no exceptions
- Migrations must be reversible (include `down()` method)
- Test migration on a copy of prod data before deploying

### Seeding

```bash
# Run full seed (all modules)
node scripts/sync-and-seed.js

# Or run SQL seed directly
psql $DATABASE_URL < db/seeds/seed_all_modules.sql
```

---

## Environment Variables

Required in `.env` (never commit):
```
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
JWT_SECRET=<random 64-char string>
JWT_EXPIRES_IN=1h
NODE_ENV=development
PORT=3000
```

Check all vars are set before deploying:
```bash
node -e "
const required = ['DATABASE_URL','JWT_SECRET','JWT_EXPIRES_IN','NODE_ENV'];
const missing = required.filter(k => !process.env[k]);
if (missing.length) { console.error('MISSING:', missing); process.exit(1); }
console.log('All env vars present');
"
```

---

## Build & Run

```bash
# Development (hot reload)
npm run start:dev

# Production build
npm run build
npm run start:prod

# TypeScript check (no emit)
npm run build -- --noEmit
```

---

## Docker Compose Checks

Before starting:
```bash
# Verify docker-compose.yml has correct image versions
grep -E "image:|postgres" docker-compose.yml

# Check port conflicts
docker-compose config --services
```

Common issues:
| Problem | Fix |
|---------|-----|
| Port 5432 already in use | `docker ps` → stop conflicting container |
| Backend can't reach DB | Check `DATABASE_URL` uses Docker service name not `localhost` |
| Migrations not running on start | Add `npm run migration:run` to Docker CMD or entrypoint |
| Seed fails with duplicate key | Clear DB first: `docker-compose down -v` |

---

## Pre-Deployment Checklist

- [ ] `npm run build` passes with zero TypeScript errors
- [ ] `npm run test` passes
- [ ] `npm audit --audit-level=high` — no HIGH/CRITICAL
- [ ] All migrations have been generated for schema changes
- [ ] `NODE_ENV=production` — no dev dependencies in runtime
- [ ] `.env` not in git (`git status` check)
- [ ] `docker-compose.yml` not using `:latest` tags in production
- [ ] Health check endpoint `/health` returns 200

---

## Useful Docker Commands

```bash
# Rebuild backend image after code changes
docker-compose build backend

# Open psql shell in DB container
docker-compose exec db psql -U postgres -d dbname

# Run a one-off command inside the backend container
docker-compose run --rm backend npm run migration:run

# Check disk usage
docker system df
```
