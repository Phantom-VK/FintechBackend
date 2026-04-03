"""Thin service functions for transaction features."""

from datetime import date
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session
import structlog

from app.exceptions import FintechBackendException
from app.models.transaction import FinancialRecord, RecordType
from app.schemas.transaction import FinancialRecordCreate, FinancialRecordUpdate


logger = structlog.get_logger(__name__)


def create_transaction(
    db: Session,
    transaction_data: FinancialRecordCreate,
    created_by: int,
) -> FinancialRecord:
    """Create a financial record."""

    logger.info(
        "transaction_create_started",
        actor_user_id=created_by,
        record_type=transaction_data.record_type.value,
        category=transaction_data.category,
    )
    transaction = FinancialRecord(
        amount=transaction_data.amount,
        record_type=transaction_data.record_type,
        category=transaction_data.category,
        record_date=transaction_data.record_date,
        description=transaction_data.description,
        created_by=created_by,
    )

    try:
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
    except Exception as exc:
        db.rollback()
        logger.exception(
            "transaction_create_failed",
            actor_user_id=created_by,
            error=str(exc),
        )
        raise FintechBackendException("Unable to create transaction", sys) from exc

    logger.info(
        "transaction_create_succeeded",
        actor_user_id=created_by,
        transaction_id=transaction.id,
    )
    return transaction


def get_transaction_by_id(
    db: Session,
    transaction_id: int,
) -> FinancialRecord | None:
    """Fetch a non-deleted financial record by id."""

    logger.info("transaction_get_requested", transaction_id=transaction_id)
    return db.scalar(
        select(FinancialRecord).where(
            FinancialRecord.id == transaction_id,
            FinancialRecord.is_deleted.is_(False),
        )
    )


def list_transactions(
    db: Session,
    record_type: RecordType | None = None,
    category: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[FinancialRecord]:
    """Return non-deleted financial records with simple filters."""

    logger.info(
        "transactions_list_requested",
        record_type=record_type.value if record_type else None,
        category=category,
        date_from=date_from.isoformat() if date_from else None,
        date_to=date_to.isoformat() if date_to else None,
    )
    query = select(FinancialRecord).where(FinancialRecord.is_deleted.is_(False))

    if record_type is not None:
        query = query.where(FinancialRecord.record_type == record_type)

    if category:
        query = query.where(FinancialRecord.category == category)

    if date_from is not None:
        query = query.where(FinancialRecord.record_date >= date_from)

    if date_to is not None:
        query = query.where(FinancialRecord.record_date <= date_to)

    transactions = db.scalars(
        query.order_by(FinancialRecord.record_date.desc(), FinancialRecord.id.desc())
    ).all()
    transaction_list = list(transactions)
    logger.info("transactions_list_succeeded", transaction_count=len(transaction_list))
    return transaction_list


def update_transaction(
    db: Session,
    transaction: FinancialRecord,
    transaction_data: FinancialRecordUpdate,
    updated_by: int,
) -> FinancialRecord:
    """Update a financial record with provided fields."""

    logger.info(
        "transaction_update_started",
        actor_user_id=updated_by,
        transaction_id=transaction.id,
    )
    updates = transaction_data.model_dump(exclude_unset=True)
    for field_name, field_value in updates.items():
        setattr(transaction, field_name, field_value)

    try:
        db.commit()
        db.refresh(transaction)
    except Exception as exc:
        db.rollback()
        logger.exception(
            "transaction_update_failed",
            actor_user_id=updated_by,
            transaction_id=transaction.id,
            error=str(exc),
        )
        raise FintechBackendException("Unable to update transaction", sys) from exc

    logger.info(
        "transaction_update_succeeded",
        actor_user_id=updated_by,
        transaction_id=transaction.id,
    )
    return transaction


def soft_delete_transaction(
    db: Session,
    transaction: FinancialRecord,
    deleted_by: int,
) -> FinancialRecord:
    """Soft delete a financial record."""

    logger.info(
        "transaction_delete_started",
        actor_user_id=deleted_by,
        transaction_id=transaction.id,
    )
    transaction.is_deleted = True

    try:
        db.commit()
        db.refresh(transaction)
    except Exception as exc:
        db.rollback()
        logger.exception(
            "transaction_delete_failed",
            actor_user_id=deleted_by,
            transaction_id=transaction.id,
            error=str(exc),
        )
        raise FintechBackendException("Unable to delete transaction", sys) from exc

    logger.info(
        "transaction_delete_succeeded",
        actor_user_id=deleted_by,
        transaction_id=transaction.id,
    )
    return transaction
