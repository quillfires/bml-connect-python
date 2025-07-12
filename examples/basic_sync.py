"""
Basic Synchronous Usage Example
===============================

This example shows how to use the BML Connect SDK in synchronous mode.
"""

from bml_connect import BMLConnect, Environment

# Initialize client
client = BMLConnect(
    api_key="your_api_key_here",
    app_id="your_app_id_here",
    environment=Environment.SANDBOX
)

try:
    # Create a transaction
    transaction = client.transactions.create_transaction({
        "amount": 1500,  # 15.00 MVR
        "currency": "MVR",
        "provider": "alipay",
        "redirectUrl": "https://yourstore.com/success",
        "localId": "order_12345",
        "customerReference": "Customer #789"
    })
    
    print("Transaction created successfully!")
    print(f"ID: {transaction.transaction_id}")
    print(f"Amount: {transaction.amount / 100:.2f} {transaction.currency}")
    print(f"Status: {transaction.state.value if transaction.state else 'N/A'}")
    print(f"Payment URL: {transaction.url}")
    
    # Retrieve the same transaction
    print("\nFetching transaction details...")
    fetched = client.transactions.get_transaction(transaction.transaction_id)
    print(f"Fetched status: {fetched.state.value if fetched.state else 'N/A'}")
    
    # List recent transactions
    print("\nListing recent transactions...")
    transactions = client.transactions.list_transactions(page=1, per_page=3)
    print(f"Found {transactions.count} transactions (showing first 3):")
    for txn in transactions.items:
        print(f"- {txn.transaction_id}: {txn.amount/100:.2f} {txn.currency} ({txn.state.value})")
        
except Exception as e:
    print(f"Error: {str(e)}")
finally:
    # Clean up resources
    client.close()