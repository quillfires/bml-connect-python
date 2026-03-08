"""
BML Connect Python SDK
======================

Python SDK for Bank of Maldives Connect API v2 with sync and async support.

Four Integration Methods
------------------------

- **Redirect Method** - redirect customer to BML's hosted payment page
- **Direct Method** - QR providers (``vendor_qr_code``) or card providers (``url``)
- **Card-On-File / Tokenization** - recurring charges against stored tokens
- **PCI Merchant Tokenization** - encrypt card details server-side with RSA

Basic Usage::

    from bml_connect import BMLConnect, Environment

    # Sync
    with BMLConnect("sk_your_private_key", Environment.SANDBOX) as client:
        # Register webhook
        client.webhooks.create("https://yourapp.com/bml-hook")

        # Redirect Method
        txn = client.transactions.create({
            "redirectUrl": "https://yourapp.com/thanks",
            "localId": "INV-001",
            "order": {
                "shopId": "YOUR_SHOP_ID",
                "products": [{"productId": "PROD_ID", "numberOfItems": 1}],
            },
        })
        print(txn.url)          # full URL
        print(txn.short_url)    # short URL for SMS/messaging

        # Direct Method - QR provider
        txn = client.transactions.create({
            "amount": 1000, "currency": "USD",
            "provider": "alipay",
            "webhook": "https://yourapp.com/bml-hook",
        })
        qr_data = txn.vendor_qr_code  # encode into QR image

        # Card-On-File - charge stored token
        tokens = client.customers.list_tokens("CUSTOMER_ID")
        new_txn = client.transactions.create({"amount": 200, "currency": "USD",
                                               "customerId": "CUSTOMER_ID"})
        client.customers.charge({"customerId": "CUSTOMER_ID",
                                  "transactionId": new_txn.id,
                                  "tokenId": tokens[0].id})

    # PCI Merchant Tokenization
    with BMLConnect("sk_...", public_key="pk_...",
                    environment=Environment.SANDBOX) as client:
        enc_key = client.public_client.get_tokens_public_key()
        card_b64 = CardEncryption.encrypt(enc_key.pem, {
            "cardNumberRaw": "4111111111111111", "cardVDRaw": "123",
            "cardExpiryMonth": 12, "cardExpiryYear": 29,
        })
        result = client.public_client.add_card(
            card_data=card_b64, key_id=enc_key.key_id,
            customer_id="CUSTOMER_ID",
            redirect="https://yourapp.com/tokenisation-callback",
        )
        # redirect user to result.next_action.url for 3DS

    # Async
    async def run():
        async with BMLConnect("sk_...", Environment.SANDBOX, async_mode=True) as client:
            txn = await client.transactions.create({...})

For documentation and examples visit:
https://github.com/quillfires/bml-connect-python
"""

__version__ = "2.0.0"
__author__ = "Ali Fayaz"
__email__ = "fayaz.quill@gmail.com"

from .client import BMLConnect
from .crypto import CardEncryption
from .exceptions import (
    AuthenticationError,
    BMLConnectError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from .models import (
    Category,
    ClientTokenNextAction,
    ClientTokenResponse,
    Company,
    Customer,
    CustomerToken,
    CustomFee,
    Environment,
    OrderField,
    PaginatedResponse,
    PaymentProvider,
    Product,
    Provider,
    QRCode,
    Shop,
    SignMethod,
    Tax,
    TokenisationStatus,
    TokensPublicKey,
    Transaction,
    TransactionState,
    Webhook,
    WebhookEvent,
    WebhookEventType,
)
from .signature import SignatureUtils

__all__ = [
    # Main client
    "BMLConnect",
    # Models
    "Transaction",
    "QRCode",
    "PaginatedResponse",
    "Webhook",
    "WebhookEvent",
    "Company",
    "PaymentProvider",
    "Shop",
    "Product",
    "Category",
    "Tax",
    "OrderField",
    "CustomFee",
    "Customer",
    "CustomerToken",
    # PCI Tokenization models
    "TokensPublicKey",
    "ClientTokenNextAction",
    "ClientTokenResponse",
    # Enums
    "Environment",
    "SignMethod",
    "TransactionState",
    "Provider",
    "WebhookEventType",
    "TokenisationStatus",
    # Exceptions
    "BMLConnectError",
    "AuthenticationError",
    "ValidationError",
    "NotFoundError",
    "ServerError",
    "RateLimitError",
    # Utilities
    "SignatureUtils",
    "CardEncryption",
]

# Make everything importable from the top-level package namespace
for _name in __all__:
    _obj = globals()[_name]
    if hasattr(_obj, "__module__"):
        _obj.__module__ = "bml_connect"
