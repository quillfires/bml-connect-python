"""
Direct Method Example
======================

Shows how to create transactions for each Direct Method provider type:

- QR providers (alipay, unionpay, wechatpay, bml_mobilepay) → encode vendorQrCode
- Card / online providers (mpgs, debit_credit_card, alipay_online) → redirect to url

Requires:
    pip install bml-connect-python flask qrcode[pil]

Run:
    BML_API_KEY=your_key flask --app direct_method run --port 5001
"""

import os
from io import BytesIO

from flask import Flask, jsonify, redirect, request, send_file

from bml_connect import BMLConnect, Environment, Provider, WebhookEvent

app    = Flask(__name__)
client = BMLConnect(
    api_key=os.environ.get("BML_API_KEY", "your_api_key"),
    environment=Environment.PRODUCTION,
)
WEBHOOK_URL = os.environ.get("BML_WEBHOOK_URL", "https://yourapp.com/bml-webhook")

# ---------------------------------------------------------------------------
# QR Providers - display a QR code in-store
# ---------------------------------------------------------------------------

@app.route("/qr-payment/<provider>")
def qr_payment(provider: str):
    """Create a QR payment and return the QR image.

    Supported providers: alipay, unionpay, wechatpay, bml_mobilepay
    """
    try:
        import qrcode
    except ImportError:
        return jsonify({"error": "Install qrcode[pil]: pip install 'qrcode[pil]'"}), 500

    valid_qr_providers = {
        Provider.ALIPAY.value,
        Provider.UNIONPAY.value,
        Provider.WECHATPAY.value,
        Provider.BML_MOBILEPAY.value,
    }
    if provider not in valid_qr_providers:
        return jsonify({"error": f"Provider must be one of {valid_qr_providers}"}), 400

    txn = client.transactions.create({
        "amount": 1000,          # 10.00 USD
        "currency": "USD",
        "provider": provider,
        "localId": "QR-INV-001",
        "webhook": WEBHOOK_URL,
        "locale": "en",
        # Include customer details so they don't need to fill in the gateway
        "customer": {
            "name": "Alice Smith",
            "email": "alice@example.com",
        },
    })

    if not txn.vendor_qr_code:
        return jsonify({"error": "No QR code data in response"}), 500

    qr = qrcode.QRCode(version=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_L,
                       box_size=10, border=4)
    qr.add_data(txn.vendor_qr_code)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return send_file(buf, mimetype="image/png",
                     download_name=f"qr_{txn.id}.png")


@app.route("/qr-payment/<provider>/json")
def qr_payment_json(provider: str):
    """Return QR transaction details as JSON (for frontend rendering)."""
    txn = client.transactions.create({
        "amount": int(request.args.get("amount", 1000)),
        "currency": request.args.get("currency", "USD"),
        "provider": provider,
        "webhook": WEBHOOK_URL,
        "locale": "en",
    })
    return jsonify({
        "transactionId": txn.id,
        "vendorQrCode": txn.vendor_qr_code,
        "state": txn.state.value if txn.state else None,
    })


# ---------------------------------------------------------------------------
# Card / Online Providers - redirect customer to secure form
# ---------------------------------------------------------------------------

@app.route("/card-payment/<provider>")
def card_payment(provider: str):
    """Create a card/online payment and redirect to the secure form.

    Supported providers: mpgs, debit_credit_card, alipay_online
    """
    valid_redirect_providers = {
        Provider.MPGS.value,
        Provider.DEBIT_CREDIT_CARD.value,
        Provider.ALIPAY_ONLINE.value,
    }
    if provider not in valid_redirect_providers:
        return jsonify({"error": f"Provider must be one of {valid_redirect_providers}"}), 400

    txn = client.transactions.create({
        "amount": 2500,
        "currency": "USD",
        "provider": provider,
        "redirectUrl": "https://yourapp.com/payment-complete",
        "webhook": WEBHOOK_URL,
        "locale": "en",
        "customer": {
            "name": "Bob Jones",
            "email": "bob@example.com",
            "billingAddress1": "1 Main Street",
            "billingCity": "Malé",
            "billingCountry": "MV",
        },
        # Control the portal experience
        "paymentPortalExperience": {
            "skipCustomerForm": True,
            "skipProviderSelection": True,
        },
    })

    if not txn.url:
        return jsonify({"error": "No redirect URL in response", "txn": str(txn)}), 500

    return redirect(txn.url, code=302)


# ---------------------------------------------------------------------------
# Poll transaction status
# ---------------------------------------------------------------------------

@app.route("/transaction/<txn_id>/status")
def transaction_status(txn_id: str):
    """Query the current state of a transaction."""
    txn = client.transactions.get(txn_id)
    return jsonify({
        "id": txn.id,
        "state": txn.state.value if txn.state else None,
        "amount": txn.amount,
        "currency": txn.currency,
        "provider": txn.provider,
        "amountFormatted": txn.amount_formatted,
        "canVoid": txn.can_void,
        "canRefundIfConfirmed": txn.can_refund_if_confirmed,
    })


# ---------------------------------------------------------------------------
# Webhook receiver (shared with all provider types)
# ---------------------------------------------------------------------------

@app.route("/bml-webhook", methods=["POST"])
def bml_webhook():
    nonce     = request.headers.get("X-Signature-Nonce", "")
    timestamp = request.headers.get("X-Signature-Timestamp", "")
    signature = request.headers.get("X-Signature", "")

    if nonce and timestamp and signature:
        if not client.verify_webhook_signature(nonce, timestamp, signature):
            return jsonify({"error": "Invalid signature"}), 403
    else:
        payload = request.get_json(force=True) or {}
        if not client.verify_legacy_webhook_signature(payload, payload.get("originalSignature", "")):
            return jsonify({"error": "Invalid signature"}), 403

    payload = request.get_json(force=True) or {}
    event = WebhookEvent.from_dict(payload)

    app.logger.info(
        "Webhook event=%s txn=%s state=%s provider=%s amount=%s %s",
        event.event_type,
        event.transaction_id,
        event.state,
        event.provider,
        event.amount,
        event.currency,
    )

    # Handle specific states
    if event.state and event.state.value == "CONFIRMED":
        # TODO: fulfil order, send receipt, etc.
        pass
    elif event.state and event.state.value in ("CANCELLED", "FAILED"):
        # TODO: notify customer, re-enable checkout, etc.
        pass

    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(port=5001, debug=True)