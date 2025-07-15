"""
BML Connect Python SDK
=====================

Python SDK for Bank of Maldives Connect API with synchronous and asynchronous support.

Features:
- Create, retrieve, and list transactions
- Verify webhook signatures
- Supports both production and sandbox environments
- Full sync/async compatibility

Basic Usage:
    from bml_connect import BMLConnect, Environment

    # Sync client
    client = BMLConnect('your-api-key', 'your-app-id', Environment.SANDBOX)
    transaction = client.transactions.create_transaction({...})

    # Async client
    async_client = BMLConnect('your-api-key', 'your-app-id', Environment.SANDBOX, async_mode=True)
    transaction = await async_client.transactions.create_transaction({...})

For detailed documentation and examples, visit:
https://github.com/quillfires/bml-connect-python
"""

__version__ = "1.1.0"
__author__ = "Ali Fayaz"
__email__ = "fayaz.quill@gmail.com"

from .client import (
    BMLConnect,
    Transaction,
    QRCode,
    PaginatedResponse,
    Environment,
    SignMethod,
    TransactionState,
    BMLConnectError,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    ServerError,
    RateLimitError,
    SignatureUtils
)

__all__ = [
    'BMLConnect',
    'Transaction',
    'QRCode',
    'PaginatedResponse',
    'Environment',
    'SignMethod',
    'TransactionState',
    'BMLConnectError',
    'AuthenticationError',
    'ValidationError',
    'NotFoundError',
    'ServerError',
    'RateLimitError',
    'SignatureUtils'
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