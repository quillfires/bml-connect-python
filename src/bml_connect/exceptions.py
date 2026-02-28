"""
BML Connect SDK - Exceptions
"""

from typing import Optional


class BMLConnectError(Exception):
    """Base exception for BML Connect SDK errors."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class AuthenticationError(BMLConnectError):
    """Raised when the API key is missing or invalid (HTTP 401)."""


class ValidationError(BMLConnectError):
    """Raised when the request payload is invalid (HTTP 400)."""


class NotFoundError(BMLConnectError):
    """Raised when a resource is not found (HTTP 404)."""


class ServerError(BMLConnectError):
    """Raised when the server returns a 5xx error."""


class RateLimitError(BMLConnectError):
    """Raised when rate limit is exceeded (HTTP 429)."""


__all__ = [
    "BMLConnectError",
    "AuthenticationError",
    "ValidationError",
    "NotFoundError",
    "ServerError",
    "RateLimitError",
]
