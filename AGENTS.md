# Cloud Atlas Tags API

REST API for managing user-scoped Tags and their associated Values. Python 3.14, FastAPI, SQLAlchemy 2.x async, PostgreSQL, Alembic.

## Quick Commands

```bash
uv sync                          # install deps
uv run alembic upgrade head      # run migrations
uv run uvicorn app.main:app --reload  # start dev server
uv run pytest                    # run tests (needs PostgreSQL)
uv run ruff format --check .     # check formatting
uv run ruff check .              # lint
uv run mypy app                  # type check
docker compose up --build        # run with Docker
```

All commands use `uv run`. Never `pip install` or run tools outside uv.

## Pre-Commit Checks (Lefthook)

Every code change must pass these checks before commit. Lefthook runs them automatically on `git commit`:

```bash
uv run ruff format --check .   # formatting
uv run ruff check .            # lint
uv run mypy app                # typecheck
uv run pytest                  # tests
```

Setup: `lefthook install` (runs once per clone). If any check fails, the commit is blocked.

## Project Structure

```
app/
├── main.py              # FastAPI app, middleware, router registration
├── exceptions.py        # AppError hierarchy (NotFoundError, ConflictError)
├── api/
│   ├── dependencies.py  # FastAPI deps: get_user_id, get_session
│   ├── error_handlers.py
│   └── v1/              # API version 1 routes
│       ├── health.py    # GET /v1/health, GET /v1/ready
│       ├── tags.py      # CRUD /v1/tags
│       └── values.py    # CRUD /v1/tags/{tag_id}/values
├── core/
│   ├── config.py        # Pydantic Settings (APP_ env prefix)
│   ├── logging.py       # Structured logging, request_id context var
│   └── rate_limit.py    # Rate limiting middleware (60 req/min per user)
├── db/
│   ├── base.py          # SQLAlchemy DeclarativeBase
│   ├── models.py        # Tag, Value ORM models
│   └── session.py       # AsyncEngine, async_sessionmaker
├── repositories/
│   ├── tags.py          # TagRepository (SQL queries, scoped by user_id)
│   └── values.py        # ValueRepository
├── schemas/
│   ├── common.py        # NameStr, OptionalNameStr (shared validation)
│   ├── tags.py          # TagCreate, TagUpdate, TagResponse, PaginatedTagResponse
│   └── values.py        # ValueCreate, ValueUpdate, ValueResponse
└── services/
    ├── tags.py          # TagService (business logic, transactions)
    └── values.py        # ValueService
```

## Architecture Rules

Request flow is strictly layered. Never skip a layer.

```
Router → Service → Repository → AsyncSession → PostgreSQL
```

- **Routers** define routes, status codes, response models. No SQL, no business logic.
- **Services** enforce ownership rules, coordinate transactions, map IntegrityError → 409.
- **Repositories** contain SQLAlchemy statements. Scope queries by `user_id`. Use `select()` style.
- **Schemas** (Pydantic) are separate from ORM models. Never use one schema for create/update/response.

Transaction boundaries live in services. Repositories flush, never commit.

## User Scoping

Every business endpoint requires `X-User-ID` header (UUID). Extracted via `get_user_id` dependency in `api/dependencies.py`. Never query without `user_id` filter. A resource from another user returns 404, never 403.

## Rate Limiting

All endpoints are rate-limited to 60 requests per minute per user (identified by `X-User-ID`). Implemented in `core/rate_limit.py` using sliding window in memory.

Response headers:
- `X-RateLimit-Limit`: Maximum requests per minute
- `X-RateLimit-Remaining`: Requests remaining in current window

Returns `429 Too Many Requests` when limit exceeded.

**Note**: Rate limiting is in-memory (not distributed). When scaling horizontally, upgrade to Redis-based rate limiting.

## API Versioning

All routes are prefixed with `/v1`. When breaking changes are needed:

1. Create `app/api/v2/` directory
2. Copy and modify routes
3. Register new router with `prefix="/v2"` in `main.py`
4. Keep old version for backward compatibility

This allows clients to migrate at their own pace.

## Name Validation

All name fields use `NameStr` from `schemas/common.py`:
- Regex: `^[a-z0-9_-]{3,64}$`
- 3-64 chars, lowercase ASCII, digits, underscore, hyphen only
- No silent normalization — reject invalid input

## Error Handling

- App errors raise `AppError` subclasses (`NotFoundError`, `ConflictError`)
- Handled by `app_error_handler` → JSON response with `type`, `title`, `status`, `detail`, `instance`
- `IntegrityError` from SQLAlchemy → rollback → 409 Conflict
- Never catch broad exceptions and mislabel them

## Testing

Tests live in `tests/integration/`. They hit a real PostgreSQL database (`cloud_atlas_test`).

```bash
uv run pytest                    # all tests
uv run pytest tests/integration/test_tags.py -v  # specific file
```

Test patterns:
- Each test gets a fresh DB (create_all / drop_all per test via engine fixture)
- `client` fixture monkey-patches `async_session_factory` to use test DB
- Use `user_id` and `other_user_id` fixtures for ownership tests
- Concurrent tests use `asyncio.Barrier` to force race conditions

When adding tests:
- Cover CRUD + validation + ownership + edge cases
- Test error response format (RFC 9457 shape)
- Test cross-user denial returns 404, not 403
- Test session recovery after failed operations

## Database

- PostgreSQL 16, async via `psycopg` (`postgresql+asyncpg://`)
- SQLAlchemy 2.x typed declarative API
- Alembic for migrations (never `create_all` in production)
- `selectin` lazy loading on Tag.values relationship
- Cascade: `ON DELETE CASCADE` on Value.tag_id FK, `cascade="all, delete-orphan"` on ORM relationship

## Docker

- Multi-stage build: `python:3.14-slim`
- Runs as non-root `appuser` (UID 1000)
- Dependencies synced from lockfile (`--frozen --no-dev`)
- Migrations run at startup via compose command, not during image build

## Environment Variables

All prefixed with `APP_` (Pydantic Settings `env_prefix`):

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection string |
| `APP_LOG_LEVEL` | `INFO` | Logging level |
| `APP_PORT` | `8000` | API port |

## Request ID

Every response includes `X-Request-ID` header for request tracing. Set via `request_id_middleware` in `main.py`. Clients can provide their own ID or the API generates one automatically.

## Client SDK Generation

Generate type-safe clients from OpenAPI spec:

```bash
./scripts/generate-client.sh typescript-axios ./clients/typescript
./scripts/generate-client.sh python ./clients/python
```

Uses `openapi-generator-cli` and reads from `http://localhost:8000/openapi.json`. Supports 40+ languages.

## Gotchas

- `conftest.py` uses `create_all`/`drop_all` for test isolation — not Alembic. Tests don't validate migration correctness.
- PATCH endpoints reject empty body `{}` → 422.
- `OptionalNameStr` in `schemas/common.py` validates regex — use it for optional name fields.
- The `request_id_middleware` sets context vars for structured logging. Fields like `duration_ms` are populated at runtime, not in the format string defaults.
- Rate limiting is in-memory — resets on server restart. Not suitable for multi-instance deployments without Redis.
