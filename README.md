# FintechBackend

Simple FastAPI backend for the finance assignment.

## Structure

```text
app/
  main.py
  config.py
  database.py
  logging_config.py
  middleware.py
  security.py
  models/
  schemas/
  routers/
  services/
  dependencies/
```

## Setup

```bash
uv sync
```

## Run

```bash
uv run uvicorn app.main:app --reload
```

## Endpoints

- `GET /`
- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `GET /users`
- `PATCH /users/{user_id}/status`

## Notes

- The first registered user becomes `admin`.
- Every user registered after that becomes `viewer`.
- Requests return an `X-Request-ID` header for log correlation.
- Logs are emitted as structured JSON and do not log passwords, tokens, or request bodies.
- Logs are also written to timestamped files inside the local `logs/` folder.
