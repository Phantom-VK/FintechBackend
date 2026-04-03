"""Custom application exceptions."""

import logging
import sys


logger = logging.getLogger(__name__)


class FintechBackendException(Exception):
    """Base exception for application-specific errors."""

    def __init__(
        self,
        error_message: str,
        error_details: sys,
        status_code: int = 500,
    ) -> None:
        super().__init__(error_message)
        self.error_message = error_message
        self.status_code = status_code
        self.exc_info = error_details.exc_info()
        _, _, exc_tb = self.exc_info

        if exc_tb is None:
            self.lineno = 0
            self.filename = "unknown"
        else:
            self.lineno = exc_tb.tb_lineno
            self.filename = exc_tb.tb_frame.f_code.co_filename

    def __str__(self) -> str:
        custom_error_message = (
            f"Error occurred in python script name [{self.filename}] "
            f"line number [{self.lineno}] error message [{self.error_message}]"
        )
        logger.error(custom_error_message)
        return custom_error_message


class BadRequestException(FintechBackendException):
    """Exception for invalid client requests."""

    def __init__(self, error_message: str, error_details: sys) -> None:
        super().__init__(error_message, error_details, status_code=400)


class AuthenticationException(FintechBackendException):
    """Exception for authentication failures."""

    def __init__(self, error_message: str, error_details: sys) -> None:
        super().__init__(error_message, error_details, status_code=401)


class AuthorizationException(FintechBackendException):
    """Exception for permission-related failures."""

    def __init__(self, error_message: str, error_details: sys) -> None:
        super().__init__(error_message, error_details, status_code=403)


class ResourceNotFoundException(FintechBackendException):
    """Exception for missing resources."""

    def __init__(self, error_message: str, error_details: sys) -> None:
        super().__init__(error_message, error_details, status_code=404)


class ConflictException(FintechBackendException):
    """Exception for duplicate or conflicting resources."""

    def __init__(self, error_message: str, error_details: sys) -> None:
        super().__init__(error_message, error_details, status_code=409)
