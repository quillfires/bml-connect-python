# Testing Guide

## Sandbox Environment

Use the sandbox environment for testing:

```python
from bml_connect import Environment

client = BMLConnect(
    api_key="your_sandbox_api_key",
    app_id="your_sandbox_app_id",
    environment=Environment.SANDBOX
)
```

## Test Cards

Use these test values for payments:
|Provider|Test Account|Notes|
|:------:|:----------:|:---:|
|Alipay|Any account|Use any credentials|
|WeChat|Any account|Use any credentials|
|Credit Card|4111 1111 1111 1111|Any future expiry, any CVV|

## Simulating Webhooks

Use this script to simulate webhook notifications:

```py
import requests
import hashlib
import json

api_key = "your_api_key"
webhook_url = "https://yourdomain.com/webhook"

# Sample payload
payload = {
    "transactionId": "test_txn_123",
    "amount": 1000,
    "currency": "MVR",
    "status": "CONFIRMED",
    "timestamp": "2025-01-01T12:00:00Z"
}

# Generate signature
signature_string = urlencode(sorted(payload.items())) + f"&apiKey={api_key}"
signature = hashlib.sha1(signature_string.encode()).hexdigest()

payload["signature"] = signature

# Send webhook
response = requests.post(webhook_url, json=payload)
print(f"Webhook response: {response.status_code} - {response.text}")
```
