# BML Connect Python SDK

[![PyPI version](https://badge.fury.io/py/bml-connect-python.svg)](https://badge.fury.io/py/bml-connect-python)
[![Python Support](https://img.shields.io/pypi/pyversions/bml-connect-python.svg)](https://pypi.org/project/bml-connect-python/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[![ViewCount](https://views.whatilearened.today/views/github/quillfires/bml-connect-python.svg)](https://views.whatilearened.today/views/github/quillfires/bml-connect-python.svg) [![GitHub forks](https://img.shields.io/github/forks/quillfires/bml-connect-python)](https://github.com/quillfires/bml-connect-python/network) [![GitHub stars](https://img.shields.io/github/stars/quillfires/bml-connect-python.svg?color=ffd40c)](https://github.com/quillfires/bml-connect-python/stargazers) [![PyPI - Downloads](https://img.shields.io/pypi/dm/bml-connect-python?color=orange&label=PIP%20-%20Installs)](https://pypi.python.org/pypi/bml-connect-python/) [![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/quillfires/bml-connect-python/issues) [![GitHub issues](https://img.shields.io/github/issues/quillfires/bml-connect-python.svg?color=808080)](https://github.com/quillfires/bml-connect-python/issues)

Python SDK for Bank of Maldives Connect API v2 with synchronous and asynchronous support.  
Compatible with all Python frameworks including Django, Flask, FastAPI, and Sanic.

> **v2.0.0** - full coverage of the BML Connect v2 API across all four integration methods: Redirect, Direct, Card-On-File Tokenization, and PCI Merchant Tokenization.

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Integration Methods](#integration-methods)
  - [Redirect Method](#redirect-method)
  - [Direct Method](#direct-method)
  - [Card-On-File / Tokenization](#card-on-file--tokenization)
  - [PCI Merchant Tokenization](#pci-merchant-tokenization)
- [Webhooks](#webhooks)
- [Transaction States](#transaction-states)
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

- **🔄 Sync/Async Support** - every resource has both sync and `async/await` variants
- **🎯 Four Integration Methods** - Redirect, Direct (QR + card), Card-On-File, PCI Tokenization
- **🪝 Webhook Registration** - register your endpoint directly in BML's backend
- **🔔 Webhook Event Parsing** - `WebhookEvent` model for `NOTIFY_TRANSACTION_CHANGE` and `NOTIFY_TOKENISATION_STATUS`
- **🔐 Webhook Verification** - SHA-256 header scheme with legacy MD5 fallback
- **🔑 PCI Card Encryption** - `CardEncryption` utility for RSA-OAEP SHA-256 server-side card encryption
- **📝 Type Annotations** - full type hints throughout
- **🛡️ Error Handling** - structured exception hierarchy
- **🚀 Framework Agnostic** - works with Django, Flask, FastAPI, Sanic, or plain scripts
- **📄 MIT Licensed** - open source and free to use

---

## Installation

```bash
pip install bml-connect-python
```

For PCI Merchant Tokenization (server-side card encryption), also install:

```bash
pip install cryptography
```

**Requires Python 3.9+**

---

## Integration Methods

All four methods use the same `POST /public/v2/transactions` endpoint. The payload and the response fields you care about differ by method.

---

### Redirect Method

The easiest integration. BML hosts the payment page - you control branding via the Merchant Dashboard under **Settings → Branding**.

```python
from bml_connect import BMLConnect, Environment

with BMLConnect(api_key="sk_...", environment=Environment.PRODUCTION) as client:
    client.webhooks.create("https://yourapp.com/bml-webhook")

    txn = client.transactions.create({
        "redirectUrl": "https://yourapp.com/payment-complete",
        "localId": "INV-001",
        "customerReference": "Order #42",   # shown on customer receipt
        "webhook": "https://yourapp.com/bml-webhook",
        "locale": "en",                     # or th_TH, en_GB, etc.
        "order": {
            "shopId": "SHOP_ID",
            "products": [{"productId": "PROD_ID", "numberOfItems": 2}],
        },
    })

    print(txn.url)        # full payment page URL
    print(txn.short_url)  # shortened URL - ideal for SMS and messaging apps
```

After payment, BML redirects back to `redirectUrl` and appends `transactionId`, `state`, and `signature` as query parameters. Always confirm the final state via the API - never rely solely on redirect parameters:

```python
txn = client.transactions.get("TRANSACTION_ID")
print(txn.state)   # e.g. TransactionState.CONFIRMED
```

#### Customising the Payment Portal

Use `paymentPortalExperience` to streamline the hosted page:

```python
txn = client.transactions.create({
    "redirectUrl": "https://yourapp.com/thanks",
    "provider": "alipay",              # pre-select provider
    "customer": {"name": "Alice", "email": "alice@example.com", ...},
    "paymentPortalExperience": {
        "skipCustomerForm": True,          # requires customer info in request
        "skipProviderSelection": True,     # requires provider in request
        "externalWebsiteTermsAccepted": True,
        "externalWebsiteTermsUrl": "https://yourapp.com/terms",
    },
})
```

#### Handling Payment Failures

| Scenario | How to configure |
|---|---|
| Let BML handle retries (default) | No extra fields needed |
| Redirect on cancel/fail | Set `redirectUrl` - BML appends state, id, errors |
| No retries allowed | Add `"allowRetry": false` |
| Merchant handles retries | Set `"paymentAttemptFailureUrl": "https://yourapp.com/checkout/123"` - transaction stays `QR_CODE_GENERATED` so it can be retried with the same ID |

---

### Direct Method

Your UI, your checkout experience. You handle displaying the payment interface.

**Provider values and what they return:**

| Provider | Value | Response field |
|---|---|---|
| Domestic card (MPGS) | `mpgs` | `url` - redirect to secure card form |
| International card | `debit_credit_card` | `url` - redirect to secure card form |
| Alipay online | `alipay_online` | `url` - redirect |
| Alipay in-person QR | `alipay` | `vendor_qr_code` - encode into QR image |
| UnionPay QR | `unionpay` | `vendor_qr_code` |
| WechatPay QR | `wechatpay` | `vendor_qr_code` |
| BML MobilePay QR | `bml_mobilepay` | `vendor_qr_code` |
| Cash | `cash` | - |

**QR providers** - generate and display a QR code:

```python
import qrcode

txn = client.transactions.create({
    "amount": 1000,
    "currency": "USD",
    "provider": "alipay",   # or unionpay / wechatpay / bml_mobilepay
    "webhook": "https://yourapp.com/bml-webhook",
    "locale": "en",
    "customer": {"name": "Alice", "email": "alice@example.com"},
})

# Encode vendor_qr_code into a QR image and display to the customer
qr = qrcode.make(txn.vendor_qr_code)
qr.save("payment_qr.png")
```

**Card / online providers** - redirect customer to the secure form:

```python
txn = client.transactions.create({
    "amount": 2500,
    "currency": "USD",
    "provider": "mpgs",     # or debit_credit_card / alipay_online
    "redirectUrl": "https://yourapp.com/payment-complete",
    "webhook": "https://yourapp.com/bml-webhook",
    "customer": {
        "name": "Bob Jones",
        "email": "bob@example.com",
        "billingAddress1": "1 Main Street",
        "billingCity": "Malé",
        "billingCountry": "MV",
    },
    "paymentPortalExperience": {
        "skipCustomerForm": True,
        "skipProviderSelection": True,
    },
})

redirect_to(txn.url)
```

You can also use the `Provider` enum:

```python
from bml_connect import Provider

txn = client.transactions.create({
    "provider": Provider.ALIPAY.value,
    ...
})
```

Use **polling** or **webhooks** to track payment status. See [Webhooks](#webhooks) for details.

---

### Card-On-File / Tokenization

Store a customer's card for future recurring or one-click charges. Only `mpgs` and `debit_credit_card` support tokenisation.

#### Step 1 - Capture the card on the first transaction

You can create the customer and capture their card in **one call**:

```python
txn = client.transactions.create({
    "amount": 100,
    "currency": "USD",
    "tokenizationDetails": {
        "tokenize": True,
        "paymentType": "UNSCHEDULED",
        "recurringFrequency": "UNSCHEDULED",
    },
    "customer": {
        "name": "Alice Smith",
        "email": "alice@example.com",
        "billingAddress1": "1 Coral Way",
        "billingCity": "Malé",
        "billingCountry": "MV",
        "currency": "MVR",
    },
    "customerAsPayer": True,
    "webhook": "https://yourapp.com/bml-webhook",
    "redirectUrl": "https://yourapp.com/payment-complete",
})
# customer_id is available at txn.customer_id after the response
```

Or use an **existing customer**:

```python
txn = client.transactions.create({
    "amount": 100,
    "currency": "USD",
    "tokenizationDetails": {
        "tokenize": True,
        "paymentType": "UNSCHEDULED",
        "recurringFrequency": "UNSCHEDULED",
    },
    "customerId": "EXISTING_CUSTOMER_ID",
    "customerAsPayer": True,
    "webhook": "https://yourapp.com/bml-webhook",
})
```

After the customer completes the payment, BML fires a `NOTIFY_TOKENISATION_STATUS` webhook confirming the card was stored.

#### Step 2 - List stored tokens

```python
tokens = client.customers.list_tokens("CUSTOMER_ID")
for t in tokens:
    print(t.id, t.brand, t.padded_card_number,
          f"{t.token_expiry_month}/{t.token_expiry_year}",
          "default" if t.default_token else "")
```

#### Step 3 - Charge a stored token

First create a transaction for the customer, then charge it against their token:

```python
# Create the transaction shell
txn = client.transactions.create({
    "amount": 5000,
    "currency": "USD",
    "customerId": "CUSTOMER_ID",
})

# Option 1 - specify token by ID (recommended)
result = client.customers.charge({
    "customerId": "CUSTOMER_ID",
    "transactionId": txn.id,
    "tokenId": tokens[0].id,
})

# Option 2 - specify by raw token string
result = client.customers.charge({
    "customerId": "CUSTOMER_ID",
    "transactionId": txn.id,
    "token": tokens[0].token,
})

# Option 3 - use default token (no token field)
result = client.customers.charge({
    "customerId": "CUSTOMER_ID",
    "transactionId": txn.id,
})

# Always confirm via API query
confirmed = client.transactions.get(txn.id)
print(confirmed.state)   # TransactionState.CONFIRMED
```

---

### PCI Merchant Tokenization

For PCI-approved merchants who capture card details directly. Requires a separate public/private key pair created in **Merchant Dashboard → Connect**.

> **Key rules:** Your private key (`sk_...`) and public key (`pk_...`) must be from the **same app**. Never mix keys across apps.

#### Setup

```python
from bml_connect import BMLConnect, CardEncryption, Environment

client = BMLConnect(
    api_key="sk_your_private_key",    # private key - creates transactions
    public_key="pk_your_public_key",  # public key - calls /public-client/* endpoints
    environment=Environment.PRODUCTION,
)
```

#### Step 1 - Fetch the RSA encryption key

```python
# Always fetch fresh - this key can rotate at any time
enc_key = client.public_client.get_tokens_public_key()
print(enc_key.key_id)
print(enc_key.pem)     # PEM-formatted public key ready for encryption
```

#### Step 2 - Encrypt card data

```python
card_b64 = CardEncryption.encrypt(enc_key.pem, {
    "cardNumberRaw":   "4111111111111111",
    "cardVDRaw":       "123",
    "cardExpiryMonth": 12,
    "cardExpiryYear":  29,
})
```

`CardEncryption.encrypt` uses RSA-OAEP with SHA-256, matching the algorithm documented by BML. It requires the `cryptography` package.

You can also validate before encrypting:

```python
from bml_connect import CardEncryption

CardEncryption.validate_card_payload({...})   # raises ValueError if invalid
```

#### Step 3 - Submit encrypted card data

```python
result = client.public_client.add_card(
    card_data=card_b64,
    key_id=enc_key.key_id,
    customer_id="CUSTOMER_ID",
    redirect="https://yourapp.com/tokenisation-callback",
    webhook="https://yourapp.com/bml-webhook",   # optional
)

# Redirect customer to 3DS authentication
redirect_to(result.next_action.url)

# Store for correlation (not a payment token)
client_side_token_id = result.next_action.client_side_token_id
```

#### Step 4 - Handle the callback

BML redirects to your `redirect` URL with query parameters:

```
# Success
https://yourapp.com/tokenisation-callback?tokenId=<id>&clientSideTokenId=<id>&customerId=<id>&status=TOKENISATION_SUCCESS

# Failure
https://yourapp.com/tokenisation-callback?clientSideTokenId=<id>&customerId=<id>&status=TOKENISATION_FAILURE
```

The `tokenId` on success is the **Customer Token ID** - use this for charging.

```python
# Flask callback handler example
@app.route("/tokenisation-callback")
def tokenisation_callback():
    status   = request.args.get("status")
    token_id = request.args.get("tokenId")       # only on success

    if status == "TOKENISATION_SUCCESS" and token_id:
        # Store token_id in your database, then charge it when needed
        pass
    else:
        # Handle failure - prompt customer to re-enter card details
        pass
```

> Always implement the async webhook listener too - the customer may close the browser before the redirect completes.

---

## Webhooks

### Register / Unregister

```python
hook = client.webhooks.create("https://yourapp.com/bml-webhook")
print(hook.id, hook.hook_url)

client.webhooks.delete("https://yourapp.com/bml-webhook")
```

### Receiving & Verifying

BML signs every webhook POST with three headers:

| Header | Description |
|---|---|
| `X-Signature-Nonce` | Unique request identifier |
| `X-Signature-Timestamp` | Unix timestamp of the request |
| `X-Signature` | `SHA-256("{nonce}{timestamp}{api_key}")` as hex |

```python
# Verify from a headers dict (works with Flask, Django, Sanic, etc.)
if not client.verify_webhook_headers(request.headers):
    abort(403)

# Or verify the three values individually
if not client.verify_webhook_signature(nonce, timestamp, signature):
    abort(403)
```

### Parsing Webhook Events

Use `WebhookEvent` to parse the notification body:

```python
from bml_connect import WebhookEvent, WebhookEventType, TokenisationStatus

event = WebhookEvent.from_dict(request.get_json())

if event.event_type == WebhookEventType.NOTIFY_TRANSACTION_CHANGE:
    print(f"Transaction {event.transaction_id} → {event.state}")
    print(f"Amount: {event.amount_formatted}")

elif event.event_type == WebhookEventType.NOTIFY_TOKENISATION_STATUS:
    if event.tokenisation_status == TokenisationStatus.SUCCESS:
        tokens = client.customers.list_tokens(event.customer_id)
        print(f"Card stored - {len(tokens)} token(s) on file")
    else:
        print(f"Tokenisation failed for customer {event.customer_id}")
```

### Legacy `originalSignature` (deprecated)

Older v1 payloads included an `originalSignature` field in the body. The SDK still supports verification for backward compatibility, but BML recommends always querying the API for the authoritative state:

```python
payload = request.get_json()
if not client.verify_legacy_webhook_signature(payload, payload.get("originalSignature", "")):
    abort(403)

# Confirm via API
txn = client.transactions.get(payload["transactionId"])
```

---

## Transaction States

| State | Description |
|---|---|
| `INITIATED` | Payment created; QR asset not yet ready |
| `QR_CODE_GENERATED` | Pending - awaiting customer payment action |
| `CONFIRMED` | Payment completed successfully |
| `CANCELLED` | User cancelled or link timed out |
| `FAILED` | Permanently failed - cannot be retried |
| `EXPIRED` | Payment link expired |
| `VOIDED` | Payment reversed - excluded from settlements |
| `AUTHORIZED` | Pre-auth approved; funds not yet captured |
| `REFUND_REQUESTED` | Refund requested, under review |
| `REFUNDED` | Refund completed |

```python
from bml_connect import TransactionState

txn = client.transactions.get("TRANSACTION_ID")

if txn.state == TransactionState.CONFIRMED:
    # fulfil order
    pass
elif txn.state in (TransactionState.CANCELLED, TransactionState.FAILED):
    # notify customer, initiate new transaction
    pass
elif txn.state == TransactionState.AUTHORIZED:
    # capture funds before pre-auth expires
    pass
```

---

## Sharing Payment Links

Both methods are **rate-limited to once per minute** per transaction.

```python
# SMS - country code prefix is optional
client.transactions.send_sms("TRANSACTION_ID", "9609601234")

# Email - single address or a list
client.transactions.send_email("TRANSACTION_ID", "customer@example.com")
client.transactions.send_email("TRANSACTION_ID", ["alice@example.com", "bob@example.com"])
```

Use `txn.short_url` (instead of `txn.url`) when sharing in SMS or messaging apps to save characters.

---

## Transactions - Additional Operations

### Update

Update mutable metadata after creation:

```python
txn = client.transactions.update(
    "TRANSACTION_ID",
    customer_reference="Booking Ref #99",    # up to 140 chars
    local_data='{"reservationId": "R-001"}', # up to 1000 chars, merchant-side only
    pnr="ABC123",                            # up to 64 chars
)
```

### Retrieve

```python
txn = client.transactions.get("TRANSACTION_ID")
print(txn.state, txn.amount_formatted, txn.can_refund_if_confirmed)
```

### List

```python
page = client.transactions.list(page=1, per_page=20, state="CONFIRMED")
for txn in page.items:
    print(txn.id, txn.amount, txn.state)
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
    "name": "Flat White", "price": 2500, "currency": "MVR", "sku": "FW-001",
})
product  = client.shops.get_product("SHOP_ID", "PRODUCT_ID")
product  = client.shops.update_product("SHOP_ID", "PRODUCT_ID", {"price": 3000})
product  = client.shops.update_product_by_sku("SHOP_ID", {"sku": "FW-001", "price": 3000})
products = client.shops.create_products_batch("SHOP_ID", [
    {"name": "Espresso", "price": 1500, "currency": "MVR"},
    {"name": "Latte",    "price": 2000, "currency": "MVR"},
])
with open("espresso.jpg", "rb") as f:
    client.shops.upload_product_image("SHOP_ID", "PRODUCT_ID", f.read(), "espresso.jpg")
client.shops.delete_product("SHOP_ID", "PRODUCT_ID")
```

### Categories, Taxes, Order Fields, Custom Fees

```python
# Categories
cats = client.shops.list_categories("SHOP_ID")
cat  = client.shops.create_category("SHOP_ID", {"name": "Hot Drinks"})
cat  = client.shops.update_category("SHOP_ID", "CAT_ID", {"name": "Hot Beverages"})
client.shops.delete_category("SHOP_ID", "CAT_ID")

# Taxes
taxes = client.shops.list_taxes("SHOP_ID")
tax   = client.shops.create_tax("SHOP_ID", {
    "name": "Tourist Tax", "code": "TT", "percentage": 10.0, "applyOn": "PRODUCT"
})
client.shops.delete_tax("SHOP_ID", "TAX_ID")
client.shops.update_products_taxes("SHOP_ID", {"taxIds": ["TAX_ID_1", "TAX_ID_2"]})

# Order Fields
field = client.shops.create_order_field("SHOP_ID", {"label": "Table Number", "type": "text"})
client.shops.update_order_field("SHOP_ID", "FIELD_ID", {"checked": True})

# Custom Fees
fee = client.shops.create_custom_fee("SHOP_ID", {
    "name": "Nature Donation", "description": "Optional donation", "fee": 100
})
client.shops.update_custom_fee("SHOP_ID", "FEE_ID", {"fee": 200})
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
client.customers.delete("CUSTOMER_ID")   # archives, does not hard-delete
```

### Tokens

```python
tokens = client.customers.list_tokens("CUSTOMER_ID")
token  = client.customers.get_token("CUSTOMER_ID", "TOKEN_ID")
client.customers.delete_token("CUSTOMER_ID", "TOKEN_ID")
```

---

## Company Info

```python
companies = client.company.get()
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
from bml_connect import BMLConnect, Environment, WebhookEvent

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
        if not client.verify_webhook_signature(nonce, timestamp, signature):
            return jsonify({"error": "Invalid signature"}), 403
    else:
        payload = request.get_json(force=True) or {}
        if not client.verify_legacy_webhook_signature(payload, payload.get("originalSignature", "")):
            return jsonify({"error": "Invalid signature"}), 403

    event = WebhookEvent.from_dict(request.get_json(force=True) or {})
    app.logger.info("Webhook: type=%s txn=%s state=%s", event.event_type, event.transaction_id, event.state)
    return jsonify({"status": "ok"})
```

### FastAPI - async webhook receiver

```python
import os
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from bml_connect import BMLConnect, Environment, WebhookEvent

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

    event = WebhookEvent.from_dict(await request.json())
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

### `BMLConnect(api_key, environment, *, async_mode, public_key)`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `api_key` | `str` | required | Private API key (`sk_...`) from BML merchant portal |
| `environment` | `Environment` or `str` | `PRODUCTION` | `Environment.SANDBOX` or `Environment.PRODUCTION` |
| `async_mode` | `bool` | `False` | Enable async/await mode |
| `public_key` | `str` | `None` | Public application key (`pk_...`) - required for PCI Merchant Tokenization only. Must be from the same app as `api_key`. |

### Resources

| Attribute | Description |
|---|---|
| `client.company` | `GET /public/me` |
| `client.webhooks` | Register / unregister webhook URLs |
| `client.transactions` | Create (all four methods), retrieve, update, SMS/email share |
| `client.shops` | Shops, products, categories, taxes, order fields, custom fees |
| `client.customers` | Customer CRUD, token management, charge stored tokens |
| `client.public_client` | PCI Tokenization - fetch RSA key, submit encrypted card data. `None` if `public_key` not provided. |

### Models

| Class | Description |
|---|---|
| `Transaction` | Full transaction record - all V2 fields |
| `WebhookEvent` | Parsed webhook notification - `NOTIFY_TRANSACTION_CHANGE` or `NOTIFY_TOKENISATION_STATUS` |
| `Webhook` | Registered webhook record |
| `Company` | Merchant company details |
| `PaymentProvider` | Provider info within a company |
| `Shop` | Shop / storefront |
| `Product` | Product with price and SKU |
| `Category` | Product category |
| `Tax` | Tax rule |
| `OrderField` | Custom order form field |
| `CustomFee` | Custom surcharge/fee |
| `Customer` | Customer record |
| `CustomerToken` | Stored card-on-file token |
| `QRCode` | QR code URL/image |
| `PaginatedResponse` | Paginated transaction list |
| `TokensPublicKey` | RSA encryption key for PCI tokenization |
| `ClientTokenResponse` | Response from `POST /public-client/tokens` - contains 3DS redirect URL |

### Enums

```python
from bml_connect import Environment, TransactionState, Provider, WebhookEventType, TokenisationStatus

Environment.SANDBOX       # → https://api.uat.merchants.bankofmaldives.com.mv
Environment.PRODUCTION    # → https://api.merchants.bankofmaldives.com.mv

TransactionState.INITIATED        # created, QR not yet ready
TransactionState.QR_CODE_GENERATED
TransactionState.CONFIRMED
TransactionState.CANCELLED
TransactionState.FAILED
TransactionState.EXPIRED
TransactionState.VOIDED
TransactionState.AUTHORIZED
TransactionState.REFUND_REQUESTED
TransactionState.REFUNDED

Provider.MPGS               # domestic card (tokenisation supported)
Provider.DEBIT_CREDIT_CARD  # international card (tokenisation supported)
Provider.ALIPAY             # in-person QR
Provider.ALIPAY_ONLINE      # e-commerce redirect
Provider.UNIONPAY           # QR
Provider.WECHATPAY          # QR
Provider.BML_MOBILEPAY      # QR
Provider.CASH

WebhookEventType.NOTIFY_TRANSACTION_CHANGE
WebhookEventType.NOTIFY_TOKENISATION_STATUS

TokenisationStatus.SUCCESS   # TOKENISATION_SUCCESS
TokenisationStatus.FAILURE   # TOKENISATION_FAILURE
```

### Exception Hierarchy

```
BMLConnectError
├── AuthenticationError   # 401 - invalid or missing API key
├── ValidationError       # 400 - malformed request
├── NotFoundError         # 404 - resource not found
├── RateLimitError        # 429 - too many requests (SMS/email: once/min)
└── ServerError           # 5xx - BML server error
```

```python
from bml_connect import BMLConnectError, AuthenticationError, RateLimitError
import time

try:
    txn = client.transactions.create({...})
except RateLimitError:
    time.sleep(60)
    txn = client.transactions.create({...})
except AuthenticationError:
    print("Check your API key")
except BMLConnectError as e:
    print(f"[{e.code}] {e.message}  (HTTP {e.status_code})")
```

### `SignatureUtils` - Webhook Verification

```python
from bml_connect import SignatureUtils

# Current - SHA-256 of nonce + timestamp + api_key
is_valid = SignatureUtils.verify_webhook_signature(nonce, timestamp, received_sig, api_key)
is_valid = SignatureUtils.verify_webhook_headers(headers_dict, api_key)

# Deprecated - MD5 originalSignature in JSON body (v1 payloads only)
is_valid = SignatureUtils.verify_legacy_signature(payload_dict, original_sig, api_key)
```

### `CardEncryption` - PCI Card Encryption

```python
from bml_connect import CardEncryption

# Validate before encrypting
CardEncryption.validate_card_payload({
    "cardNumberRaw": "4111111111111111",
    "cardVDRaw": "123",
    "cardExpiryMonth": 12,
    "cardExpiryYear": 29,
})

# Encrypt - returns Base64 RSA-OAEP SHA-256 ciphertext
card_b64 = CardEncryption.encrypt(enc_key.pem, {
    "cardNumberRaw": "4111111111111111",
    "cardVDRaw": "123",
    "cardExpiryMonth": 12,
    "cardExpiryYear": 29,
})
```

---

## Migration from v1.x

| v1.x | v2.0 | Notes |
|---|---|---|
| `BMLConnect(api_key, app_id, ...)` | `BMLConnect(api_key, ...)` | `app_id` optional, `public_key` new |
| `client.transactions.create_transaction({...})` | `client.transactions.create({...})` | V2 endpoint, no signature, all four methods |
| `client.transactions.get_transaction(id)` | `client.transactions.get(id)` | Alias preserved |
| `client.transactions.list_transactions(...)` | `client.transactions.list(...)` | Alias preserved |
| `SignatureUtils.generate_signature(...)` | Raises `NotImplementedError` | V2 transactions don't need request signatures |
| `SignatureUtils.verify_signature(...)` | `SignatureUtils.verify_legacy_signature(...)` | Old name kept as alias |
| `client.verify_webhook_signature(payload, sig)` | `client.verify_legacy_webhook_signature(payload, sig)` | Renamed to clarify it's the deprecated path |
| `client.verify_webhook_payload(raw, sig)` | `client.verify_webhook_headers(headers)` | New header-based scheme |

V2 transactions require no `signature`, `signMethod`, or `apiKey` in the payload:

```python
# Before (v1.x)
client.transactions.create_transaction({
    "amount": 1500, "currency": "MVR",
    "provider": "alipay", "signMethod": "sha1",
})

# After (v2.0)
client.transactions.create({
    "redirectUrl": "https://yourapp.com/thanks",
    "localId": "INV-001",
    "order": {"shopId": "SHOP_ID", "products": [...]},
})
```

---

## Project Structure

```
bml-connect-python/
├── src/bml_connect/
│   ├── __init__.py       # Public API surface
│   ├── client.py         # BMLConnect façade
│   ├── resources.py      # Resource managers
│   ├── models.py         # Dataclass models + enums
│   ├── transport.py      # HTTP layer (sync + async)
│   ├── signature.py      # SignatureUtils
│   ├── crypto.py         # CardEncryption (PCI tokenization)
│   └── exceptions.py     # Exception hierarchy
├── tests/
│   ├── test_sdk.py
│   └── test_client.py
├── examples/
│   ├── basic_sync.py
│   ├── basic_async.py
│   ├── direct_method.py        # Direct Method - QR and card
│   ├── card_on_file.py         # Card-On-File tokenization + recurring charge
│   ├── pci_tokenization.py     # PCI Merchant Tokenization
│   ├── webhook_flask.py
│   ├── webhook_fastapi.py
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
poetry install
```

### Running Tests

```bash
poetry run pytest -v
```

### Code Quality

```bash
poetry run isort src/ tests/
poetry run black src/ tests/
poetry run mypy src/
poetry run flake8 src/ tests/
```

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a pull request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Make your changes and add tests
4. Ensure all checks pass (`poetry run pytest`)
5. Submit a pull request

---

## License

MIT - see [LICENSE](LICENSE) for details.

---

## Support

- 📖 [Documentation](https://github.com/quillfires/bml-connect-python/wiki)
- 🐛 [Issue Tracker](https://github.com/quillfires/bml-connect-python/issues)
- 💬 [Discussions](https://github.com/quillfires/bml-connect-python/discussions)
- 📋 [Changelog](CHANGELOG.md)

## Security

Please report security vulnerabilities by email to fayaz.quill@gmail.com rather than opening a public issue. See [SECURITY.md](SECURITY.md) for the full policy.

---

Made with ❤️ for the Maldivian developer community
