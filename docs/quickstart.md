# BML Connect Python SDK - Quick Start

## Installation

```bash
pip install bml-connect-python
```

## Basic Usage

### Synchronous Client

```py
from bml_connect import BMLConnect, Environment

client = BMLConnect(
    api_key="your_api_key",
    app_id="your_app_id",
    environment=Environment.SANDBOX
)

transaction = client.transactions.create_transaction({
    "amount": 1500,  # 15.00 MVR
    "currency": "MVR",
    "provider": "alipay",
    "redirectUrl": "https://yourstore.com/success"
})
```

### Asynchronous Client

```py
import asyncio
from bml_connect import BMLConnect, Environment

async def main():
    client = BMLConnect(
        api_key="your_api_key",
        app_id="your_app_id",
        environment=Environment.SANDBOX,
        async_mode=True
    )

    transaction = await client.transactions.create_transaction({
        "amount": 2000,
        "currency": "MVR",
        "provider": "wechat",
        "redirectUrl": "https://yourstore.com/success"
    })

asyncio.run(main())
```

## Webhook Verification

```py
# Verify webhook signature
is_valid = client.verify_webhook_signature(
    payload=webhook_payload,
    signature=received_signature
)
```

## Error Handling

```py
try:
    transaction = client.transactions.create_transaction({...})
except ValidationError as e:
    print(f"Validation error: {e}")
except AuthenticationError:
    print("Invalid credentials")
except BMLConnectError as e:
    print(f"General error: {e}")
```
