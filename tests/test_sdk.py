"""
Test suite for BML Connect SDK v2.
"""

import json

import pytest

from bml_connect import (
    BMLConnect,
    BMLConnectError,
    Environment,
    SignatureUtils,
    Webhook,
)
from bml_connect.models import (
    Category,
    Company,
    Customer,
    CustomerToken,
    CustomFee,
    OrderField,
    Product,
    Shop,
    Tax,
    Transaction,
    TransactionState,
)

# ---------------------------------------------------------------------------
# Environment / client initialisation
# ---------------------------------------------------------------------------


def test_invalid_environment_raises():
    with pytest.raises(ValueError, match="Invalid environment"):
        BMLConnect(api_key="key", environment="bad_env")


def test_sync_client_creation():
    with BMLConnect(api_key="test", environment=Environment.SANDBOX) as client:
        assert not client.async_mode


@pytest.mark.asyncio
async def test_async_client_creation():
    async with BMLConnect(
        api_key="test", environment=Environment.SANDBOX, async_mode=True
    ) as client:
        assert client.async_mode


def test_environment_urls():
    assert "uat" in Environment.SANDBOX.base_url
    assert "uat" not in Environment.PRODUCTION.base_url


# ---------------------------------------------------------------------------
# Current webhook verification - SHA-256 nonce + timestamp
# ---------------------------------------------------------------------------


def test_verify_webhook_signature_valid():
    import hashlib

    api_key = "my_api_key"
    nonce = "abc123"
    timestamp = "1700000000"
    sign_string = f"{nonce}{timestamp}{api_key}"
    expected_sig = hashlib.sha256(sign_string.encode()).hexdigest()

    assert SignatureUtils.verify_webhook_signature(
        nonce, timestamp, expected_sig, api_key
    )


def test_verify_webhook_signature_tampered():
    import hashlib

    api_key = "my_api_key"
    nonce = "abc123"
    timestamp = "1700000000"
    sign_string = f"{nonce}{timestamp}{api_key}"
    sig = hashlib.sha256(sign_string.encode()).hexdigest()

    # Tamper: change nonce
    assert not SignatureUtils.verify_webhook_signature(
        "different_nonce", timestamp, sig, api_key
    )


def test_verify_webhook_signature_wrong_key():
    import hashlib

    nonce = "abc123"
    timestamp = "1700000000"
    sig = hashlib.sha256(f"{nonce}{timestamp}correct_key".encode()).hexdigest()

    assert not SignatureUtils.verify_webhook_signature(
        nonce, timestamp, sig, "wrong_key"
    )


def test_verify_webhook_headers_valid():
    import hashlib

    api_key = "my_api_key"
    nonce = "nonce_xyz"
    timestamp = "1700000001"
    sig = hashlib.sha256(f"{nonce}{timestamp}{api_key}".encode()).hexdigest()

    headers = {
        "X-Signature-Nonce": nonce,
        "X-Signature-Timestamp": timestamp,
        "X-Signature": sig,
    }
    assert SignatureUtils.verify_webhook_headers(headers, api_key)


def test_verify_webhook_headers_missing_header():
    headers = {
        "X-Signature-Nonce": "nonce",
        # Missing X-Signature-Timestamp and X-Signature
    }
    assert not SignatureUtils.verify_webhook_headers(headers, "key")


# ---------------------------------------------------------------------------
# Client-level verify_webhook_signature / verify_webhook_headers
# ---------------------------------------------------------------------------


def test_client_verify_webhook_signature():
    import hashlib

    api_key = "my_api_key"
    nonce = "n1"
    timestamp = "t1"
    sig = hashlib.sha256(f"{nonce}{timestamp}{api_key}".encode()).hexdigest()

    client = BMLConnect(api_key=api_key, environment=Environment.SANDBOX)
    assert client.verify_webhook_signature(nonce, timestamp, sig)
    assert not client.verify_webhook_signature(nonce, "wrong_ts", sig)
    client.close()


def test_client_verify_webhook_headers():
    import hashlib

    api_key = "my_api_key"
    nonce = "n2"
    timestamp = "t2"
    sig = hashlib.sha256(f"{nonce}{timestamp}{api_key}".encode()).hexdigest()

    client = BMLConnect(api_key=api_key, environment=Environment.SANDBOX)
    assert client.verify_webhook_headers(
        {
            "X-Signature-Nonce": nonce,
            "X-Signature-Timestamp": timestamp,
            "X-Signature": sig,
        }
    )
    client.close()


# ---------------------------------------------------------------------------
# Deprecated legacy verification - originalSignature (MD5)
# ---------------------------------------------------------------------------


def test_verify_legacy_signature_valid():
    import base64
    import hashlib

    api_key = "key"
    amount = 1000
    currency = "MVR"
    sign_str = f"amount={amount}&currency={currency}&apiKey={api_key}"
    original_sig = base64.b64encode(hashlib.md5(sign_str.encode()).digest()).decode()

    assert SignatureUtils.verify_legacy_signature(
        {"amount": amount, "currency": currency}, original_sig, api_key
    )


