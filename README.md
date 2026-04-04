# FintechBackend

![Python](https://img.shields.io/badge/Python-3.12.3-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![uv](https://img.shields.io/badge/uv-package%20manager-5C5CFF)
![Structlog](https://img.shields.io/badge/Structlog-JSON%20logging-3A7D44)

Simple FastAPI backend for finance data processing, access control, transaction management, dashboard reporting, structured logging, and custom exception handling.

## Project Overview

This backend provides:

- JWT-based authentication
- Role-based access control for `admin`, `analyst`, and `viewer`
- User management with admin-only updates and soft delete
- Transaction CRUD, bulk create, filtering, pagination, and sorting
- Dashboard summary and trend APIs
- Structured request logging and safe custom exceptions

Main application entrypoint: [app/main.py](app/main.py)

## Tech Stack

- Python 3.12.3
- FastAPI: [pyproject.toml](pyproject.toml)
- SQLAlchemy ORM: [app/database.py](app/database.py)
- SQLite database: [app/config.py](app/config.py)
- JWT auth and password hashing: [app/security.py](app/security.py)
- Structured JSON logging: [app/logging_config.py](app/logging_config.py)

## Documentation

- Project information: [docs/project-info.md](docs/project-info.md)
- Local setup and commands: [docs/setup.md](docs/setup.md)
- API reference: [docs/api.md](docs/api.md)
- Data models and enums: [docs/models.md](docs/models.md)
- Database details: [docs/database.md](docs/database.md)

## Source Layout

- Application code: [app/](app)
- Routers: [app/routers/](app/routers)
- Services: [app/services/](app/services)
- Models: [app/models/](app/models)
- Schemas: [app/schemas/](app/schemas)
- Dependencies: [app/dependencies/](app/dependencies)
- Static assets: [static/](static)
- Automated tests: [tests/](tests)

## Quick Start

Install dependencies:

```bash
uv sync
```

Run the backend:

```bash
uv run uvicorn app.main:app --reload
```

Open:

- Swagger UI: `http://127.0.0.1:8000/docs`
- Root endpoint: `http://127.0.0.1:8000/`
- Health endpoint: `http://127.0.0.1:8000/health`

For full setup, test, and reset instructions, use [docs/setup.md](docs/setup.md).
