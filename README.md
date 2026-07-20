# Cloud Atlas Tags API

[![CI](https://github.com/Acauhi99/cloud-atlas/actions/workflows/ci.yml/badge.svg)](https://github.com/Acauhi99/cloud-atlas/actions/workflows/ci.yml)

REST API for managing user-scoped Tags and their associated Values. Built with FastAPI, SQLAlchemy 2.x async, PostgreSQL, and Alembic.

## Stack

- Python 3.14+ / FastAPI / Pydantic v2
- SQLAlchemy 2.x async (asyncpg)
- PostgreSQL 16
- Alembic migrations
- pytest + pytest-asyncio + HTTPX
- Ruff + mypy
- Docker multi-stage build

## Quick Start

### Prerequisites

- Python 3.14+
- PostgreSQL 16+
- uv

### Local Development

```bash
# Install dependencies
uv sync

# Create database
createdb cloud_atlas

# Run migrations
uv run alembic upgrade head

# Start the API
uv run uvicorn app.main:app --reload
```

### Environment Variables

```bash
APP_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/cloud_atlas
APP_LOG_LEVEL=INFO
APP_PORT=8000
```

### Docker Compose

```bash
docker compose up --build
```

## API

Every request requires the `X-User-ID` header (UUID). All endpoints are versioned under `/v1`:

```bash
curl -H "X-User-ID: 39e77112-bb38-475f-9e94-d3a27fe80c46" http://localhost:8000/v1/tags
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/tags` | List tags (paginated) |
| POST | `/v1/tags` | Create tag (optionally with values) |
| GET | `/v1/tags/{tag_id}` | Get tag |
| PATCH | `/v1/tags/{tag_id}` | Update tag |
| DELETE | `/v1/tags/{tag_id}` | Delete tag (cascades to values) |
| GET | `/v1/tags/{tag_id}/values` | List values |
| POST | `/v1/tags/{tag_id}/values` | Create value |
| GET | `/v1/tags/{tag_id}/values/{value_id}` | Get value |
| PATCH | `/v1/tags/{tag_id}/values/{value_id}` | Update value |
| DELETE | `/v1/tags/{tag_id}/values/{value_id}` | Delete value |
| GET | `/v1/health` | Health check |
| GET | `/v1/ready` | Readiness check |

### Example Requests

```bash
# Create tag with values
curl -X POST http://localhost:8000/v1/tags \
  -H "X-User-ID: 39e77112-bb38-475f-9e94-d3a27fe80c46" \
  -H "Content-Type: application/json" \
  -d '{"name": "team", "description": "Team tag", "values": [{"name": "atlas"}]}'

# List tags with pagination
curl "http://localhost:8000/v1/tags?page=1&page_size=20&name=team" \
  -H "X-User-ID: 39e77112-bb38-475f-9e94-d3a27fe80c46"
```

### Validation Rules

- Names: 3-64 characters, lowercase ASCII letters, digits, underscore, or hyphen (`^[a-z0-9_-]{3,64}$`)
- Descriptions: optional, nullable
- Tag names unique per user (DB constraint)
- Value names unique per tag (DB constraint)

### Error Format (RFC 9457)

```json
{
  "type": "about:blank",
  "title": "Conflict",
  "status": 409,
  "detail": "A tag with this name already exists",
  "instance": "/v1/tags"
}
```

### Rate Limiting

All endpoints are rate-limited to **60 requests per minute** per user (identified by `X-User-ID` header).

**Response headers:**

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
```

When the limit is exceeded, the API returns `429 Too Many Requests`:

```json
{
  "detail": "Rate limit exceeded"
}
```

### Request ID

Every response includes an `X-Request-ID` header for request tracing and debugging:

```
X-Request-ID: 39e77112-bb38-475f-9e94-d3a27fe80c46
```

You can provide your own request ID in the request header, or the API will generate one automatically.

## Development

### Before Committing

Every code change must pass these checks before commit. Lefthook runs them automatically on `git commit`:

```bash
uv run ruff format --check .   # formatting
uv run ruff check .            # lint
uv run mypy app                # typecheck
uv run pytest                  # tests (requires PostgreSQL)
```

If any check fails, the commit is blocked. Fix the issues and try again.

To skip hooks temporarily (not recommended): `git commit --no-verify`

### Setup Hooks

```bash
lefthook install
```

This installs pre-commit hooks that run format, lint, typecheck, and tests on every commit.

### Manual Checks

```bash
# Run all checks manually
uv run ruff format --check .
uv run ruff check .
uv run mypy app
uv run pytest

# Run tests with verbose output
uv run pytest tests/ -v
```

## Architecture

```
app/
├── main.py              # FastAPI app, middleware, router registration
├── exceptions.py        # AppError hierarchy
├── api/
│   ├── dependencies.py  # X-User-ID extraction, session
│   ├── error_handlers.py
│   └── v1/              # API version 1 routes
│       ├── health.py
│       ├── tags.py
│       └── values.py
├── core/
│   ├── config.py        # Pydantic Settings (APP_ env prefix)
│   ├── logging.py       # Structured logging, request_id context var
│   └── rate_limit.py    # Rate limiting middleware
├── db/                  # models, session factory
├── repositories/        # SQLAlchemy queries
├── schemas/             # Pydantic request/response
└── services/            # Business logic, transactions
```

Request flow: Router → Service → Repository → AsyncSession → PostgreSQL

### API Versioning

The API uses URL-based versioning (`/v1/`). When breaking changes are needed:

1. Create a new version directory: `app/api/v2/`
2. Register the new router with prefix `/v2`
3. Keep the old version running for backward compatibility
4. Document deprecation timeline

This allows clients to migrate at their own pace.

## CI/CD

Both GitHub Actions and GitLab CI pipelines run automatically on every push and pull request.

### Pipeline Jobs

All jobs run in parallel:

- **lint**: Ruff formatting and linting
- **typecheck**: mypy type checking
- **test**: pytest with PostgreSQL service
- **audit**: pip-audit vulnerability scanning
- **deps**: uv lock file consistency check
- **docker**: Docker image build (no push)

### GitHub Actions

Workflow: `.github/workflows/ci.yml`

Features:
- Automatic cancellation of outdated runs (`cancel-in-progress`)
- uv dependency caching
- PostgreSQL service container for tests

### GitLab CI

Configuration: `.gitlab-ci.yml`

Features:
- All jobs in single stage (parallel execution)
- `interruptible: true` for automatic cancellation
- uv cache keyed by `uv.lock`
- PostgreSQL service for tests
- Docker-in-Docker for image builds

## Client SDK Generation

Generate type-safe client SDKs from the OpenAPI specification:

```bash
# Start the API server
uv run uvicorn app.main:app --reload

# Generate TypeScript/Axios client
./scripts/generate-client.sh typescript-axios ./clients/typescript

# Generate Python client
./scripts/generate-client.sh python ./clients/python

# Generate Go client
./scripts/generate-client.sh go ./clients/go
```

Supported languages: TypeScript, Python, Go, Java, Kotlin, Swift, Dart, Ruby, PHP, C#, and 30+ more.

The script uses [openapi-generator-cli](https://openapi-generator.tech/) and reads from `http://localhost:8000/openapi.json`.

## Design Decisions

- User identification via header, no auth infrastructure
- Service layer owns transaction boundaries and IntegrityError → 409 mapping
- `selectinload` for eager-loading tag values (avoids N+1)
- Repository layer scoped by user_id for ownership isolation
- Alembic for schema migrations (not `create_all`)
- Rate limiting in memory (not distributed) — upgrade to Redis when scaling horizontally
