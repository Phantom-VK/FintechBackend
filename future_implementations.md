# Future Implementations

## Transaction Enhancements

- Restore soft-deleted transactions with an admin-only endpoint.
- Add idempotency-key support for transaction creation to avoid duplicate writes.
- Add transaction status if the product later needs a pending/posted/reversed workflow.
- Add richer audit metadata such as `updated_by`, `deleted_by`, and `deleted_at`.
- Add search support for description and category.

## Live Updates

- Add an SSE endpoint for real-time transaction and dashboard updates.

## Notes

- Pagination and sorting are being implemented in the current `vikram/feature/financial-records-crud` branch.
- These items are optional improvements, not current assignment blockers.
