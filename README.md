# Cloud Atlas Tags API

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

Every request requires the `X-User-ID` header (UUID):

```bash
curl -H "X-User-ID: 39e77112-bb38-475f-9e94-d3a27fe80c46" http://localhost:8000/tags
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/tags` | List tags (paginated) |
| POST | `/tags` | Create tag (optionally with values) |
| GET | `/tags/{tag_id}` | Get tag |
| PATCH | `/tags/{tag_id}` | Update tag |
| DELETE | `/tags/{tag_id}` | Delete tag (cascades to values) |
| GET | `/tags/{tag_id}/values` | List values |
| POST | `/tags/{tag_id}/values` | Create value |
| GET | `/tags/{tag_id}/values/{value_id}` | Get value |
| PATCH | `/tags/{tag_id}/values/{value_id}` | Update value |
| DELETE | `/tags/{tag_id}/values/{value_id}` | Delete value |
| GET | `/health` | Health check |
| GET | `/ready` | Readiness check |

### Example Requests

```bash
# Create tag with values
curl -X POST http://localhost:8000/tags \
  -H "X-User-ID: 39e77112-bb38-475f-9e94-d3a27fe80c46" \
  -H "Content-Type: application/json" \
  -d '{"name": "team", "description": "Team tag", "values": [{"name": "atlas"}]}'

# List tags with pagination
curl "http://localhost:8000/tags?page=1&page_size=20&name=team" \
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
  "instance": "/tags"
}
```

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
├── main.py              # FastAPI app, middleware
├── api/
│   ├── dependencies.py  # X-User-ID extraction, session
│   ├── error_handlers.py
│   └── routes/          # tags.py, values.py, health.py
├── core/                # config, logging
├── db/                  # models, session factory
├── repositories/        # SQLAlchemy queries
├── schemas/             # Pydantic request/response
├── services/            # Business logic, transactions
└── exceptions.py        # AppError hierarchy
```

Request flow: Router → Service → Repository → AsyncSession → PostgreSQL

## Design Decisions

- User identification via header, no auth infrastructure
- Service layer owns transaction boundaries and IntegrityError → 409 mapping
- `selectinload` for eager-loading tag values (avoids N+1)
- Repository layer scoped by user_id for ownership isolation
- Alembic for schema migrations (not `create_all`)
