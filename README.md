# BML Connect Python SDK

[![PyPI version](https://badge.fury.io/py/bml-connect-python.svg)](https://badge.fury.io/py/bml-connect-python)
[![Python Support](https://img.shields.io/pypi/pyversions/bml-connect-python.svg)](https://pypi.org/project/bml-connect-python/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[![ViewCount](https://views.whatilearened.today/views/github/quillfires/bml-connect-python.svg)](https://views.whatilearened.today/views/github/quillfires/bml-connect-python.svg) [![GitHub forks](https://img.shields.io/github/forks/quillfires/bml-connect-python)](https://github.com/quillfires/bml-connect-python/network) [![GitHub stars](https://img.shields.io/github/stars/quillfires/bml-connect-python.svg?color=ffd40c)](https://github.com/quillfires/bml-connect-python/stargazers) [![PyPI - Downloads](https://img.shields.io/pypi/dm/bml-connect-python?color=orange&label=PIP%20Installs)](https://pypi.python.org/pypi/bml-connect-python/) [![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/quillfires/bml-connect-python/issues) [![GitHub issues](https://img.shields.io/github/issues/quillfires/bml-connect-python.svg?color=808080)](https://github.com/quillfires/bml-connect-python/issues)

Python SDK for Bank of Maldives Connect API with synchronous and asynchronous support.  
Compatible with all Python frameworks including Django, Flask, FastAPI, and Sanic.

## Features

- **🔄 Sync/Async Support**: Choose your preferred programming style
- **🎯 Full API Coverage**: Create, retrieve, cancel transactions; webhook signature verification
- **📝 Type Annotations**: Full type hint support for better development experience
- **🛡️ Error Handling**: Comprehensive error hierarchy for easy debugging
- **🚀 Framework Agnostic**: Works with any Python web framework
- **🔒 Context Manager Support**: Automatic resource cleanup with `with`/`async with`
- **📄 MIT Licensed**: Open source and free to use

## Installation

```bash
pip install bml-connect-python
```

## Quick Start

### Synchronous Usage

```python
from bml_connect import BMLConnect, Environment

# Use as a context manager for automatic cleanup
with BMLConnect(
    api_key="your_api_key",
    app_id="your_app_id",
    environment=Environment.SANDBOX
) as client:
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
```

### Asynchronous Usage

```python
import asyncio
from bml_connect import BMLConnect, Environment

async def main():
    async with BMLConnect(
        api_key="your_api_key",
        app_id="your_app_id",
        environment=Environment.SANDBOX,
        async_mode=True
    ) as client:
        transaction = await client.transactions.create_transaction({
            "amount": 2000,
            "currency": "MVR",
            "provider": "wechat",
            "redirectUrl": "https://yourstore.com/success"
        })
        print(f"Transaction ID: {transaction.transaction_id}")

asyncio.run(main())
```

## Framework Integration Examples

### Flask Integration

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

### FastAPI Integration

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

### Sanic Integration

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

## API Reference

### `BMLConnect(api_key, app_id, environment, async_mode, timeout)`

Main entry point for the SDK.

| Parameter     | Type                   | Default      | Description                                       |
| ------------- | ---------------------- | ------------ | ------------------------------------------------- |
| `api_key`     | `str`                  | required     | Your API key from the BML merchant portal         |
| `app_id`      | `str`                  | required     | Your application ID from the BML merchant portal  |
| `environment` | `Environment` or `str` | `PRODUCTION` | `Environment.SANDBOX` or `Environment.PRODUCTION` |
| `async_mode`  | `bool`                 | `False`      | Set `True` to use async methods                   |
| `timeout`     | `int`                  | `30`         | Request timeout in seconds                        |

### Transaction Methods

| Method                     | Sync | Async | Description                             |
| -------------------------- | ---- | ----- | --------------------------------------- |
| `create_transaction(data)` | ✅   | ✅    | Create a new payment transaction        |
| `get_transaction(id)`      | ✅   | ✅    | Retrieve a transaction by ID            |
| `cancel_transaction(id)`   | ✅   | ✅    | Cancel a transaction by ID              |
| `list_transactions(...)`   | ✅   | ✅    | List transactions with optional filters |

### `list_transactions` Parameters

```python
client.transactions.list_transactions(
    page=1,
    per_page=20,
    state="CONFIRMED",       # Filter by TransactionState value
    provider="alipay",       # Filter by provider
    start_date="2026-01-01", # Filter from date
    end_date="2026-02-01",   # Filter to date
)
```

### Core Classes

- **`BMLConnect`**: Main entry point for the SDK
- **`Transaction`**: Typed transaction object returned by all transaction methods
- **`QRCode`**: QR code details attached to a transaction
- **`PaginatedResponse`**: Wraps paginated transaction list results
- **`Environment`**: `SANDBOX` or `PRODUCTION`
- **`SignMethod`**: `SHA1` (default) or `MD5`
- **`TransactionState`**: `CREATED`, `QR_CODE_GENERATED`, `CONFIRMED`, `CANCELLED`, `FAILED`, `EXPIRED`, `REFUND_REQUESTED`, `REFUNDED`

### Exception Hierarchy

```
BMLConnectError
├── AuthenticationError   (401)
├── ValidationError       (400)
├── NotFoundError         (404)
├── ServerError           (5xx)
└── RateLimitError        (429)
```

### Signature Utilities

```python
from bml_connect import SignatureUtils

# Generate a signature manually
signature = SignatureUtils.generate_signature(data, api_key, method)

# Verify a signature with constant-time comparison
is_valid = SignatureUtils.verify_signature(data, signature, api_key, method)
```

## Advanced Usage

### Transaction Management

```python
with BMLConnect(api_key="your_api_key", app_id="your_app_id") as client:
    # Create
    transaction = client.transactions.create_transaction({
        "amount": 5000,
        "currency": "MVR",
        "provider": "alipay",
        "redirectUrl": "https://yourstore.com/success",
        "localId": "order_456"
    })

    # Retrieve
    details = client.transactions.get_transaction(transaction.transaction_id)
    print(f"State: {details.state}")

    # Cancel
    cancelled = client.transactions.cancel_transaction(transaction.transaction_id)

    # List with filters
    results = client.transactions.list_transactions(
        page=1,
        per_page=10,
        state="CONFIRMED"
    )
    for t in results.items:
        print(t.transaction_id, t.amount, t.state)
```

### Webhook Handling

```python
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    payload = request.get_json()

    if not client.verify_webhook_signature(payload, payload.get('signature')):
        return {"error": "Invalid signature"}, 403

    state = payload.get('state')
    if state == 'CONFIRMED':
        pass  # fulfil the order
    elif state == 'REFUND_REQUESTED':
        pass  # initiate refund flow
    elif state == 'REFUNDED':
        pass  # mark order as refunded

    return {"status": "success"}
```

### Custom Timeout

```python
# For slow network environments or large payloads
client = BMLConnect(
    api_key="your_api_key",
    app_id="your_app_id",
    timeout=60
)
```

## Requirements

- Python 3.9+
- `requests`
- `aiohttp`

## Development

### Setup

```bash
git clone https://github.com/quillfires/bml-connect-python.git
cd bml-connect-python
pip install -e .[dev]
```

### Running Tests

```bash
pytest
```

### Code Quality

```bash
black .
flake8 .
mypy .
```

## Project Structure

```
bml-connect-python/
├── src/bml_connect/          # Source code
├── tests/                    # Test files
├── examples/                 # Usage examples
├── pyproject.toml           # Build configuration
├── requirements.txt         # Runtime dependencies
├── requirements-dev.txt     # Development dependencies
└── README.md               # This file
```

## Contributing

Contributions are welcome. Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License — see [LICENSE](LICENSE) for details.

## Support

- 📖 [Documentation](https://github.com/quillfires/bml-connect-python/wiki)
- 🐛 [Issue Tracker](https://github.com/quillfires/bml-connect-python/issues)
- 💬 [Discussions](https://github.com/quillfires/bml-connect-python/discussions)

## Changelog

See [CHANGELOG.md](https://github.com/quillfires/bml-connect-python/blob/main/CHANGELOG.md) for a full history of changes.

## Security

If you discover a security issue, please email fayaz.quill@gmail.com instead of opening a public issue.

---

Made with ❤️ for the Maldivian developer community

