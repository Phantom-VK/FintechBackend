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
- App configuration: [app/core/config.py](../app/core/config.py)
- Database setup: [app/db/session.py](../app/db/session.py)
- Logging setup: [app/core/logging_config.py](../app/core/logging_config.py)
- Exception classes: [app/core/exceptions.py](../app/core/exceptions.py)

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
- Core: [app/core/](../app/core)
  - configuration, security, logging, middleware, and exceptions
- DB: [app/db/](../app/db)
  - database engine, session, and base model setup

## Logging and Exceptions

Structured JSON logging is configured in [app/core/logging_config.py](../app/core/logging_config.py) and request context binding is handled by [app/core/middleware.py](../app/core/middleware.py).

Application exceptions are defined in [app/core/exceptions.py](../app/core/exceptions.py) and handled centrally in [app/main.py](../app/main.py).

## Related Docs

- Setup guide: [docs/setup.md](setup.md)
- API reference: [docs/api.md](api.md)
- Models reference: [docs/models.md](models.md)
- Database notes: [docs/database.md](database.md)