def test_verify_legacy_signature_wrong_amount():
    import base64
    import hashlib

    api_key = "key"
    sign_str = "amount=1000&currency=MVR&apiKey=key"
    sig = base64.b64encode(hashlib.md5(sign_str.encode()).digest()).decode()

    # Different amount → should fail
    assert not SignatureUtils.verify_legacy_signature(
        {"amount": 9999, "currency": "MVR"}, sig, api_key
    )


def test_verify_legacy_signature_missing_fields():
    with pytest.raises(ValueError, match="amount and currency are required"):
        SignatureUtils.verify_legacy_signature({}, "sig", "key")


def test_client_verify_legacy_webhook_signature():
    import base64
    import hashlib

    api_key = "key"
    amount = 500
    currency = "MVR"
    sign_str = f"amount={amount}&currency={currency}&apiKey={api_key}"
    orig_sig = base64.b64encode(hashlib.md5(sign_str.encode()).digest()).decode()

    client = BMLConnect(api_key=api_key, environment=Environment.SANDBOX)
    payload = {"amount": amount, "currency": currency, "originalSignature": orig_sig}
    assert client.verify_legacy_webhook_signature(payload, orig_sig)
    client.close()


def test_generate_legacy_signature_raises():
    """generate_legacy_signature was removed in v2 - must raise NotImplementedError."""
    with pytest.raises(NotImplementedError):
        SignatureUtils.generate_legacy_signature(
            {"amount": 100, "currency": "MVR"}, "key"
        )


# ---------------------------------------------------------------------------
# Model: Transaction.from_dict
# ---------------------------------------------------------------------------


def test_transaction_from_dict_v2():
    data = {
        "id": "txn_abc",
        "amount": 1500,
        "currency": "MVR",
        "state": "CONFIRMED",
        "url": "https://pay.example.com/txn_abc",
        "shortUrl": "https://bml.mv/abc",
        "qr": {"url": "https://qr.example.com/abc"},
        "isPaymentLink": True,
    }
    txn = Transaction.from_dict(data)
    assert txn.id == "txn_abc"
    assert txn.transaction_id == "txn_abc"
    assert txn.state == TransactionState.CONFIRMED
    assert txn.qr_code is not None
    assert txn.qr_code.url == "https://qr.example.com/abc"
    assert txn.short_url == "https://bml.mv/abc"
    assert txn.is_payment_link is True


def test_transaction_unknown_state_does_not_raise():
    txn = Transaction.from_dict({"id": "t1", "state": "UNKNOWN_STATE"})
    assert txn.state is None


# ---------------------------------------------------------------------------
# Model: Webhook.from_dict
# ---------------------------------------------------------------------------


def test_webhook_from_dict():
    data = {
        "id": "wh_1",
        "hookUrl": "https://myapp.com/hook",
        "companyId": "co_1",
        "created": "2024-01-01T00:00:00Z",
    }
    wh = Webhook.from_dict(data)
    assert wh.id == "wh_1"
    assert wh.hook_url == "https://myapp.com/hook"


# ---------------------------------------------------------------------------
# Model: Company.from_dict
# ---------------------------------------------------------------------------


def test_company_from_dict():
    data = {
        "id": "co_1",
        "tradingName": "Acme Ltd",
        "enabledCurrencies": ["MVR", "USD"],
        "paymentProviders": [
            {"value": "card", "description": "Cards", "ecommerce": True, "mobile": True}
        ],
    }
    co = Company.from_dict(data)
    assert co.trading_name == "Acme Ltd"
    assert "MVR" in co.enabled_currencies
    assert co.payment_providers[0].value == "card"


# ---------------------------------------------------------------------------
# Model: Shop.from_dict
# ---------------------------------------------------------------------------


def test_shop_from_dict():
    data = {
        "id": "sh_1",
        "name": "My Store",
        "status": "OPEN",
        "qr": {"url": "https://checkout.example.com/sh_1"},
    }
    shop = Shop.from_dict(data)
    assert shop.name == "My Store"
    assert shop.qr_url == "https://checkout.example.com/sh_1"


# ---------------------------------------------------------------------------
# Model: Customer / CustomerToken
# ---------------------------------------------------------------------------


def test_customer_from_dict():
    data = {
        "id": "cu_1",
        "name": "Alice",
        "email": "alice@example.com",
        "currency": "MVR",
        "companyId": "co_1",
    }
    cu = Customer.from_dict(data)
    assert cu.name == "Alice"


def test_customer_token_from_dict():
    data = {
        "id": "tok_1",
        "brand": "VISA",
        "provider": "mpgs",
        "token": "encrypted_token",
        "tokenType": "CARD",
    }
    tok = CustomerToken.from_dict(data)
    assert tok.brand == "VISA"
    assert tok.token_type == "CARD"


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


def test_sync_context_manager():
    with BMLConnect(api_key="k", environment=Environment.SANDBOX) as client:
        assert client is not None


@pytest.mark.asyncio
async def test_async_context_manager():
    async with BMLConnect(
        api_key="k", environment=Environment.SANDBOX, async_mode=True
    ) as client:
        assert client is not None
