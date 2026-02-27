"""
BML Connect Python SDK
=====================

Python SDK for Bank of Maldives Connect API with synchronous and asynchronous support.

Features:
- Create, retrieve, cancel, and list transactions
- Verify webhook signatures
- Supports both production and sandbox environments
- Full sync/async compatibility with context manager support

Basic Usage:
    from bml_connect import BMLConnect, Environment

    # Sync client (context manager)
    with BMLConnect('your-api-key', 'your-app-id', Environment.SANDBOX) as client:
        transaction = client.transactions.create_transaction({...})

    # Async client (context manager)
    async with BMLConnect(
        'your-api-key', 'your-app-id', Environment.SANDBOX, async_mode=True
    ) as client:
        transaction = await client.transactions.create_transaction({...})

For detailed documentation and examples, visit:
https://github.com/quillfires/bml-connect-python
"""

__version__ = "1.2.1"
__author__ = "Ali Fayaz"
__email__ = "fayaz.quill@gmail.com"

from .client import (
    AuthenticationError,
    BMLConnect,
    BMLConnectError,
    Environment,
    NotFoundError,
    PaginatedResponse,
    QRCode,
    RateLimitError,
    ServerError,
    SignatureUtils,
    SignMethod,
    Transaction,
    TransactionState,
    ValidationError,
)

__all__ = [
    "BMLConnect",
    "Transaction",
    "QRCode",
    "PaginatedResponse",
    "Environment",
    "SignMethod",
    "TransactionState",
    "BMLConnectError",
    "AuthenticationError",
    "ValidationError",
    "NotFoundError",
    "ServerError",
    "RateLimitError",
    "SignatureUtils",
]

BMLConnect.__module__ = "bml_connect"
Transaction.__module__ = "bml_connect"
QRCode.__module__ = "bml_connect"
PaginatedResponse.__module__ = "bml_connect"
Environment.__module__ = "bml_connect"
SignMethod.__module__ = "bml_connect"
TransactionState.__module__ = "bml_connect"
BMLConnectError.__module__ = "bml_connect"
AuthenticationError.__module__ = "bml_connect"
ValidationError.__module__ = "bml_connect"
NotFoundError.__module__ = "bml_connect"
ServerError.__module__ = "bml_connect"
RateLimitError.__module__ = "bml_connect"
SignatureUtils.__module__ = "bml_connect"
