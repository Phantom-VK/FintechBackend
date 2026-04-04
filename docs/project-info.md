# Project Info

This project is a simple finance backend built with FastAPI and SQLAlchemy. The code is intentionally kept small and structured so each layer stays easy to read and extend.

## Purpose

The backend supports:

- authentication and access control
- user administration
- financial transaction management
- dashboard reporting
- structured logging
- safe application exception handling

## Main Entry Points

- Application bootstrap: [app/main.py](../app/main.py)
- App configuration: [app/config.py](../app/config.py)
- Database setup: [app/database.py](../app/database.py)
- Logging setup: [app/logging_config.py](../app/logging_config.py)
- Exception classes: [app/exceptions.py](../app/exceptions.py)

## Role Model

- `admin`
  - can manage users
  - can create, update, delete, and bulk create transactions
  - can read dashboard data
- `analyst`
  - can read transactions
  - can read dashboard data
- `viewer`
  - can read transactions
  - can read dashboard data
  - cannot create or modify transactions

Role definitions live in [app/models/user.py](../app/models/user.py).

## Backend Structure

- Routers: [app/routers/](../app/routers)
  - request handling and response models
- Services: [app/services/](../app/services)
  - simple business logic and database operations
- Models: [app/models/](../app/models)
  - SQLAlchemy tables and enums
- Schemas: [app/schemas/](../app/schemas)
  - request and response contracts
- Dependencies: [app/dependencies/](../app/dependencies)
  - auth and role-based reusable dependencies

## Logging and Exceptions

Structured JSON logging is configured in [app/logging_config.py](../app/logging_config.py) and request context binding is handled by [app/middleware.py](../app/middleware.py).

Application exceptions are defined in [app/exceptions.py](../app/exceptions.py) and handled centrally in [app/main.py](../app/main.py).

## Related Docs

- Setup guide: [docs/setup.md](setup.md)
- API reference: [docs/api.md](api.md)
- Models reference: [docs/models.md](models.md)
- Database notes: [docs/database.md](database.md)
