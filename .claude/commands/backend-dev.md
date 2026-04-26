---
name: backend-dev
description: >
  NestJS backend development guide for this project. Trigger when implementing
  new features, modules, use-cases, or API endpoints. Enforces project
  conventions: DDD layering, TypeORM repositories, DTO validation, JWT auth,
  and Swagger docs.
---

# Backend Development — NestJS / TypeORM / PostgreSQL

This project follows **Domain-Driven Design** with four strict layers per module:
`domain` → `application` → `infrastructure` → `presentation`

Modules: `member`, `user`, `publisher`, `subscription`, `invitation`

---

## ASSUMPTIONS — state these before any non-trivial task

```
ASSUMPTIONS I'M MAKING:
1. [which module / layer this touches]
2. [whether a new DB migration is required]
3. [whether JWT guard/scope changes are needed]
→ Correct me now or I'll proceed with these.
```

---

## Layer Conventions

### Domain (`src/modules/<module>/domain/`)
- Pure TypeScript — zero framework imports
- Entities, Value Objects, Domain Events, Repository **interfaces**
- Throw domain-specific errors (e.g., `MemberAlreadyApprovedError`)

### Application (`src/modules/<module>/application/`)
- Use-cases only — one file per use-case
- Inject repository interfaces (not implementations)
- No HTTP/Express types allowed here

### Infrastructure (`src/modules/<module>/infrastructure/`)
- TypeORM entities (`*.entity.ts`) — decoupled from domain entities
- Repository implementations that satisfy domain interfaces
- DB migrations in `db/migrations/`

### Presentation (`src/modules/<module>/presentation/`)
- NestJS controllers, DTOs, guards, filters
- All input validated with `class-validator`
- All endpoints decorated with `@ApiOperation`, `@ApiResponse` for Swagger

---

## Checklist Before Writing Code

- [ ] Does the use-case already exist? (`src/modules/<module>/application/use-cases/`)
- [ ] Is there a TypeORM entity for the table? (`infrastructure/entities/`)
- [ ] Does the controller already have a route for this action?
- [ ] Will this change need a DB migration?

---

## Patterns

### New Use-Case
```typescript
// application/use-cases/my-action.usecase.ts
@Injectable()
export class MyActionUseCase {
  constructor(
    @Inject(MEMBER_REPOSITORY)
    private readonly memberRepo: IMemberRepository,
  ) {}

  async execute(dto: MyActionDto): Promise<void> {
    const member = await this.memberRepo.findById(dto.memberId);
    if (!member) throw new MemberNotFoundError(dto.memberId);
    // domain logic
    await this.memberRepo.save(member);
  }
}
```

### New Controller Endpoint
```typescript
@Post(':id/action')
@UseGuards(JwtAuthGuard)
@ApiOperation({ summary: 'Short description' })
@ApiResponse({ status: 200, description: 'Success' })
@ApiResponse({ status: 404, description: 'Member not found' })
async myAction(
  @Param('id', ParseUUIDPipe) id: string,
  @Body() dto: MyActionDto,
): Promise<void> {
  await this.myActionUseCase.execute({ memberId: id, ...dto });
}
```

### DTO
```typescript
export class MyActionDto {
  @IsUUID()
  @ApiProperty()
  memberId: string;

  @IsString()
  @IsNotEmpty()
  @ApiProperty()
  reason: string;
}
```

---

## Database

- TypeORM with PostgreSQL — `@nestjs/typeorm`
- Always create migrations for schema changes — never use `synchronize: true` in production
- Seed data lives in `db/seeds/`

```bash
# Generate migration
npx typeorm migration:generate -n MigrationName

# Run migrations
npx typeorm migration:run

# Seed
node scripts/sync-and-seed.js
```

---

## Error Handling

- Domain errors → caught by `MemberErrorFilter` in presentation layer
- Unhandled errors → default NestJS exception filter
- HTTP status codes must match OpenAPI spec in `promptpost4.0-api-specification-main/`

---

## Verification

After implementing:
1. `npm run build` — no TypeScript errors
2. `npm run test` — unit tests pass
3. `npm run test:e2e` — integration tests pass
4. Check Swagger UI at `/api/docs` — new endpoint visible and correct
5. Run `docker-compose up` and manually test the endpoint
