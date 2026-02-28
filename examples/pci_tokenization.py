"""
PCI Merchant Tokenization Example
===================================

Demonstrates the server-side portion of the PCI Merchant Tokenization flow
for PCI-approved merchants who capture card details directly.

Flow:
1. Server: fetch RSA encryption public key from BML
2. Server (or client-side): encrypt card data with RSA-OAEP SHA-256
3. Server: POST encrypted card data → receive clientSideTokenId + 3DS URL
4. Frontend: redirect customer to 3DS URL for bank authentication
5. Server: handle callback - on success, tokenId (Customer Token) in URL
6. Server: use tokenId to charge via customers.charge()

.. important::
    Private key (``sk_...``) and public key (``pk_...``) MUST be from the
    **same app** in the BML merchant dashboard.  Do not mix keys across apps.

Requirements:
    pip install bml-connect-python cryptography flask

Run:
    BML_API_KEY=sk_... BML_PUBLIC_KEY=pk_... flask --app pci_tokenization run --port 5002
"""

import os

from flask import Flask, jsonify, redirect, request, url_for

from bml_connect import BMLConnect, CardEncryption, Environment

app = Flask(__name__)

API_KEY     = os.environ.get("BML_API_KEY", "sk_your_private_key")
PUBLIC_KEY  = os.environ.get("BML_PUBLIC_KEY", "pk_your_public_key")
WEBHOOK_URL = os.environ.get("BML_WEBHOOK_URL", "https://yourapp.com/bml-webhook")

# Both keys must be set to use public_client
client = BMLConnect(
    api_key=API_KEY,
    public_key=PUBLIC_KEY,
    environment=Environment.PRODUCTION,
)


# ---------------------------------------------------------------------------
# Step 1: Expose the encryption public key to the frontend (optional)
#         OR use it server-side directly
# ---------------------------------------------------------------------------

@app.route("/api/card-encryption-key")
def get_encryption_key():
    """Return the RSA encryption key to the frontend for client-side use.

    .. warning::
        Always fetch fresh - this key can rotate at any time.
    """
    enc_key = client.public_client.get_tokens_public_key()
    return jsonify({
        "keyId": enc_key.key_id,
        "publicKey": enc_key.public_key,  # raw key - frontend adds PEM headers
    })


# ---------------------------------------------------------------------------
# Step 2 + 3: Encrypt card data and submit (server-side path)
# ---------------------------------------------------------------------------

@app.route("/api/tokenise-card", methods=["POST"])
def tokenise_card():
    """Receive raw card details, encrypt server-side, submit to BML.

    Request body (JSON):
        {
            "customerId": "...",
            "cardNumber": "4111111111111111",
            "cardCvv": "123",
            "cardExpiryMonth": 12,
            "cardExpiryYear": 29
        }

    .. note::
        In a real integration you would typically encrypt on the client
        (browser / mobile) so card data never hits your server in the clear.
        This example shows the server-side path for PCI-approved merchants only.
    """
    body = request.get_json(force=True) or {}
    customer_id = body.get("customerId")
    if not customer_id:
        return jsonify({"error": "customerId is required"}), 400

    # Build and validate card payload
    card_payload = {
        "cardNumberRaw":   body.get("cardNumber", "").replace(" ", ""),
        "cardVDRaw":       body.get("cardCvv", ""),
        "cardExpiryMonth": int(body.get("cardExpiryMonth", 0)),
        "cardExpiryYear":  int(body.get("cardExpiryYear", 0)),
    }

    try:
        CardEncryption.validate_card_payload(card_payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    # Always fetch the latest encryption key
    enc_key = client.public_client.get_tokens_public_key()

    # Encrypt card data
    try:
        card_b64 = CardEncryption.encrypt(enc_key.pem, card_payload)
    except ImportError as exc:
        return jsonify({"error": str(exc)}), 500

    # Submit to BML
    result = client.public_client.add_card(
        card_data=card_b64,
        key_id=enc_key.key_id,
        customer_id=customer_id,
        redirect=url_for("tokenisation_callback", _external=True),
        webhook=WEBHOOK_URL,
    )

    return jsonify({
        "clientSideTokenId": result.next_action.client_side_token_id if result.next_action else None,
        "redirectUrl": result.next_action.url if result.next_action else None,
    })


# ---------------------------------------------------------------------------
# Step 5: Handle 3DS callback from BML after cardholder authentication
# ---------------------------------------------------------------------------

@app.route("/tokenisation-callback")
def tokenisation_callback():
    """BML redirects here after 3DS authentication with result in query params.

    Success:
        ?tokenId=<customerTokenId>&clientSideTokenId=<id>&customerId=<id>&status=TOKENISATION_SUCCESS

    Failure:
        ?clientSideTokenId=<id>&customerId=<id>&status=TOKENISATION_FAILURE
    """
    status           = request.args.get("status")
    token_id         = request.args.get("tokenId")          # Customer Token ID (success only)
    client_token_id  = request.args.get("clientSideTokenId")
    customer_id      = request.args.get("customerId")

    if status == "TOKENISATION_SUCCESS" and token_id:
        # Card stored successfully - token_id is ready for charging
        app.logger.info(
            "Card tokenised: customer=%s tokenId=%s", customer_id, token_id
        )
        # TODO: store token_id in your database linked to the customer
        # Optionally verify by listing tokens:
        # tokens = client.customers.list_tokens(customer_id)
        return jsonify({
            "status": "success",
            "customerId": customer_id,
            "tokenId": token_id,
            "message": "Card stored successfully. You can now charge this card.",
        })

    else:
        app.logger.warning(
            "Tokenisation failed: customer=%s clientSideTokenId=%s",
            customer_id, client_token_id,
        )
        return jsonify({
            "status": "failure",
            "customerId": customer_id,
            "clientSideTokenId": client_token_id,
            "message": "Card tokenisation failed. Please try again.",
        }), 400


# ---------------------------------------------------------------------------
# Step 6: Charge a stored token
# ---------------------------------------------------------------------------

@app.route("/api/charge", methods=["POST"])
def charge_stored_token():
    """Charge a previously stored card token.

    Request body:
        {
            "customerId": "...",
            "tokenId": "...",      # from tokenisation callback or list tokens
            "amount": 5000,        # in cents
            "currency": "USD"
        }
    """
    body        = request.get_json(force=True) or {}
    customer_id = body.get("customerId")
    token_id    = body.get("tokenId")
    amount      = body.get("amount", 0)
    currency    = body.get("currency", "USD")

    if not all([customer_id, amount, currency]):
        return jsonify({"error": "customerId, amount and currency are required"}), 400

    # Create a transaction shell for this customer
    txn = client.transactions.create({
        "amount": amount,
        "currency": currency,
        "customerId": customer_id,
    })

    # Build charge payload
    charge_payload: dict = {
        "customerId": customer_id,
        "transactionId": txn.id,
    }
    if token_id:
        charge_payload["tokenId"] = token_id   # explicit token; omit for default
    
    result = client.customers.charge(charge_payload)

    # Always confirm via API query
    confirmed = client.transactions.get(txn.id)
    return jsonify({
        "transactionId": txn.id,
        "chargeState": result.state.value if result.state else None,
        "confirmedState": confirmed.state.value if confirmed.state else None,
        "amountFormatted": confirmed.amount_formatted,
    })


if __name__ == "__main__":
    if not PUBLIC_KEY or PUBLIC_KEY == "pk_your_public_key":
        print("WARNING: Set BML_PUBLIC_KEY env var to your public application key (pk_...)")
    app.run(port=5002, debug=True)