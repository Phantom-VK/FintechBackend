"""Thin service functions for transaction features."""

import sys

from sqlalchemy import or_, select
from sqlalchemy.orm import Session
import structlog

from app.core.exceptions import FintechBackendException
from app.models.transaction import FinancialRecord
from app.schemas.transaction import (
    FinancialRecordCreate,
    FinancialRecordFilters,
    FinancialRecordListOptions,
    FinancialRecordUpdate,
    SortOrder,
    TransactionSortField,
)


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


def create_transactions_bulk(
    db: Session,
    transactions_data: list[FinancialRecordCreate],
    created_by: int,
) -> list[FinancialRecord]:
    """Create multiple financial records in a single request."""

    logger.info(
        "transactions_bulk_create_started",
        actor_user_id=created_by,
        record_count=len(transactions_data),
    )
    transactions = [
        FinancialRecord(
            amount=transaction_data.amount,
            record_type=transaction_data.record_type,
            category=transaction_data.category,
            record_date=transaction_data.record_date,
            description=transaction_data.description,
            created_by=created_by,
        )
        for transaction_data in transactions_data
    ]

    try:
        db.add_all(transactions)
        db.commit()
        for transaction in transactions:
            db.refresh(transaction)
    except Exception as exc:
        db.rollback()
        logger.exception(
            "transactions_bulk_create_failed",
            actor_user_id=created_by,
            error=str(exc),
        )
        raise FintechBackendException("Unable to create transactions in bulk", sys) from exc

    logger.info(
        "transactions_bulk_create_succeeded",
        actor_user_id=created_by,
        record_count=len(transactions),
    )
    return transactions


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
    filters: FinancialRecordFilters,
    list_options: FinancialRecordListOptions,
) -> tuple[list[FinancialRecord], int]:
    """Return non-deleted financial records with filters, pagination, and sorting."""

    logger.info(
        "transactions_list_requested",
        record_type=filters.record_type.value if filters.record_type else None,
        category=filters.category,
        search=filters.search,
        date_from=filters.date_from.isoformat() if filters.date_from else None,
        date_to=filters.date_to.isoformat() if filters.date_to else None,
        page=list_options.page,
        limit=list_options.limit,
        sort_by=list_options.sort_by.value,
        sort_order=list_options.sort_order.value,
    )
    query = select(FinancialRecord).where(FinancialRecord.is_deleted.is_(False))
    count_query = select(FinancialRecord.id).where(FinancialRecord.is_deleted.is_(False))

    if filters.record_type is not None:
        query = query.where(FinancialRecord.record_type == filters.record_type)
        count_query = count_query.where(FinancialRecord.record_type == filters.record_type)

    if filters.category:
        query = query.where(FinancialRecord.category == filters.category)
        count_query = count_query.where(FinancialRecord.category == filters.category)

    if filters.search:
        search_pattern = f"%{filters.search}%"
        search_clause = or_(
            FinancialRecord.category.ilike(search_pattern),
            FinancialRecord.description.ilike(search_pattern),
        )
        query = query.where(search_clause)
        count_query = count_query.where(search_clause)

    if filters.date_from is not None:
        query = query.where(FinancialRecord.record_date >= filters.date_from)
        count_query = count_query.where(FinancialRecord.record_date >= filters.date_from)

    if filters.date_to is not None:
        query = query.where(FinancialRecord.record_date <= filters.date_to)
        count_query = count_query.where(FinancialRecord.record_date <= filters.date_to)

    total = len(db.scalars(count_query).all())

    sort_column = FinancialRecord.record_date
    if list_options.sort_by == TransactionSortField.AMOUNT:
        sort_column = FinancialRecord.amount
    elif list_options.sort_by == TransactionSortField.CREATED_AT:
        sort_column = FinancialRecord.created_at

    if list_options.sort_order == SortOrder.ASC:
        query = query.order_by(sort_column.asc(), FinancialRecord.id.asc())
    else:
        query = query.order_by(sort_column.desc(), FinancialRecord.id.desc())

    offset = (list_options.page - 1) * list_options.limit
    transactions = db.scalars(
        query.offset(offset).limit(list_options.limit)
    ).all()
    transaction_list = list(transactions)
    logger.info(
        "transactions_list_succeeded",
        transaction_count=len(transaction_list),
        total=total,
    )
    return transaction_list, total


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
