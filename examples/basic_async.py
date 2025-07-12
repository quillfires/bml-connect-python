"""
Basic Asynchronous Usage Example
===============================

This example shows how to use the BML Connect SDK in asynchronous mode.
"""

import asyncio
from bml_connect import BMLConnect, Environment

async def main():
    # Initialize async client
    client = BMLConnect(
        api_key="your_api_key_here",
        app_id="your_app_id_here",
        environment=Environment.SANDBOX,
        async_mode=True
    )
    
    try:
        # Create a transaction
        transaction = await client.transactions.create_transaction({
            "amount": 2000,  # 20.00 MVR
            "currency": "MVR",
            "provider": "wechat",
            "redirectUrl": "https://yourstore.com/success"
        })
        
        print(f"Created transaction: {transaction.transaction_id}")
        print(f"QR Code URL: {transaction.qr_code.url if transaction.qr_code else 'N/A'}")
        
        # Get transaction details
        details = await client.transactions.get_transaction(transaction.transaction_id)
        print(f"Current status: {details.state.value if details.state else 'N/A'}")
        
        # List transactions with filters
        print("\nListing confirmed transactions...")
        transactions = await client.transactions.list_transactions(
            page=1,
            per_page=5,
            state="CONFIRMED"
        )
        print(f"Found {transactions.count} confirmed transactions")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        # Clean up async resources
        await client.aclose()

if __name__ == "__main__":
    asyncio.run(main())