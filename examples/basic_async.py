"""
Basic Asynchronous Usage Example
==================================

Demonstrates the V2 BML Connect SDK using async/await.
"""

import asyncio

from bml_connect import BMLConnect, Environment


async def main() -> None:
    async with BMLConnect(
        api_key="your_api_key_here",
        environment=Environment.SANDBOX,
        async_mode=True,
    ) as client:

        # Register webhook
        hook = await client.webhooks.create("https://yourapp.com/bml-webhook")
        print(f"Webhook registered: {hook.id}")

        # Create V2 transaction
        txn = await client.transactions.create(
            {
                "redirectUrl": "https://yourapp.com/thanks",
                "localId": "INV-ASYNC-001",
                "order": {
                    "shopId": "YOUR_SHOP_ID",
                    "products": [{"productId": "PROD_ID", "numberOfItems": 1}],
                },
                # Optional: set an expiry date
                "expires": "2026-12-31T23:59:59.000Z",
            }
        )
        print(f"Created transaction {txn.id}: {txn.url}")

        # Share payment link
        await client.transactions.send_sms(txn.id, "9609601234")
        await client.transactions.send_email(txn.id, ["alice@example.com", "bob@example.com"])

        # Fetch details
        fetched = await client.transactions.get(txn.id)
        print(f"State: {fetched.state.value if fetched.state else 'N/A'}")

        # List shops and their products
        shops = await client.shops.list()
        for shop in shops:
            print(f"\nShop: {shop.name} ({shop.id})")
            products = await client.shops.list_products(shop.id)
            for p in products:
                print(f"  Product: {p.name} - {p.price} {p.currency}")

        # Customers
        customers = await client.customers.list()
        print(f"\n{len(customers)} customers on account.")

        # Cleanup
        await client.webhooks.delete("https://yourapp.com/bml-webhook")


if __name__ == "__main__":
    asyncio.run(main())