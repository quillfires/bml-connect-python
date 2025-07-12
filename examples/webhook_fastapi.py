"""
FastAPI Webhook Handler Example
===============================

This example shows how to handle BML Connect webhooks with FastAPI.
"""

from fastapi import FastAPI, Request, HTTPException
from bml_connect import BMLConnect
import uvicorn

app = FastAPI(title="BML Connect Webhook Handler")
client = BMLConnect(api_key="your_api_key_here", app_id="your_app_id_here")

@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        payload = await request.json()
        signature = payload.get("signature")
        
        if not signature:
            raise HTTPException(400, "Missing signature header")
        
        if client.verify_webhook_signature(payload, signature):
            # Process verified webhook
            transaction_id = payload.get("transactionId")
            status = payload.get("status")
            amount = payload.get("amount", 0) / 100
            currency = payload.get("currency", "MVR")
            
            print(f"Received webhook for transaction {transaction_id}")
            print(f"Status: {status}, Amount: {amount:.2f} {currency}")
            
            # Add your business logic here (update database, send notification, etc.)
            
            return {"status": "success"}
        else:
            raise HTTPException(403, "Invalid signature")
    except Exception as e:
        raise HTTPException(400, str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)