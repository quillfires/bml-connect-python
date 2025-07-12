# BML Connect Python SDK

[![PyPI Version](https://img.shields.io/pypi/v/bml-connect-python.svg)](https://pypi.org/project/bml-connect-python/)
[![Python Versions](https://img.shields.io/pypi/pyversions/bml-connect-python.svg)](https://pypi.org/project/bml-connect-python/)
[![License](https://img.shields.io/pypi/l/bml-connect-python.svg)](https://opensource.org/licenses/MIT)

Python SDK for Bank of Maldives Connect API with synchronous and asynchronous support.  
Compatible with all Python frameworks including Django, Flask, FastAPI, and Sanic.

---

## Features

- **Sync/Async Support:** Choose your preferred programming style
- **Full API Coverage:** Transactions, webhooks, and signature verification
- **Type Annotations:** Full type hint support for better development experience
- **Error Handling:** Comprehensive error hierarchy for easy debugging
- **Framework Agnostic:** Works with any Python web framework
- **MIT Licensed:** Open source and free to use

---

## Installation

```bash
pip install bml-connect-python
```

---

## Quick Start

### Synchronous Client

```python
from bml_connect import BMLConnect, Environment

client = BMLConnect(
    api_key="your_api_key",
    app_id="your_app_id",
    environment=Environment.SANDBOX
)

try:
    transaction = client.transactions.create_transaction({
        "amount": 1500,  # 15.00 MVR
        "currency": "MVR",
        "provider": "alipay",
        "redirectUrl": "https://yourstore.com/success",
        "localId": "order_123",
        "customerReference": "Customer #456"
    })
    print(f"Transaction ID: {transaction.transaction_id}")
    print(f"Payment URL: {transaction.url}")
except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
```

### Asynchronous Client

```python
import asyncio
from bml_connect import BMLConnect, Environment

async def main():
    client = BMLConnect(
        api_key="your_api_key",
        app_id="your_app_id",
        environment=Environment.SANDBOX,
        async_mode=True
    )
    try:
        transaction = await client.transactions.create_transaction({
            "amount": 2000,
            "currency": "MVR",
            "provider": "wechat",
            "redirectUrl": "https://yourstore.com/success"
        })
        print(f"Transaction ID: {transaction.transaction_id}")
    finally:
        await client.aclose()

asyncio.run(main())
```

---

## Webhook Verification

### Flask Example

```python
from flask import Flask, request, jsonify
from bml_connect import BMLConnect

app = Flask(__name__)
client = BMLConnect(api_key="your_api_key", app_id="your_app_id")

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_json()
    signature = payload.get('signature')
    if client.verify_webhook_signature(payload, signature):
        # Process webhook
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"error": "Invalid signature"}), 403
```

### FastAPI Example

```python
from fastapi import FastAPI, Request, HTTPException
from bml_connect import BMLConnect

app = FastAPI()
client = BMLConnect(api_key="your_api_key", app_id="your_app_id")

@app.post("/webhook")
async def handle_webhook(request: Request):
    payload = await request.json()
    signature = payload.get("signature")
    if client.verify_webhook_signature(payload, signature):
        return {"status": "success"}
    else:
        raise HTTPException(403, "Invalid signature")
```

### Sanic Example

```python
from sanic import Sanic, response
from bml_connect import BMLConnect

app = Sanic("BMLWebhook")
client = BMLConnect(api_key="your_api_key", app_id="your_app_id")

@app.post('/webhook')
async def webhook(request):
    payload = request.json
    signature = payload.get('signature')
    if client.verify_webhook_signature(payload, signature):
        return response.json({"status": "success"})
    else:
        return response.json({"error": "Invalid signature"}, status=403)
```

---

## API Reference

### Main Classes

- `BMLConnect`: Main entry point for the SDK.
- `Transaction`: Transaction object.
- `QRCode`: QR code details.
- `PaginatedResponse`: For paginated transaction lists.
- `Environment`: Enum for `SANDBOX` and `PRODUCTION`.
- `SignMethod`: Enum for signature methods.
- `TransactionState`: Enum for transaction states.

### Error Classes

- `BMLConnectError`
- `AuthenticationError`
- `ValidationError`
- `NotFoundError`
- `ServerError`
- `RateLimitError`

### Utilities

- `SignatureUtils.generate_signature(data, api_key, method)`
- `SignatureUtils.verify_signature(data, signature, api_key, method)`

---

## Development

### Requirements

- Python 3.7+
- See `requirements.txt` and `requirements-dev.txt` for dependencies.

### Testing

```bash
pip install -e .[dev]
pytest
```

### Formatting & Linting

```bash
black .
flake8 .
mypy .
```

---

## Packaging

- Uses `pyproject.toml` for build configuration.
- Source code is in `src/bml_connect/`.
- Examples in `examples/`.
- Tests in `tests/`.

---

## License

MIT License. See `LICENSE` for details.

---

## Links

- [Homepage](https://github.com/bankofmaldives/bml-connect-python)
- [Documentation](https://bml-connect-python.readthedocs.io)
- [API Reference](docs/api_reference.md)
- [Changelog](https://github.com/bankofmaldives/bml-connect-python/releases)

---

## Contributing

Pull requests and issues are welcome! See the documentation for guidelines.
