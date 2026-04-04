# Models

SQLAlchemy models live in [app/models/](../app/models).

## User

Source file: [app/models/user.py](../app/models/user.py)

Fields:

- `id`
- `username`
- `email`
- `hashed_password`
- `role`
- `is_active`
- `is_deleted`
- `created_at`

Role enum:

- `viewer`
- `analyst`
- `admin`

## FinancialRecord

Source file: [app/models/transaction.py](../app/models/transaction.py)

Fields:

- `id`
- `amount`
- `record_type`
- `category`
- `record_date`
- `description`
- `created_by`
- `is_deleted`
- `created_at`
- `updated_at`

Record type enum:

- `income`
- `expense`

## Relationships

- One user can own many records.
- `FinancialRecord.created_by` points to `User.id`.
- ORM relationships are defined in:
  - [app/models/user.py](../app/models/user.py)
  - [app/models/transaction.py](../app/models/transaction.py)

## Response and Request Schemas

Pydantic models live in [app/schemas/](../app/schemas):

- [app/schemas/user.py](../app/schemas/user.py)
- [app/schemas/transaction.py](../app/schemas/transaction.py)
- [app/schemas/dashboard.py](../app/schemas/dashboard.py)
