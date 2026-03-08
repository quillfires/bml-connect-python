"""
Flask Webhook Example
======================

Shows how to:
1. Register your Flask endpoint URL with BML at startup so it receives
   transaction notifications.
2. Receive and verify webhook POST requests from BML using the current
   SHA-256 header scheme (X-Signature-Nonce, X-Signature-Timestamp, X-Signature).
3. Fall back to legacy ``originalSignature`` verification for old v1 payloads.
4. Unregister the webhook URL on shutdown.

Run:
    pip install flask bml-connect-python
    BML_API_KEY=your_key BML_WEBHOOK_URL=https://yourapp.com/bml-webhook flask --app webhook_flask run --port 5000
"""

import os

from flask import Flask, jsonify, request

from bml_connect import BMLConnect, Environment

app = Flask(__name__)

API_KEY     = os.environ.get("BML_API_KEY", "your_api_key_here")
WEBHOOK_URL = os.environ.get("BML_WEBHOOK_URL", "https://yourapp.com/bml-webhook")

client = BMLConnect(api_key=API_KEY, environment=Environment.PRODUCTION)


# ---------------------------------------------------------------------------
# Register webhook at startup
# ---------------------------------------------------------------------------
with app.app_context():
    try:
        hook = client.webhooks.create(WEBHOOK_URL)
        app.logger.info("BML webhook registered: %s", hook.id)
    except Exception as exc:
        app.logger.warning("Could not register webhook (already exists?): %s", exc)


# ---------------------------------------------------------------------------
# Webhook receiver
# ---------------------------------------------------------------------------
@app.route("/bml-webhook", methods=["POST"])
def bml_webhook():
    """Receive and verify BML transaction update notifications."""

    # --- Current verification: SHA-256 of nonce + timestamp + api_key -------
    nonce     = request.headers.get("X-Signature-Nonce", "")
    timestamp = request.headers.get("X-Signature-Timestamp", "")
    signature = request.headers.get("X-Signature", "")

    if nonce and timestamp and signature:
        if not client.verify_webhook_signature(nonce, timestamp, signature):
            app.logger.warning("BML webhook: invalid signature (nonce=%s ts=%s)", nonce, timestamp)
            return jsonify({"error": "Invalid signature"}), 403

    else:
        # --- Legacy fallback: originalSignature in the JSON body (deprecated) ---
        payload = request.get_json(force=True) or {}
        original_sig = payload.get("originalSignature")
        if not original_sig:
            return jsonify({"error": "Missing signature headers"}), 400
        if not client.verify_legacy_webhook_signature(payload, original_sig):
            app.logger.warning("BML webhook: invalid legacy signature")
            return jsonify({"error": "Invalid signature"}), 403

    payload = request.get_json(force=True) or {}
    _process_notification(payload)
    return jsonify({"status": "ok"}), 200


def _process_notification(payload: dict) -> None:
    txn_id   = payload.get("id") or payload.get("transactionId")
    state    = payload.get("state")
    amount   = payload.get("amount")
    currency = payload.get("currency")
    app.logger.info("Transaction %s → state=%s  %s %s", txn_id, state, amount, currency)

    transaction = client.transactions.get(txn_id)
    # TODO: update database, trigger fulfilment, send receipts, etc.


# ---------------------------------------------------------------------------
# Unregister on teardown (useful in dev/CI)
# ---------------------------------------------------------------------------
@app.teardown_appcontext
def _unregister_webhook(_exc=None) -> None:
    if os.environ.get("BML_UNREGISTER_ON_SHUTDOWN"):
        try:
            client.webhooks.delete(WEBHOOK_URL)
            app.logger.info("BML webhook unregistered.")
        except Exception:
            pass


if __name__ == "__main__":
    app.run(port=5000, debug=True)