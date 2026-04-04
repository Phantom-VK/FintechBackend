"""HTTP middleware for request-scoped structured logging."""

import time
import uuid

import structlog
from fastapi import Request


logger = structlog.get_logger(__name__)


async def logging_middleware(request: Request, call_next):
    """Bind request context, log request lifecycle, and return a request id."""

    start = time.perf_counter()
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )

    logger.info("request_started")

    try:
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "request_completed",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as exc:  # pylint: disable=broad-exception-caught
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.exception(
            "request_failed",
            error_type=type(exc).__name__,
            duration_ms=duration_ms,
        )
        raise
    finally:
        structlog.contextvars.clear_contextvars()
