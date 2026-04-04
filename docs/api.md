# API Reference

Main router registration happens in [app/main.py](../app/main.py).

## Health

Source file: [app/routers/health.py](../app/routers/health.py)

- `GET /`
  - returns a simple project status message
- `GET /health`
  - checks API and database availability

## Auth

Source file: [app/routers/auth.py](../app/routers/auth.py)

- `POST /auth/register`
  - creates a new user
  - first registered user becomes `admin`
  - later users default to `viewer`
- `POST /auth/login`
  - returns a bearer token
- `GET /auth/me`
  - returns the authenticated user

Register request body:

```json
{
  "username": "admin1",
  "email": "admin1@example.com",
  "password": "secret123"
}
```

Login request body:

```json
{
  "username": "admin1",
  "password": "secret123"
}
```

## Users

Source file: [app/routers/users.py](../app/routers/users.py)

All user routes are admin-only.

- `GET /users/`
  - returns all non-deleted users
- `PATCH /users/{user_id}`
  - partial update for `username`, `email`, and `role`
- `PATCH /users/{user_id}/status`
  - activate or deactivate a user
- `DELETE /users/{user_id}`
  - soft delete a user

User update request body:

```json
{
  "username": "analyst1",
  "email": "analyst1@example.com",
  "role": "analyst"
}
```

Status update request body:

```json
{
  "is_active": false
}
```

## Transactions

Source file: [app/routers/transactions.py](../app/routers/transactions.py)

### Access rules

- `admin`
  - can create, bulk create, update, and delete
- `analyst`
  - can read
- `viewer`
  - can read

### Routes

- `POST /transactions/`
  - create one transaction
- `POST /transactions/bulk`
  - create multiple transactions
- `GET /transactions/`
  - list transactions with filters, pagination, and sorting
- `GET /transactions/{transaction_id}`
  - get one transaction
- `PATCH /transactions/{transaction_id}`
  - update one transaction
- `DELETE /transactions/{transaction_id}`
  - soft delete one transaction

Create transaction request body:

```json
{
  "amount": 2500,
  "record_type": "expense",
  "category": "food",
  "record_date": "2026-04-01",
  "description": "Monthly grocery purchase"
}
```

Bulk create request body:

```json
[
  {
    "amount": 5200,
    "record_type": "income",
    "category": "salary",
    "record_date": "2026-01-05",
    "description": "January salary credit"
  },
  {
    "amount": 350,
    "record_type": "expense",
    "category": "food",
    "record_date": "2026-01-06",
    "description": "Groceries"
  }
]
```

List query parameters:

- `record_type`
- `category`
- `date_from`
- `date_to`
- `page`
- `limit`
- `sort_by`
  - `record_date`
  - `amount`
  - `created_at`
- `sort_order`
  - `asc`
  - `desc`

Example:

```text
GET /transactions/?category=food&page=1&limit=5&sort_by=amount&sort_order=asc
```

## Dashboard

Source file: [app/routers/dashboard.py](../app/routers/dashboard.py)

Accessible to `admin`, `analyst`, and `viewer`.

- `GET /dashboard/summary`
  - total income
  - total expenses
  - net balance
  - category totals
  - recent activity
- `GET /dashboard/trends`
  - monthly income, expense, and net trend data

## Schemas

Schema source files:

- User schemas: [app/schemas/user.py](../app/schemas/user.py)
- Transaction schemas: [app/schemas/transaction.py](../app/schemas/transaction.py)
- Dashboard schemas: [app/schemas/dashboard.py](../app/schemas/dashboard.py)
