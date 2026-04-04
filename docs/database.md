# Database

Database configuration lives in [app/config.py](../app/config.py) and [app/database.py](../app/database.py).

## Current Database

The project currently uses SQLite through the local file [finance.db](../finance.db).

Configured database URL:

- [app/config.py](../app/config.py)

Session and engine setup:

- [app/database.py](../app/database.py)

## Tables

Current tables are defined by:

- [app/models/user.py](../app/models/user.py)
- [app/models/transaction.py](../app/models/transaction.py)

Tables:

- `users`
- `financial_records`

## Table Creation

Tables are created automatically during app startup in [app/main.py](../app/main.py).

## Reset Strategy

Since the current project does not use migrations yet, the simplest local reset is:

```bash
rm finance.db
uv run uvicorn app.main:app --reload
```

## Important Notes

- Deleted users are soft deleted with `is_deleted`
- Deleted transactions are soft deleted with `is_deleted`
- Enums are stored as lowercase values like `admin`, `analyst`, `viewer`, `income`, and `expense`

## Related Files

- App bootstrap: [app/main.py](../app/main.py)
- DB setup: [app/database.py](../app/database.py)
- User model: [app/models/user.py](../app/models/user.py)
- Transaction model: [app/models/transaction.py](../app/models/transaction.py)
