"""
Basic Synchronous Usage Example
================================

Demonstrates the V2 BML Connect SDK using the context-manager pattern.
"""

from bml_connect import BMLConnect, Environment

# ---------------------------------------------------------------------------
# Initialise
# ---------------------------------------------------------------------------
client = BMLConnect(api_key="your_api_key_here", environment=Environment.SANDBOX)

with client:
    # -----------------------------------------------------------------------
    # 1. Register a webhook URL so BML notifies you of transaction updates
    # -----------------------------------------------------------------------
    hook = client.webhooks.create("https://yourapp.com/bml-webhook")
    print(f"Webhook registered: {hook.id} → {hook.hook_url}")

    # -----------------------------------------------------------------------
    # 2. Create a V2 transaction (no signature required)
    # -----------------------------------------------------------------------
    txn = client.transactions.create(
        {
            "redirectUrl": "https://yourapp.com/thanks",
            "localId": "INV-001",
            "customerReference": "Order #42",
            "order": {
                "shopId": "YOUR_SHOP_ID",
                "products": [
                    {"productId": "YOUR_PRODUCT_ID", "numberOfItems": 2},
                ],
            },
        }
    )

    print(f"\nTransaction created!")
    print(f"  ID        : {txn.id}")
    print(f"  Amount    : {txn.amount} {txn.currency}")
    print(f"  State     : {txn.state.value if txn.state else 'N/A'}")
    print(f"  Pay URL   : {txn.url}")
    print(f"  Short URL : {txn.short_url}")

    # -----------------------------------------------------------------------
    # 3. Share the payment link with the customer
    # -----------------------------------------------------------------------
    updated_sms = client.transactions.send_sms(txn.id, "9609601234")
    print(f"\nSMS sent. Last shared: {updated_sms.last_shared}")

    updated_email = client.transactions.send_email(txn.id, "customer@example.com")
    print(f"Email sent. Last shared: {updated_email.last_shared}")

    # -----------------------------------------------------------------------
    # 4. Retrieve and update a transaction
    # -----------------------------------------------------------------------
    fetched = client.transactions.get(txn.id)
    print(f"\nFetched state: {fetched.state.value if fetched.state else 'N/A'}")

    patched = client.transactions.update(
        txn.id,
        customer_reference="Booking #99",
        local_data='{"reservationId": "RES-001"}',
        pnr="ABC123",
    )
    print(f"Updated customer_reference: {patched.customer_reference}")

    # -----------------------------------------------------------------------
    # 5. Shop management
    # -----------------------------------------------------------------------
    shops = client.shops.list()
    print(f"\nShops: {[s.name for s in shops]}")

    # -----------------------------------------------------------------------
    # 6. Customer management
    # -----------------------------------------------------------------------
    customers = client.customers.list()
    print(f"Customers: {len(customers)}")

    # -----------------------------------------------------------------------
    # 7. Unregister webhook when no longer needed
    # -----------------------------------------------------------------------
    client.webhooks.delete("https://yourapp.com/bml-webhook")
    print("\nWebhook removed.")