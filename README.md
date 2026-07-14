# ERP Inventory & Sales Management — FastAPI Backend

## Quick Start

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- MongoDB (local or Atlas)
- Redis (optional — falls back to in-memory if not configured)

### Setup

```bash
# Clone and cd into project
cd erp-BE-fastapi

# Install dependencies
uv sync

# Populate database with default roles, permissions, admin user, and sample data
uv run python scripts/seed.py

# Start the server
uv run uvicorn app.main:socket_app --host 0.0.0.0 --port 5001 --reload
```

### Default credentials (after seeding)

| Role     | Email              | Password      |
|----------|--------------------|---------------|
| Admin    | admin@erp.com      | Admin@123     |
| Manager  | manager@erp.com    | Manager@123   |
| Employee | employee@erp.com   | Employee@123  |

### Docker

```bash
docker compose up -d    # starts MongoDB + Redis + App
```

## Commands

```bash
uv run pytest tests/ -v          # Run tests
uv run ruff check app/ tests/    # Lint
uv run ruff format app/ tests/   # Format
uv run mypy app/                 # Type check
uv run python scripts/seed.py    # Seed database
```

## Architecture

```
app/
├── main.py                  # App factory, middleware, lifespan
├── router.py                # Aggregates all API routers
├── socketio.py              # WebSocket events (low-stock alerts)
├── core/                    # Framework foundation
│   ├── config.py            # pydantic-settings
│   ├── security.py          # JWT, password hashing
│   ├── deps.py              # FastAPI dependencies (auth, RBAC)
│   ├── exceptions.py        # Custom exceptions + handlers
│   ├── http_status.py       # HTTP status code constants
│   └── models/base.py       # BaseDocument Pydantic model
├── infrastructure/          # External adapters
│   ├── mongo/               # MongoDB client + BaseRepository
│   ├── cloudinary.py        # Image upload/delete
│   ├── rate_limiter.py      # slowapi limiter + rate_limit helper
│   ├── logging.py           # structlog + request logging middleware
│   └── cache.py             # TTL in-memory cache
├── schemas/
│   └── response.py          # Standardized API response format
└── modules/                 # Bounded contexts (modular monolith)
    ├── auth/                # Login, logout, current user
    ├── users/               # User CRUD
    ├── roles/               # Role + Permission CRUD
    ├── categories/          # Category CRUD
    ├── products/            # Product CRUD + image upload
    ├── sales/               # Sale creation + history
    └── dashboard/           # Statistics + low-stock alerts
```

## API Documentation

Once running, open the interactive docs:
- Swagger UI: http://localhost:5001/api-docs
- OpenAPI JSON: http://localhost:5001/api-docs.json

## Environment Variables

| Variable              | Default                        | Description                    |
|-----------------------|--------------------------------|--------------------------------|
| `PORT`                | `5000`                         | Server port                    |
| `MONGODB_URI`         | `mongodb://localhost:27017`    | MongoDB connection string      |
| `DB_NAME`             | `erp-fastapi`                  | Database name                  |
| `JWT_SECRET`          | —                              | JWT signing secret             |
| `JWT_EXPIRES_IN`      | `1d`                           | Token expiry                   |
| `CLOUDINARY_CLOUD_NAME`| —                             | Cloudinary cloud name          |
| `CLOUDINARY_API_KEY`  | —                              | Cloudinary API key             |
| `CLOUDINARY_API_SECRET`| —                             | Cloudinary API secret          |
| `CLIENT_URL`          | `http://localhost:5173`        | CORS allowed origin            |
| `REDIS_URL`           | (empty)                        | Redis URL — memory fallback if unset |
| `NODE_ENV`            | `development`                  | Environment                    |
| `LOG_LEVEL`           | `info`                         | Logging level                  |
