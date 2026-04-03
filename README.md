# FintechBackend

Simple FastAPI backend for the finance assignment.

## Structure

```text
app/
  main.py
  config.py
  database.py
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
