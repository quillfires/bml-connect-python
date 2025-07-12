# Handling Webhooks

## Webhook Structure

BML Connect will POST JSON payloads to your endpoint with the following structure:

```json
{
  "transactionId": "txn_12345",
  "amount": 1000,
  "currency": "MVR",
  "status": "CONFIRMED",
  "signature": "generated_signature"
}
```

### Verification Process

1. Extract the signature from the payload
2. Remove the signature field from the payload
3. Verify using your API key:

```py
is_valid = client.verify_webhook_signature(
    payload=payload_data,
    signature=received_signature
)
```
