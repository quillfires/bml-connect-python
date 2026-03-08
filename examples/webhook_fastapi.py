"""
FastAPI Webhook Example
========================

Async-native FastAPI server that:
1. Registers its webhook endpoint with BML on startup.
2. Verifies incoming notifications using the current SHA-256 header scheme
   (X-Signature-Nonce, X-Signature-Timestamp, X-Signature).
3. Falls back to legacy ``originalSignature`` verification for old v1 payloads.
4. Unregisters the webhook on shutdown.

Run:
    pip install fastapi uvicorn bml-connect-python
    BML_API_KEY=your_key uvicorn webhook_fastapi:app --port 8000
"""

import json
import os

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from bml_connect import BMLConnect, Environment

API_KEY     = os.environ.get("BML_API_KEY", "your_api_key_here")
WEBHOOK_URL = os.environ.get("BML_WEBHOOK_URL", "https://yourapp.com/bml-webhook")

app    = FastAPI()
client = BMLConnect(api_key=API_KEY, environment=Environment.PRODUCTION, async_mode=True)


@app.on_event("startup")
async def register_webhook() -> None:
    try:
        hook = await client.webhooks.create(WEBHOOK_URL)
        print(f"BML webhook registered: {hook.id}")
    except Exception as exc:
        print(f"Warning: could not register webhook (already exists?): {exc}")


@app.on_event("shutdown")
async def unregister_webhook() -> None:
    try:
        await client.webhooks.delete(WEBHOOK_URL)
        print("BML webhook unregistered.")
    except Exception:
        pass
    await client.aclose()


@app.post("/bml-webhook")
async def bml_webhook(
    request: Request,
    x_signature_nonce: str     = Header(default=""),
    x_signature_timestamp: str = Header(default=""),
    x_signature: str           = Header(default=""),
) -> JSONResponse:
    """Receive and verify BML transaction update notifications."""

    if x_signature_nonce and x_signature_timestamp and x_signature:
        # Current SHA-256 header verification
        if not client.verify_webhook_signature(
            x_signature_nonce, x_signature_timestamp, x_signature
        ):
            raise HTTPException(status_code=403, detail="Invalid signature")
    else:
        # Legacy originalSignature fallback
        raw = await request.body()
        payload = json.loads(raw)
        original_sig = payload.get("originalSignature")
        if not original_sig:
            raise HTTPException(status_code=400, detail="Missing signature headers")
        if not client.verify_legacy_webhook_signature(payload, original_sig):
            raise HTTPException(status_code=403, detail="Invalid legacy signature")

    payload = await request.json()
    txn_id = payload.get("id") or payload.get("transactionId")
    state  = payload.get("state")
    print(f"Webhook: txn={txn_id} state={state}")

    transaction = await client.transactions.get(txn_id)

    # TODO: persist state change, trigger business logic

    return JSONResponse({"status": "ok"})