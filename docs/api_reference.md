# API Reference

## BMLConnect Class

The main client class for interacting with the BML Connect API.

### Parameters

- `api_key` (str): Your API key from BML merchant portal
- `app_id` (str): Your application ID from BML merchant portal
- `environment` (Environment): API environment (SANDBOX or PRODUCTION)
- `async_mode` (bool): Whether to use async operations (default: False)

### Properties

- `transactions`: Access to transaction operations

### Methods

- `verify_webhook_signature(payload, signature, method=SignMethod.SHA1)`: Verify webhook signature
- `close()`: Clean up resources (synchronous)
- `aclose()`: Clean up resources (asynchronous)

## Transaction Operations

### create_transaction(data)

Create a new payment transaction

**Parameters:**

- `data` (dict): Transaction data including:
  - `amount` (int): Amount in cents (e.g., 1500 = 15.00 MVR)
  - `currency` (str): Currency code (e.g., "MVR")
  - `provider` (str): Payment provider ("alipay" or "wechat")
  - `redirectUrl` (str): Redirect URL after payment
  - `localId` (str, optional): Your internal ID
  - `customerReference` (str, optional): Customer reference

**Returns:** `Transaction` object

### get_transaction(transaction_id)

Retrieve a transaction by ID

**Parameters:**

- `transaction_id` (str): BML transaction ID

**Returns:** `Transaction` object

### list_transactions(page=1, per_page=20, \*\*filters)

List transactions with pagination

**Parameters:**

- `page` (int): Page number
- `per_page` (int): Items per page
- `filters`: Optional filters:
  - `state` (str): Transaction state
  - `provider` (str): Payment provider
  - `start_date` (str): Start date (YYYY-MM-DD)
  - `end_date` (str): End date (YYYY-MM-DD)

**Returns:** `PaginatedResponse` object
