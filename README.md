# BML Connect Python SDK

[![PyPI version](https://badge.fury.io/py/bml-connect-python.svg)](https://badge.fury.io/py/bml-connect-python)
[![Python Support](https://img.shields.io/pypi/pyversions/bml-connect-python.svg)](https://pypi.org/project/bml-connect-python/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[![ViewCount](https://views.whatilearened.today/views/github/quillfires/bml-connect-python.svg)](https://views.whatilearened.today/views/github/quillfires/bml-connect-python.svg) [![GitHub forks](https://img.shields.io/github/forks/quillfires/bml-connect-python)](https://github.com/quillfires/bml-connect-python/network) [![GitHub stars](https://img.shields.io/github/stars/quillfires/bml-connect-python.svg?color=ffd40c)](https://github.com/quillfires/bml-connect-python/stargazers) [![PyPI - Downloads](https://img.shields.io/pypi/dm/bml-connect-python?color=orange&label=PIP%20-%20Installs)](https://pypi.python.org/pypi/bml-connect-python/) [![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/quillfires/bml-connect-python/issues) [![GitHub issues](https://img.shields.io/github/issues/bml-connect-python.svg?color=808080)](https://github.com/quillfires/bml-connect-python/issues)

Python SDK for Bank of Maldives Connect API v2 with synchronous and asynchronous support.  
Compatible with all Python frameworks including Django, Flask, FastAPI, and Sanic.

> **v2.0.0** brings full coverage of the BML Connect v2 API: shop & product management,
> customer & token management, webhook registration, SMS/email payment link sharing,
> and updated transaction creation that **no longer requires a request signature**.

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Webhooks](#webhooks)
- [Transactions](#transactions)
- [Sharing Payment Links](#sharing-payment-links)
- [Shops & Products](#shops--products)
- [Customers & Tokens](#customers--tokens)
- [Company Info](#company-info)
- [Framework Integration](#framework-integration)
- [API Reference](#api-reference)
- [Migration from v1.x](#migration-from-v1x)
- [Development](#development)
- [Contributing](#contributing)
- [Security](#security)

---

## Features

- **🔄 Sync/Async Support** - Choose your style; every resource has both a sync and an `async/await` variant
- **🎯 Full API Coverage** - Transactions (v2), webhooks registration, SMS/email sharing, shops, products, categories, taxes, order fields, custom fees, customers, tokens
- **🪝 Webhook Registration** - Register your endpoint URL directly in BML's backend so you receive push notifications
- **📝 Type Annotations** - Full type hints throughout for a great IDE experience
- **🛡️ Error Handling** - Structured exception hierarchy for easy debugging
- **🔐 Dual Webhook Verification** - HMAC-SHA256 (current) and legacy SHA-1/MD5 (backward compat)
- **🚀 Framework Agnostic** - Works with Django, Flask, FastAPI, Sanic, or plain scripts
- **📄 MIT Licensed** - Open source and free to use

---

## Installation

```bash
pip install bml-connect-python
```

**Requires Python 3.9+**

---

## Quick Start

### Synchronous

```python
from bml_connect import BMLConnect, Environment

with BMLConnect(api_key="your_api_key", environment=Environment.SANDBOX) as client:

    # 1. Register your webhook URL so BML notifies you of payment updates
    client.webhooks.create("https://yourapp.com/bml-webhook")

    # 2. Create a transaction (V2 - no signature needed)
    txn = client.transactions.create({
        "redirectUrl": "https://yourapp.com/thanks",
        "localId": "INV-001",
        "customerReference": "Order #42",
        "order": {
            "shopId": "YOUR_SHOP_ID",
            "products": [
                {"productId": "YOUR_PRODUCT_ID", "numberOfItems": 2}
            ],
        },
    })

    print(f"Payment URL : {txn.url}")
    print(f"Short URL   : {txn.short_url}")

    # 3. Send the payment link to the customer
    client.transactions.send_sms(txn.id, "9609601234")
    client.transactions.send_email(txn.id, "customer@example.com")
```

### Asynchronous

```python
import asyncio
from bml_connect import BMLConnect, Environment

async def main():
    async with BMLConnect(api_key="your_api_key", environment=Environment.SANDBOX, async_mode=True) as client:

        await client.webhooks.create("https://yourapp.com/bml-webhook")

        txn = await client.transactions.create({
            "redirectUrl": "https://yourapp.com/thanks",
            "localId": "INV-ASYNC-001",
            "order": {
                "shopId": "YOUR_SHOP_ID",
                "products": [{"productId": "PROD_ID", "numberOfItems": 1}],
            },
        })

        print(f"Transaction: {txn.id} → {txn.url}")
        await client.transactions.send_sms(txn.id, "9609601234")

asyncio.run(main())
```

---

## Webhooks

BML supports push notifications: you register a public URL and BML `POST`s a transaction
update payload to it whenever a payment state changes.

### Register / Unregister

```python
# Register
hook = client.webhooks.create("https://yourapp.com/bml-webhook")
print(hook.id, hook.hook_url)

# Unregister (pass the exact URL you registered)
client.webhooks.delete("https://yourapp.com/bml-webhook")
```

### Receiving & Verifying Webhook Notifications

BML signs every outgoing webhook with three HTTP headers:

| Header                  | Description                                              |
| ----------------------- | -------------------------------------------------------- |
| `X-Signature-Nonce`     | Unique identifier for the request                        |
| `X-Signature-Timestamp` | Unix timestamp of the request                            |
| `X-Signature`           | `SHA-256("{nonce}{timestamp}{api_key}")` as a hex string |

Reconstruct the same string, hash it, and compare - the SDK does this for you:

```python
# From any headers dict (Flask, Django, Sanic, plain dicts…)
if not client.verify_webhook_headers(request.headers):
    abort(403)

# Or pass the three values individually
nonce     = request.headers["X-Signature-Nonce"]
timestamp = request.headers["X-Signature-Timestamp"]
signature = request.headers["X-Signature"]

if not client.verify_webhook_signature(nonce, timestamp, signature):
    abort(403)
```

You can also call the utility directly without a client instance:

```python
from bml_connect import SignatureUtils

is_valid = SignatureUtils.verify_webhook_signature(nonce, timestamp, signature, api_key)
is_valid = SignatureUtils.verify_webhook_headers(request.headers, api_key)
```

**Legacy `originalSignature` (deprecated)**

Older v1 webhook payloads included an `originalSignature` field in the JSON body
instead of headers. BML no longer recommends relying on this alone - always
query the API for the authoritative transaction state. The SDK still supports it
for backward compatibility:

```python
payload      = request.get_json()
original_sig = payload.get("originalSignature")

if not client.verify_legacy_webhook_signature(payload, original_sig):
    abort(403)

# Then confirm with the API
txn = client.transactions.get(payload["id"])
```

---

## Transactions

### Create (V2 - recommended)

The V2 endpoint (`POST /public/v2/transactions`) supports two modes.

**Order-based** - reference products from a shop:

```python
txn = client.transactions.create({
    "redirectUrl": "https://yourapp.com/thanks",
    "webhook": "https://yourapp.com/bml-webhook",   # per-transaction webhook override
    "localId": "INV-001",
    "customerReference": "Order #42",               # shown on customer receipt
    "order": {
        "shopId": "SHOP_ID",
        "products": [
            {"productId": "PROD_ID", "numberOfItems": 2},
            {"sku": "SKU-XYZ", "numberOfItems": 1},  # or reference by SKU
        ],
        "orderFields": [                             # if your shop requires them
            {"id": "FIELD_ID", "value": "Table 5"}
        ],
    },
    # Optional: attach to an existing customer
    "customerId": "CUSTOMER_ID",
    # Optional: expire the payment link
    "expires": "2026-12-31T23:59:59.000Z",
})
```

**With customer creation** - create a customer record inline:

```python
txn = client.transactions.create({
    "redirectUrl": "https://yourapp.com/thanks",
    "order": {"shopId": "SHOP_ID", "products": [...]},
    "customer": {
        "name": "Alice Smith",
        "email": "alice@example.com",
        "billingEmail": "alice@example.com",
        "billingAddress1": "123 Coral Way",
        "billingCity": "Malé",
        "billingCountry": "MV",
        "billingPostCode": "20026",
        "currency": "MVR",
    },
})
```

**With tokenisation** - for recurring or unscheduled payments:

```python
txn = client.transactions.create({
    "order": {"shopId": "SHOP_ID", "products": [...]},
    "tokenizationDetails": {
        "tokenize": True,
        "paymentType": "RECURRING",          # or "UNSCHEDULED"
        "recurringFrequency": "MONTHLY",
        "expiryDate": "2027-01-01",
    },
})
```

### Retrieve

```python
txn = client.transactions.get("TRANSACTION_ID")
print(txn.state, txn.amount, txn.currency)

# Backward-compat alias also works:
txn = client.transactions.get_transaction("TRANSACTION_ID")
```

### Update

Update mutable metadata on a transaction after creation:

```python
txn = client.transactions.update(
    "TRANSACTION_ID",
    customer_reference="Booking Ref #99",    # up to 140 chars, shown on receipt
    local_data='{"reservationId": "R-001"}', # up to 1000 chars, merchant-side only
    pnr="ABC123",                            # up to 64 chars, booking/PNR reference
)
```

### List (legacy)

```python
page = client.transactions.list(page=1, per_page=20, state="CONFIRMED")
for txn in page.items:
    print(txn.id, txn.amount, txn.state)
```

---

## Sharing Payment Links

Both methods are **rate-limited to once per minute** per transaction to prevent spam.

```python
# SMS - phone number with country code, + prefix is optional
client.transactions.send_sms("TRANSACTION_ID", "9609601234")

# Email - single address or a list
client.transactions.send_email("TRANSACTION_ID", "customer@example.com")
client.transactions.send_email("TRANSACTION_ID", ["alice@example.com", "bob@example.com"])
```

---

## Shops & Products

### Shops

```python
shops = client.shops.list()
shop  = client.shops.get("SHOP_ID")
shop  = client.shops.create({"name": "My Café", "reference": "cafe-main"})
shop  = client.shops.update("SHOP_ID", {"name": "My Café & Bar"})
```

### Products

```python
products = client.shops.list_products("SHOP_ID")
product  = client.shops.create_product("SHOP_ID", {
    "name": "Flat White",
    "price": 2500,      # in cents
    "currency": "MVR",
    "sku": "FW-001",
})
product  = client.shops.get_product("SHOP_ID", "PRODUCT_ID")
product  = client.shops.update_product("SHOP_ID", "PRODUCT_ID", {"price": 3000})
product  = client.shops.update_product_by_sku("SHOP_ID", {"sku": "FW-001", "price": 3000})

# Bulk create
products = client.shops.create_products_batch("SHOP_ID", [
    {"name": "Espresso", "price": 1500, "currency": "MVR"},
    {"name": "Latte",    "price": 2000, "currency": "MVR"},
])

# Upload product image
with open("espresso.jpg", "rb") as f:
    client.shops.upload_product_image("SHOP_ID", "PRODUCT_ID", f.read(), "espresso.jpg")

client.shops.delete_product("SHOP_ID", "PRODUCT_ID")
```

### Categories

```python
cats = client.shops.list_categories("SHOP_ID")
cat  = client.shops.create_category("SHOP_ID", {"name": "Hot Drinks"})
cat  = client.shops.update_category("SHOP_ID", "CAT_ID", {"name": "Hot Beverages"})
client.shops.delete_category("SHOP_ID", "CAT_ID")
```

### Taxes

```python
taxes = client.shops.list_taxes("SHOP_ID")
tax   = client.shops.create_tax("SHOP_ID", {
    "name": "Tourist Tax", "code": "TT", "percentage": 10.0, "applyOn": "PRODUCT"
})
client.shops.delete_tax("SHOP_ID", "TAX_ID")

# Bulk apply taxes to all products in a shop
client.shops.update_products_taxes("SHOP_ID", {"taxIds": ["TAX_ID_1", "TAX_ID_2"]})
```

### Order Fields

```python
fields = client.shops.list_order_fields("SHOP_ID")
field  = client.shops.create_order_field("SHOP_ID", {"label": "Table Number", "type": "text"})
field  = client.shops.update_order_field("SHOP_ID", "FIELD_ID", {"checked": True})
client.shops.delete_order_field("SHOP_ID", "FIELD_ID")
```

### Custom Fees

```python
fees = client.shops.list_custom_fees("SHOP_ID")
fee  = client.shops.create_custom_fee("SHOP_ID", {
    "name": "Nature Donation", "description": "Optional donation", "fee": 100
})
fee  = client.shops.update_custom_fee("SHOP_ID", "FEE_ID", {"fee": 200})
client.shops.delete_custom_fee("SHOP_ID", "FEE_ID")
```

---

## Customers & Tokens

### Customers

```python
customers = client.customers.list()
customer  = client.customers.create({
    "name": "Alice Smith",
    "email": "alice@example.com",
    "companyId": "YOUR_COMPANY_ID",
    "currency": "MVR",
})
customer  = client.customers.get("CUSTOMER_ID")
customer  = client.customers.update("CUSTOMER_ID", {"name": "Alice J. Smith"})
client.customers.delete("CUSTOMER_ID")  # archives, does not hard-delete
```

### Tokens

```python
tokens = client.customers.list_tokens("CUSTOMER_ID")
token  = client.customers.get_token("CUSTOMER_ID", "TOKEN_ID")
client.customers.delete_token("CUSTOMER_ID", "TOKEN_ID")
```

### Charge a Stored Token

```python
txn = client.customers.charge({
    "customerId": "CUSTOMER_ID",
    "tokenId": "TOKEN_ID",
    "amount": 5000,
    "currency": "MVR",
})
print(txn.state)
```

---

## Company Info

```python
companies = client.company.get()   # returns a list
for co in companies:
    print(co.trading_name, co.enabled_currencies)
    for provider in co.payment_providers:
        print(f"  {provider.value} - ecommerce={provider.ecommerce}")
```

---

## Framework Integration

### Flask - full webhook receiver

```python
import os
from flask import Flask, jsonify, request
from bml_connect import BMLConnect, Environment

app    = Flask(__name__)
client = BMLConnect(api_key=os.environ["BML_API_KEY"], environment=Environment.PRODUCTION)
HOOK   = "https://yourapp.com/bml-webhook"

with app.app_context():
    client.webhooks.create(HOOK)

@app.route("/bml-webhook", methods=["POST"])
def webhook():
    nonce     = request.headers.get("X-Signature-Nonce", "")
    timestamp = request.headers.get("X-Signature-Timestamp", "")
    signature = request.headers.get("X-Signature", "")

    if nonce and timestamp and signature:
        # Current SHA-256 header verification
        if not client.verify_webhook_signature(nonce, timestamp, signature):
            return jsonify({"error": "Invalid signature"}), 403
    else:
        # Legacy originalSignature fallback (deprecated)
        payload = request.get_json(force=True) or {}
        if not client.verify_legacy_webhook_signature(payload, payload.get("originalSignature", "")):
            return jsonify({"error": "Invalid signature"}), 403

    payload = request.get_json(force=True) or {}
    print(f"Transaction {payload.get('id')} → {payload.get('state')}")
    return jsonify({"status": "ok"})
```

### FastAPI - async webhook receiver

```python
import os
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from bml_connect import BMLConnect, Environment

app    = FastAPI()
client = BMLConnect(api_key=os.environ["BML_API_KEY"], environment=Environment.PRODUCTION, async_mode=True)
HOOK   = "https://yourapp.com/bml-webhook"

@app.on_event("startup")
async def startup():
    await client.webhooks.create(HOOK)

@app.on_event("shutdown")
async def shutdown():
    await client.webhooks.delete(HOOK)
    await client.aclose()

@app.post("/bml-webhook")
async def webhook(
    request: Request,
    x_signature_nonce: str     = Header(default=""),
    x_signature_timestamp: str = Header(default=""),
    x_signature: str           = Header(default=""),
):
    if x_signature_nonce and x_signature_timestamp and x_signature:
        if not client.verify_webhook_signature(x_signature_nonce, x_signature_timestamp, x_signature):
            raise HTTPException(403, "Invalid signature")
    else:
        payload = await request.json()
        if not client.verify_legacy_webhook_signature(payload, payload.get("originalSignature", "")):
            raise HTTPException(403, "Invalid signature")

    payload = await request.json()
    print(f"Transaction {payload.get('id')} → {payload.get('state')}")
    return JSONResponse({"status": "ok"})
```

### Sanic

```python
from sanic import Sanic, response
from bml_connect import BMLConnect, Environment

app    = Sanic("BMLApp")
client = BMLConnect(api_key="your_api_key", environment=Environment.PRODUCTION)

@app.post("/bml-webhook")
async def webhook(request):
    nonce     = request.headers.get("X-Signature-Nonce", "")
    timestamp = request.headers.get("X-Signature-Timestamp", "")
    signature = request.headers.get("X-Signature", "")

    if nonce and timestamp and signature:
        if not client.verify_webhook_signature(nonce, timestamp, signature):
            return response.json({"error": "Invalid signature"}, status=403)
    else:
        payload = request.json or {}
        if not client.verify_legacy_webhook_signature(payload, payload.get("originalSignature", "")):
            return response.json({"error": "Invalid signature"}, status=403)

    return response.json({"status": "ok"})
```

---

## API Reference

### `BMLConnect(api_key, environment, *, async_mode)`

| Parameter     | Type                   | Default      | Description                                       |
| ------------- | ---------------------- | ------------ | ------------------------------------------------- |
| `api_key`     | `str`                  | required     | API key from BML merchant portal                  |
| `environment` | `Environment` or `str` | `PRODUCTION` | `Environment.SANDBOX` or `Environment.PRODUCTION` |
| `async_mode`  | `bool`                 | `False`      | Enable async/await mode                           |

### Resources

| Attribute             | Class                  | Description                                                   |
| --------------------- | ---------------------- | ------------------------------------------------------------- |
| `client.company`      | `CompanyResource`      | `GET /public/me`                                              |
| `client.webhooks`     | `WebhooksResource`     | Register / unregister webhook URLs                            |
| `client.transactions` | `TransactionsResource` | Create, retrieve, update transactions; send SMS/email         |
| `client.shops`        | `ShopsResource`        | Shops, products, categories, taxes, order fields, custom fees |
| `client.customers`    | `CustomersResource`    | Customer CRUD, token management, charge stored tokens         |

### Models

| Class               | Description                                  |
| ------------------- | -------------------------------------------- |
| `Transaction`       | Full transaction record (V2 fields included) |
| `Webhook`           | Registered webhook record                    |
| `Company`           | Merchant company details                     |
| `PaymentProvider`   | Provider info within a company               |
| `Shop`              | Shop / storefront                            |
| `Product`           | Product with price and SKU                   |
| `Category`          | Product category                             |
| `Tax`               | Tax rule                                     |
| `OrderField`        | Custom order form field                      |
| `CustomFee`         | Custom surcharge/fee                         |
| `Customer`          | Customer record                              |
| `CustomerToken`     | Stored payment token                         |
| `QRCode`            | QR code URL/image                            |
| `PaginatedResponse` | Paginated transaction list                   |

### Enums

```python
from bml_connect import Environment, TransactionState, SignMethod

Environment.SANDBOX       # → https://api.uat.merchants.bankofmaldives.com.mv
Environment.PRODUCTION    # → https://api.merchants.bankofmaldives.com.mv

TransactionState.CREATED
TransactionState.QR_CODE_GENERATED
TransactionState.CONFIRMED
TransactionState.CANCELLED
TransactionState.FAILED
TransactionState.EXPIRED

SignMethod.SHA1   # legacy only
SignMethod.MD5    # legacy only
```

### Exception Hierarchy

```
BMLConnectError
├── AuthenticationError   # 401 - invalid or missing API key
├── ValidationError       # 400 - malformed request
├── NotFoundError         # 404 - resource not found
├── RateLimitError        # 429 - too many requests
└── ServerError           # 5xx - BML server error
```

```python
from bml_connect import BMLConnectError, AuthenticationError, RateLimitError

try:
    txn = client.transactions.create({...})
except RateLimitError:
    time.sleep(60)
except AuthenticationError:
    print("Check your API key")
except BMLConnectError as e:
    print(f"[{e.code}] {e.message}  (HTTP {e.status_code})")
```

### `SignatureUtils` - Webhook Verification

```python
from bml_connect import SignatureUtils

# Current - SHA-256 of nonce + timestamp + api_key (header-based)
is_valid = SignatureUtils.verify_webhook_signature(nonce, timestamp, received_sig, api_key)

# Convenience: pass the full headers dict directly
is_valid = SignatureUtils.verify_webhook_headers(headers_dict, api_key)

# Deprecated - MD5 originalSignature in JSON body (v1 payloads only)
is_valid = SignatureUtils.verify_legacy_signature(payload_dict, original_sig, api_key)
```

---

## Migration from v1.x

### What changed

| v1.x                                            | v2.0                                                                  | Notes                                                |
| ----------------------------------------------- | --------------------------------------------------------------------- | ---------------------------------------------------- |
| `BMLConnect(api_key, app_id, ...)`              | `BMLConnect(api_key, ...)`                                            | `app_id` is now optional (no longer sent in headers) |
| `client.transactions.create_transaction({...})` | `client.transactions.create({...})`                                   | Targets V2 endpoint; no signature                    |
| `client.transactions.get_transaction(id)`       | `client.transactions.get(id)`                                         | Alias preserved                                      |
| `client.transactions.list_transactions(...)`    | `client.transactions.list(...)`                                       | Alias preserved                                      |
| `SignatureUtils.generate_signature(...)`        | `SignatureUtils.generate_legacy_signature(...)`                       | Old name kept as alias                               |
| `SignatureUtils.verify_signature(...)`          | `SignatureUtils.verify_legacy_signature(...)`                         | Old name kept as alias                               |
| `client.verify_webhook_signature(payload, sig)` | unchanged for legacy; new `verify_webhook_payload(raw, sig)` for HMAC |                                                      |

### Signature no longer required for new transactions

V2 transactions do **not** require you to compute and inject a `signature` field.
Simply remove the `signature`, `signMethod`, and `apiKey` fields from your payload.

If you still need the legacy v1 endpoint, use `client.transactions.create_v1({...})`
which automatically generates the SHA-1 signature for you.

```python
# Before (v1.x)
transaction = client.transactions.create_transaction({
    "amount": 1500,
    "currency": "MVR",
    "provider": "alipay",
    "signMethod": "sha1",
    ...
})

# After (v2.0) - no signature, no signMethod, no provider field at top level
transaction = client.transactions.create({
    "redirectUrl": "https://yourapp.com/thanks",
    "localId": "INV-001",
    "order": {
        "shopId": "YOUR_SHOP_ID",
        "products": [{"productId": "PROD_ID", "numberOfItems": 1}],
    },
})
```

---

## Project Structure

```
bml-connect-python/
├── src/bml_connect/
│   ├── __init__.py       # Public API surface
│   ├── client.py         # BMLConnect façade
│   ├── resources.py      # Resource managers (transactions, shops, …)
│   ├── models.py         # Dataclass models
│   ├── transport.py      # HTTP layer (sync + async)
│   ├── signature.py      # SignatureUtils
│   └── exceptions.py     # Exception hierarchy
├── tests/
│   ├── test_sdk.py
│   └── test_client.py
├── examples/
│   ├── basic_sync.py
│   ├── basic_async.py
│   ├── webhook_flask.py
│   ├── webhook_fastapi.py
│   ├── webhook_plain.py
│   └── webhook_sanic.py
├── pyproject.toml
└── README.md
```

---

## Development

### Setup

```bash
git clone https://github.com/quillfires/bml-connect-python.git
cd bml-connect-python
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Quality

```bash
black .       # format
flake8 .      # lint
mypy src/     # type check
```

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING](https://github.com/quillfires/bml-connect-python/blob/main/CONTRIBUTING.md) before submitting a pull request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Make your changes and add tests
4. Ensure all tests pass (`pytest`)
5. Submit a pull request

---

## License

MIT - see [LICENSE](https://github.com/quillfires/bml-connect-python/blob/main/LICENSE) for details.

---

## Support

- 📖 [Documentation](https://github.com/quillfires/bml-connect-python/wiki)
- 🐛 [Issue Tracker](https://github.com/quillfires/bml-connect-python/issues)
- 💬 [Discussions](https://github.com/quillfires/bml-connect-python/discussions)
- 📋 [Changelog](https://github.com/quillfires/bml-connect-python/blob/main/CHANGELOG.md)

## Security

Please report security vulnerabilities by email to fayaz.quill@gmail.com rather than opening a public issue.
See [SECURITY](https://github.com/quillfires/bml-connect-python/blob/main/SECURITY.md) for the full policy.

---

Made with ❤️ for the Maldivian developer community
