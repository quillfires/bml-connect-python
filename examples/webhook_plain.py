from bml_connect import BMLConnect

client = BMLConnect(api_key="your_api_key", app_id="your_app_id")

def handle_webhook(payload: dict):
    signature = payload.get('signature')
    if not signature:
        return {"error": "Missing signature"}, 400
    if client.verify_webhook_signature(payload, signature):
        # Process webhook
        print(f"Received valid webhook: {payload}")
        return {"status": "success"}, 200
    else:
        return {"error": "Invalid signature"}, 403

# Example usage:
if __name__ == "__main__":
    # Simulate receiving a webhook payload
    payload = {
        "transactionId": "txn_123",
        "status": "CONFIRMED",
        "amount": 1500,
        "currency": "MVR",
        "signature": "..."  # Replace with actual signature
    }
    result, status = handle_webhook(payload)
    print(f"Result: {result}, Status: {status}")
