"""Transaction routes."""

import sys
from typing import Annotated

from fastapi import APIRouter, Depends, status
import structlog
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_roles
from app.exceptions import BadRequestException, ResourceNotFoundException
from app.models.transaction import FinancialRecord
from app.models.user import User, UserRole
from app.schemas.transaction import (
    FinancialRecordCreate,
    FinancialRecordFilters,
    FinancialRecordListOptions,
    FinancialRecordListOut,
    FinancialRecordOut,
    FinancialRecordUpdate,
    get_financial_record_filters,
    get_financial_record_list_options,
)
from app.services.transaction_service import (
    create_transaction,
    get_transaction_by_id,
    list_transactions as list_transactions_service,
    soft_delete_transaction,
    update_transaction as update_transaction_service,
)


router = APIRouter(prefix="/transactions", tags=["transactions"])
logger = structlog.get_logger(__name__)


@router.post("/", response_model=FinancialRecordOut, status_code=status.HTTP_201_CREATED)
async def create_transaction_record(
    transaction_data: FinancialRecordCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> FinancialRecord:
    """Create a financial transaction."""

    logger.info(
        "transaction_create_requested",
        actor_user_id=current_user.id,
        record_type=transaction_data.record_type.value,
        category=transaction_data.category,
    )
    return create_transaction(db, transaction_data, current_user.id)


@router.get("/", response_model=FinancialRecordListOut)
async def list_transactions(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER)),
    ],
    filters: Annotated[FinancialRecordFilters, Depends(get_financial_record_filters)],
    list_options: Annotated[
        FinancialRecordListOptions,
        Depends(get_financial_record_list_options),
    ],
) -> FinancialRecordListOut:
    """List financial transactions with simple filters."""

    logger.info(
        "transactions_list_route_requested",
        actor_user_id=current_user.id,
        role=current_user.role.value,
    )
    if (
        filters.date_from is not None
        and filters.date_to is not None
        and filters.date_from > filters.date_to
    ):
        logger.warning(
            "transactions_list_invalid_date_range",
            actor_user_id=current_user.id,
        )
        raise BadRequestException("date_from cannot be greater than date_to", sys)

    items, total = list_transactions_service(
        db=db,
        filters=filters,
        list_options=list_options,
    )
    logger.info(
        "transactions_list_route_completed",
        actor_user_id=current_user.id,
        returned_count=len(items),
        total=total,
        page=list_options.page,
        limit=list_options.limit,
    )
    return FinancialRecordListOut(
        items=items,
        total=total,
        page=list_options.page,
        limit=list_options.limit,
    )


@router.get("/{transaction_id}", response_model=FinancialRecordOut)
async def get_transaction(
    transaction_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER)),
    ],
) -> FinancialRecord:
    """Return a single financial transaction."""

    logger.info(
        "transaction_get_route_requested",
        actor_user_id=current_user.id,
        role=current_user.role.value,
        transaction_id=transaction_id,
    )
    transaction = get_transaction_by_id(db, transaction_id)
    if transaction is None:
        logger.warning(
            "transaction_get_not_found",
            actor_user_id=current_user.id,
            transaction_id=transaction_id,
        )
        raise ResourceNotFoundException("Transaction not found", sys)

    logger.info(
        "transaction_get_route_succeeded",
        actor_user_id=current_user.id,
        transaction_id=transaction.id,
    )
    return transaction


@router.patch("/{transaction_id}", response_model=FinancialRecordOut)
async def update_transaction(
    transaction_id: int,
    transaction_data: FinancialRecordUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> FinancialRecord:
    """Update a financial transaction."""

    logger.info(
        "transaction_update_requested",
        actor_user_id=current_user.id,
        transaction_id=transaction_id,
    )
    transaction = get_transaction_by_id(db, transaction_id)
    if transaction is None:
        logger.warning(
            "transaction_update_not_found",
            actor_user_id=current_user.id,
            transaction_id=transaction_id,
        )
        raise ResourceNotFoundException("Transaction not found", sys)

    updated_transaction = update_transaction_service(
        db,
        transaction,
        transaction_data,
        current_user.id,
    )
    logger.info(
        "transaction_update_completed",
        actor_user_id=current_user.id,
        transaction_id=updated_transaction.id,
    )
    return updated_transaction


@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> dict[str, str]:
    """Soft delete a financial transaction."""

    logger.info(
        "transaction_delete_requested",
        actor_user_id=current_user.id,
        transaction_id=transaction_id,
    )
    transaction = get_transaction_by_id(db, transaction_id)
    if transaction is None:
        logger.warning(
            "transaction_delete_not_found",
            actor_user_id=current_user.id,
            transaction_id=transaction_id,
        )
        raise ResourceNotFoundException("Transaction not found", sys)

    soft_delete_transaction(db, transaction, current_user.id)
    logger.info(
        "transaction_delete_completed",
        actor_user_id=current_user.id,
        transaction_id=transaction_id,
    )
    return {"message": "Transaction deleted successfully"}
