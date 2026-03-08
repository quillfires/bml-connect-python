"""
Card-On-File (Tokenization) Example
=====================================

Demonstrates the full Card-On-File workflow:

1. Create a customer (or reuse an existing one)
2. Create a transaction with tokenizationDetails to capture the card
3. Customer completes first payment → BML stores card → sends webhook
4. On subsequent charges: create transaction → charge stored token

Only ``mpgs`` and ``debit_credit_card`` providers support tokenisation.

Run:
    BML_API_KEY=your_key python card_on_file.py
"""

import os
import time

from bml_connect import BMLConnect, Environment, TransactionState, WebhookEvent, WebhookEventType

API_KEY     = os.environ.get("BML_API_KEY", "your_api_key")
WEBHOOK_URL = os.environ.get("BML_WEBHOOK_URL", "https://yourapp.com/bml-webhook")

client = BMLConnect(api_key=API_KEY, environment=Environment.SANDBOX)


# ---------------------------------------------------------------------------
# Step 1: Create a customer (skip if customerId already exists)
# ---------------------------------------------------------------------------

def create_customer() -> str:
    customer = client.customers.create({
        "name": "Alice Smith",
        "email": "alice@example.com",
        "billingEmail": "alice@example.com",
        "billingAddress1": "1 Coral Way",
        "billingCity": "Malé",
        "billingCountry": "MV",
        "billingPostCode": "20026",
        "currency": "MVR",
        "companyId": os.environ.get("BML_COMPANY_ID", "your_company_id"),
    })
    print(f"Customer created: {customer.id}")
    return customer.id


# ---------------------------------------------------------------------------
# Step 2a: Create a tokenization transaction with existing customer
# ---------------------------------------------------------------------------

def create_tokenisation_transaction(customer_id: str) -> str:
    txn = client.transactions.create({
        "amount": 100,          # 1.00 USD - initial charge to capture card
        "currency": "USD",
        "tokenizationDetails": {
            "tokenize": True,
            "paymentType": "UNSCHEDULED",
            "recurringFrequency": "UNSCHEDULED",
        },
        "customerId": customer_id,
        "customerAsPayer": True,
        "webhook": WEBHOOK_URL,
        "redirectUrl": "https://yourapp.com/payment-complete",
    })

    print(f"Tokenisation transaction created: {txn.id}")
    print(f"State: {txn.state}")
    print(f"Payment URL: {txn.url}")
    print(f"Short URL:   {txn.short_url}")
    return txn.id


# ---------------------------------------------------------------------------
# Step 2b: Create customer AND transaction in one call
# ---------------------------------------------------------------------------

def create_customer_and_tokenisation_transaction() -> str:
    txn = client.transactions.create({
        "amount": 100,
        "currency": "USD",
        "tokenizationDetails": {
            "tokenize": True,
            "paymentType": "UNSCHEDULED",
            "recurringFrequency": "UNSCHEDULED",
        },
        "customer": {
            "name": "Bob Jones",
            "email": "bob@example.com",
            "billingEmail": "bob@example.com",
            "billingAddress1": "2 Palm Street",
            "billingCity": "Malé",
            "billingCountry": "MV",
            "currency": "MVR",
        },
        "customerAsPayer": True,
        "webhook": WEBHOOK_URL,
        "redirectUrl": "https://yourapp.com/payment-complete",
    })

    print(f"Transaction + Customer created: {txn.id}")
    print(f"Customer ID: {txn.customer_id}")
    print(f"Payment URL: {txn.url}")
    return txn.id


# ---------------------------------------------------------------------------
# Step 3: Wait for tokenisation (polling - in production use webhooks instead)
# ---------------------------------------------------------------------------

def wait_for_tokenisation(txn_id: str, max_seconds: int = 120) -> bool:
    """Poll transaction state until CONFIRMED or terminal state."""
    print(f"\nPolling transaction {txn_id}...")
    deadline = time.time() + max_seconds
    while time.time() < deadline:
        txn = client.transactions.get(txn_id)
        print(f"  state={txn.state}")
        if txn.state == TransactionState.CONFIRMED:
            print("Payment confirmed - card should be tokenised.")
            return True
        if txn.state in (TransactionState.CANCELLED, TransactionState.FAILED, TransactionState.EXPIRED):
            print(f"Terminal state reached: {txn.state}")
            return False
        time.sleep(5)
    print("Polling timed out.")
    return False


