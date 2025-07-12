# Advanced Usage

## Pagination

The `list_transactions` method returns a `PaginatedResponse` object:

```python
page = client.transactions.list_transactions(
    page=2,
    per_page=10,
    state="CONFIRMED"
)

print(f"Page {page.current_page} of {page.total_pages}")
print(f"Total transactions: {page.count}")

for transaction in page.items:
    print(f"{transaction.transaction_id}: {transaction.amount}")
```

## Custom Signing Methods

You can specify different signing methods when creating transactions:

```py
transaction = client.transactions.create_transaction({
    "amount": 1500,
    "currency": "MVR",
    "signMethod": "md5",  # Use MD5 instead of default SHA1
    # ... other fields
})
```

## Error Handling

Handle specific error types:

```py
try:
    transaction = client.transactions.get_transaction("invalid_id")
except NotFoundError:
    print("Transaction not found")
except AuthenticationError:
    print("Invalid API credentials")
except RateLimitError:
    print("API rate limit exceeded - try again later")
except BMLConnectError as e:
    print(f"BML Error: {e}")
```

## Framework Integration

### Django Middleware

```py
# middleware.py
from django.http import JsonResponse
from bml_connect import BMLConnect

class BMLWebhookMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.client = BMLConnect(api_key="your_key", app_id="your_app_id")

    def __call__(self, request):
        if request.path == '/webhook':
            return self.handle_webhook(request)
        return self.get_response(request)

    def handle_webhook(self, request):
        try:
            payload = json.loads(request.body)
            signature = payload.get('signature')

            if not signature:
                return JsonResponse({"error": "Missing signature"}, status=400)

            if self.client.verify_webhook_signature(payload, signature):
                # Process webhook
                return JsonResponse({"status": "success"})
            else:
                return JsonResponse({"error": "Invalid signature"}, status=403)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
```
