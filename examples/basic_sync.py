"""
Basic Synchronous Usage Example
================================

Demonstrates all four BML Connect integration methods using the sync client.

Set your keys before running:
    export BML_API_KEY=sk_...
    export BML_PUBLIC_KEY=pk_...
    export BML_SHOP_ID=...
    export BML_COMPANY_ID=...
"""

import os

from bml_connect import (
    BMLConnect,
    CardEncryption,
    Environment,
    Provider,
    TransactionState,
    WebhookEvent,
    WebhookEventType,
)

API_KEY     = os.environ.get("BML_API_KEY", "sk_your_private_key")
PUBLIC_KEY  = os.environ.get("BML_PUBLIC_KEY", "pk_your_public_key")
SHOP_ID     = os.environ.get("BML_SHOP_ID", "your_shop_id")
COMPANY_ID  = os.environ.get("BML_COMPANY_ID", "your_company_id")
WEBHOOK_URL = os.environ.get("BML_WEBHOOK_URL", "https://yourapp.com/bml-webhook")

with BMLConnect(
    api_key=API_KEY,
    public_key=PUBLIC_KEY,
    environment=Environment.SANDBOX,
) as client:

    # -----------------------------------------------------------------------
    # Register webhook
    # -----------------------------------------------------------------------
    hook = client.webhooks.create(WEBHOOK_URL)
    print(f"Webhook registered: {hook.id} - {hook.hook_url}")

    # -----------------------------------------------------------------------
    # Method 1: Redirect Method
    # Redirect customer to BML-hosted payment page
    # -----------------------------------------------------------------------
    print("\n--- Redirect Method ---")
    txn = client.transactions.create({
        "redirectUrl": "https://yourapp.com/payment-complete",
        "localId": "INV-001",
        "customerReference": "Order #42",
        "webhook": WEBHOOK_URL,
        "locale": "en",
        "order": {
            "shopId": SHOP_ID,
            "products": [{"productId": "YOUR_PRODUCT_ID", "numberOfItems": 2}],
        },
        "paymentPortalExperience": {
            "skipCustomerForm": False,
            "skipProviderSelection": False,
        },
    })
    print(f"  ID        : {txn.id}")
    print(f"  State     : {txn.state.value if txn.state else 'N/A'}")
    print(f"  URL       : {txn.url}")
    print(f"  Short URL : {txn.short_url}")

    # Share the link
    client.transactions.send_sms(txn.id, "9609601234")
    client.transactions.send_email(txn.id, "customer@example.com")
    print("  SMS and email sent.")

    # Update mutable fields
    client.transactions.update(
        txn.id,
        customer_reference="Booking #42",
        local_data='{"reservationId": "RES-001"}',
        pnr="ABC123",
    )

    # Always confirm state via API after redirect callback
    fetched = client.transactions.get(txn.id)
    print(f"  Confirmed state: {fetched.state.value if fetched.state else 'N/A'}")

    # -----------------------------------------------------------------------
    # Method 2: Direct Method - QR provider
    # Generate a QR code to display in-store
    # -----------------------------------------------------------------------
    print("\n--- Direct Method (QR provider: alipay) ---")
    qr_txn = client.transactions.create({
        "amount": 1000,
        "currency": "USD",
        "provider": Provider.ALIPAY.value,
        "webhook": WEBHOOK_URL,
        "locale": "en",
    })
    print(f"  ID           : {qr_txn.id}")
    print(f"  vendor_qr_code: {qr_txn.vendor_qr_code[:40]}..." if qr_txn.vendor_qr_code else "  No QR code returned")
    # Encode qr_txn.vendor_qr_code into a QR image and display to customer
    # e.g. qrcode.make(qr_txn.vendor_qr_code).save("payment.png")

    # -----------------------------------------------------------------------
    # Method 2: Direct Method - card provider
    # Redirect customer to secure card form
    # -----------------------------------------------------------------------
    print("\n--- Direct Method (card provider: mpgs) ---")
    card_txn = client.transactions.create({
        "amount": 2500,
        "currency": "USD",
        "provider": Provider.MPGS.value,
        "redirectUrl": "https://yourapp.com/payment-complete",
        "webhook": WEBHOOK_URL,
        "customer": {
            "name": "Alice Smith",
            "email": "alice@example.com",
            "billingAddress1": "1 Coral Way",
            "billingCity": "Male",
            "billingCountry": "MV",
        },
        "paymentPortalExperience": {
            "skipCustomerForm": True,
            "skipProviderSelection": True,
        },
    })
    print(f"  ID  : {card_txn.id}")
    print(f"  URL : {card_txn.url}")
    # Redirect customer to card_txn.url

    # -----------------------------------------------------------------------
    # Method 3: Card-On-File / Tokenization
    # Capture card on first transaction, charge silently later
    # -----------------------------------------------------------------------
    print("\n--- Card-On-File / Tokenization ---")

    # 3a. Create customer + tokenisation transaction in one call
    tok_txn = client.transactions.create({
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
            "billingAddress1": "2 Palm Street",
            "billingCity": "Male",
            "billingCountry": "MV",
            "currency": "MVR",
        },
        "customerAsPayer": True,
        "webhook": WEBHOOK_URL,
        "redirectUrl": "https://yourapp.com/payment-complete",
    })
    print(f"  Tokenisation txn : {tok_txn.id}")
    print(f"  Customer ID      : {tok_txn.customer_id}")
    print(f"  URL              : {tok_txn.url}")
    # After customer pays, BML fires NOTIFY_TOKENISATION_STATUS webhook

    # 3b. List stored tokens (after card is captured)
    # tokens = client.customers.list_tokens(tok_txn.customer_id)
    # for t in tokens:
    #     print(f"  Token: {t.id}  {t.brand}  {t.padded_card_number}")

    # 3c. Charge stored token (subsequent payments, no customer interaction)
    # new_txn = client.transactions.create({"amount": 5000, "currency": "USD",
    #                                        "customerId": tok_txn.customer_id})
    # result = client.customers.charge({"customerId": tok_txn.customer_id,
    #                                    "transactionId": new_txn.id,
    #                                    "tokenId": tokens[0].id})
    # print(f"  Charge state: {result.state}")

    # -----------------------------------------------------------------------
    # Method 4: PCI Merchant Tokenization
    # Encrypt card server-side, submit for 3DS, then charge tokenId
    # -----------------------------------------------------------------------
    print("\n--- PCI Merchant Tokenization ---")
    if client.public_client:
        # Always fetch fresh - key can rotate
        enc_key = client.public_client.get_tokens_public_key()
        print(f"  Encryption key ID: {enc_key.key_id}")

        card_b64 = CardEncryption.encrypt(enc_key.pem, {
            "cardNumberRaw":   "4111111111111111",
            "cardVDRaw":       "123",
            "cardExpiryMonth": 12,
            "cardExpiryYear":  29,
        })
        print(f"  Encrypted card data (truncated): {card_b64[:40]}...")

        result = client.public_client.add_card(
            card_data=card_b64,
            key_id=enc_key.key_id,
            customer_id="YOUR_CUSTOMER_ID",
            redirect="https://yourapp.com/tokenisation-callback",
            webhook=WEBHOOK_URL,
        )
        print(f"  3DS redirect URL       : {result.next_action.url if result.next_action else 'N/A'}")
        print(f"  Client-side token ID   : {result.next_action.client_side_token_id if result.next_action else 'N/A'}")
        # Redirect customer to result.next_action.url for 3DS
        # On success callback: ?tokenId=<id>&status=TOKENISATION_SUCCESS
        # Use tokenId with client.customers.charge(...)
    else:
        print("  Skipped - public_key not provided")

    # -----------------------------------------------------------------------
    # Other resources
    # -----------------------------------------------------------------------
    print("\n--- Other Resources ---")

    shops = client.shops.list()
    print(f"  Shops: {[s.name for s in shops]}")

    customers = client.customers.list()
    print(f"  Customers: {len(customers)}")

    companies = client.company.get()
    for co in companies:
        print(f"  Company: {co.trading_name} - {co.enabled_currencies}")

    # -----------------------------------------------------------------------
    # Unregister webhook
    # -----------------------------------------------------------------------
    client.webhooks.delete(WEBHOOK_URL)
    print("\nWebhook removed. Done.")