# ---------------------------------------------------------------------------
# Step 4: List tokens for the customer
# ---------------------------------------------------------------------------

def list_tokens(customer_id: str):
    tokens = client.customers.list_tokens(customer_id)
    print(f"\nTokens for customer {customer_id}:")
    for t in tokens:
        print(f"  id={t.id}  brand={t.brand}  card={t.padded_card_number}"
              f"  exp={t.token_expiry_month}/{t.token_expiry_year}"
              f"  default={t.default_token}")
    return tokens


# ---------------------------------------------------------------------------
# Step 5: Charge a stored token (three options)
# ---------------------------------------------------------------------------

def charge_token(customer_id: str, token_id: str = None, token: str = None) -> None:
    """Create a new transaction for the amount then charge the stored token."""

    # Create the transaction shell first
    txn = client.transactions.create({
        "amount": 5320,          # 53.20 USD recurring charge
        "currency": "USD",
        "customerId": customer_id,
    })
    print(f"\nCharge transaction created: {txn.id}")

    # Build charge payload - three options:
    charge_payload = {
        "customerId": customer_id,
        "transactionId": txn.id,
    }
    if token_id:
        charge_payload["tokenId"] = token_id          # Option 1: by token ID
    elif token:
        charge_payload["token"] = token               # Option 2: by raw token string
    # else: Option 3 - no token specified → default token is used

    result = client.customers.charge(charge_payload)
    print(f"Charge result state: {result.state}")

    # Always confirm via API query (don't rely solely on charge response)
    confirmed_txn = client.transactions.get(txn.id)
    print(f"Confirmed state via API query: {confirmed_txn.state}")


# ---------------------------------------------------------------------------
# Webhook handler example - parsing Card-On-File webhook events
# ---------------------------------------------------------------------------

def handle_webhook_event(raw_payload: dict) -> None:
    """Parse and handle a Card-On-File webhook notification.

    Verify the signature before calling this - see webhook_flask.py.
    """
    event = WebhookEvent.from_dict(raw_payload)

    if event.event_type == WebhookEventType.NOTIFY_TOKENISATION_STATUS:
        print(f"Tokenisation event: status={event.tokenisation_status} "
              f"customer={event.customer_id} txn={event.transaction_id}")
        if event.tokenisation_status and event.tokenisation_status.value == "TOKENISATION_SUCCESS":
            # Card stored - safe to charge in future
            tokens = client.customers.list_tokens(event.customer_id)
            print(f"  {len(tokens)} token(s) now on file for customer {event.customer_id}")

    elif event.event_type == WebhookEventType.NOTIFY_TRANSACTION_CHANGE:
        print(f"Transaction change: txn={event.transaction_id} state={event.state} "
              f"amount={event.amount_formatted}")


# ---------------------------------------------------------------------------
# Main - run the full workflow
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # --- Workflow A: existing customer ---
    print("=== Workflow A: Existing Customer ===")
    customer_id = create_customer()
    txn_id = create_tokenisation_transaction(customer_id)
    print(f"\nRedirect customer to payment URL to complete first charge.")
    print(f"After payment, BML sends NOTIFY_TOKENISATION_STATUS webhook.")
    print(f"Then charge_token(customer_id, token_id=tokens[0].id)")

    # --- Workflow B: new customer inline ---
    print("\n=== Workflow B: New Customer Inline ===")
    txn_id_b = create_customer_and_tokenisation_transaction()
    print(f"\nCustomer created during transaction - customer_id is in txn.customer_id")

    # After card is captured, demonstrate charging (commented - needs real IDs):
    # tokens = list_tokens(customer_id)
    # charge_token(customer_id, token_id=tokens[0].id)   # Option 1
    # charge_token(customer_id, token=tokens[0].token)   # Option 2
    # charge_token(customer_id)                          # Option 3 - default token

    client.close()