# Setup

## Requirements

- Python 3.12.3
- `uv` package manager

Project dependency definition: [pyproject.toml](../pyproject.toml)

## Install Dependencies

```bash
uv sync
```

## Run the Backend

```bash
uv run uvicorn app.main:app --reload
```

Application entrypoint: [app/main.py](../app/main.py)

## Initial User Bootstrap

Registration behavior is implemented in [app/services/auth_service.py](../app/services/auth_service.py).

- The first registered user becomes `admin`
- Every later self-registered user becomes `viewer`
- `analyst` is not accepted during normal registration
- `analyst` can only be assigned later by an `admin` through [app/routers/users.py](../app/routers/users.py)

This also applies to the deployed AWS instance.

- No user has been pre-created by us there
- The first successful registration on the deployed app will become `admin`

## Open the Backend

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`
- Root route: `http://127.0.0.1:8000/`
- Health route: `http://127.0.0.1:8000/health`

Current deployed instance:

- Base URL: `http://13.233.155.129:8000`
- Swagger UI: `http://13.233.155.129:8000/docs`
- Health route: `http://13.233.155.129:8000/health`

Health routes are defined in [app/routers/health.py](../app/routers/health.py).

## Run Lint

```bash
uv run pylint app tests
```

Pylint config: [.pylintrc](../.pylintrc)

## Run Automated Tests

The project test suite uses the Python standard library `unittest` module, so it does not need an extra test dependency.

```bash
uv run python -m unittest discover -s tests -v
```

Test suite location: [tests/](../tests)

## Reset the Local Database

The project uses the SQLite file [finance.db](../finance.db).

Delete it and restart the app:

```bash
rm finance.db
uv run uvicorn app.main:app --reload
```

Tables are recreated automatically from [app/main.py](../app/main.py) using metadata from [app/models/](../app/models).

## Logs

Structured logs are written to the local [logs/](../logs) directory.

Logging source files:

- [app/core/logging_config.py](../app/core/logging_config.py)
- [app/core/middleware.py](../app/core/middleware.py)
