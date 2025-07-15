# BML Connect Python SDK

[![PyPI version](https://badge.fury.io/py/bml-connect-python.svg)](https://badge.fury.io/py/bml-connect-python)
[![Python Support](https://img.shields.io/pypi/pyversions/bml-connect-python.svg)](https://pypi.org/project/bml-connect-python/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


[![ViewCount](https://views.whatilearened.today/views/github/quillfires/bml-connect-python.svg)](https://views.whatilearened.today/views/github/quillfires/bml-connect-python.svg)  [![GitHub forks](https://img.shields.io/github/forks/quillfires/bml-connect-python)](https://github.com/quillfires/bml-connect-python/network)  [![GitHub stars](https://img.shields.io/github/stars/quillfires/bml-connect-python.svg?color=ffd40c)](https://github.com/quillfires/bml-connect-python/stargazers)  [![PyPI - Downloads](https://img.shields.io/pypi/dm/bml-connect-python?color=orange&label=PIP%20-%20Installs)](https://pypi.python.org/pypi/bml-connect-python/) [![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/quillfires/bml-connect-python/issues)  [![GitHub issues](https://img.shields.io/github/issues/quillfires/bml-connect-python.svg?color=808080)](https://github.com/quillfires/bml-connect-python/issues) 

Python SDK for Bank of Maldives Connect API with synchronous and asynchronous support.  
Compatible with all Python frameworks including Django, Flask, FastAPI, and Sanic.

## Features

- **🔄 Sync/Async Support**: Choose your preferred programming style
- **🎯 Full API Coverage**: Transactions, webhooks, and signature verification
- **📝 Type Annotations**: Full type hint support for better development experience
- **🛡️ Error Handling**: Comprehensive error hierarchy for easy debugging
- **🚀 Framework Agnostic**: Works with any Python web framework
- **📄 MIT Licensed**: Open source and free to use

## Installation

```bash
pip install bml-connect-python
```

## Quick Start

### Synchronous Usage

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

### Asynchronous Usage

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

### Core Classes

- **`BMLConnect`**: Main entry point for the SDK
- **`Transaction`**: Transaction object with all transaction details
- **`QRCode`**: QR code details for payment processing
- **`PaginatedResponse`**: For paginated transaction lists
- **`Environment`**: Enum for `SANDBOX` and `PRODUCTION` environments
- **`SignMethod`**: Enum for signature methods
- **`TransactionState`**: Enum for transaction states

### Exception Hierarchy

```
BMLConnectError
├── AuthenticationError
├── ValidationError
├── NotFoundError
├── ServerError
└── RateLimitError
```

### Signature Utilities

```python
from bml_connect import SignatureUtils

# Generate signature
signature = SignatureUtils.generate_signature(data, api_key, method)

# Verify signature
is_valid = SignatureUtils.verify_signature(data, signature, api_key, method)
```

## Advanced Usage

### Transaction Management

```python
# Create a transaction
transaction = client.transactions.create_transaction({
    "amount": 5000,
    "currency": "MVR",
    "provider": "alipay",
    "redirectUrl": "https://yourstore.com/success",
    "localId": "order_456"
})

# Get transaction details
details = client.transactions.get_transaction(transaction.transaction_id)

# List transactions with pagination
transactions = client.transactions.list_transactions(
    page=1,
    per_page=10,
    status="completed"
)
```

### Webhook Handling

```python
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    payload = request.get_json()
    
    # Verify webhook signature
    if not client.verify_webhook_signature(payload, payload.get('signature')):
        return {"error": "Invalid signature"}, 403
    
    # Process different webhook events
    event_type = payload.get('event_type')
    if event_type == 'transaction.completed':
        # Handle completed transaction
        transaction_id = payload.get('transaction_id')
        # Your business logic here
    elif event_type == 'transaction.failed':
        # Handle failed transaction
        pass
    
    return {"status": "success"}
```

## Requirements

- Python 3.7+
- See `requirements.txt` and `requirements-dev.txt` for dependencies

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/quillfires/bml-connect-python.git
cd bml-connect-python

# Install in development mode
pip install -e .[dev]
```

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
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

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📖 [Documentation](https://github.com/quillfires/bml-connect-python/wiki)
- 🐛 [Issue Tracker](https://github.com/quillfires/bml-connect-python/issues)
- 💬 [Discussions](https://github.com/quillfires/bml-connect-python/discussions)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

## Security

If you discover any security-related issues, please email fayaz.quill@gmail.com instead of using the issue tracker.

---

Made with ❤️ for the Maldivian developer community