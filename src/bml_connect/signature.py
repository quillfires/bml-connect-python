"""
BML Connect SDK - Signature Utilities
======================================

Provides:
- Current webhook signature verification (SHA-256, header-based nonce + timestamp).
- Deprecated legacy verification (MD5 of amount/currency/apiKey via ``originalSignature``
  field in the webhook body).

Current Algorithm
-----------------
BML sends three headers with every webhook request::

    X-Signature-Nonce     - unique identifier for the request
    X-Signature-Timestamp - Unix timestamp of the request
    X-Signature           - SHA-256 hex digest of "{nonce}{timestamp}{api_key}"

Reconstruct the same string, hash it, and compare with ``X-Signature``.

Deprecated Algorithm
--------------------
Older webhook payloads included an ``originalSignature`` field in the JSON body.
That signature was an MD5 base64 digest of ``amount=X&currency=Y&apiKey=Z``.
BML no longer recommends relying on this alone - always query the API for the
source-of-truth transaction state.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
from typing import Any, Dict, Optional, Union

from .exceptions import ValidationError

logger = logging.getLogger("bml_connect")


class SignatureUtils:
    """Utility methods for BML Connect webhook signature verification."""

    # ------------------------------------------------------------------
    # Current verification (SHA-256, nonce + timestamp headers)
    # ------------------------------------------------------------------

    @staticmethod
    def verify_webhook_signature(
        nonce: str,
        timestamp: str,
        received_signature: str,
        api_key: str,
    ) -> bool:
        """Verify a BML webhook request using the current SHA-256 header scheme.

        BML attaches three headers to every outgoing webhook POST:

        - ``X-Signature-Nonce`` - a unique request identifier
        - ``X-Signature-Timestamp`` - request timestamp
        - ``X-Signature`` - ``SHA-256("{nonce}{timestamp}{api_key}")`` as a hex string

        This method reconstructs that digest and performs a constant-time
        comparison against the received signature to prevent timing attacks.

        Args:
            nonce: Value of the ``X-Signature-Nonce`` header.
            timestamp: Value of the ``X-Signature-Timestamp`` header.
            received_signature: Value of the ``X-Signature`` header.
            api_key: Your BML merchant API key.

        Returns:
            ``True`` if the signature is valid, ``False`` otherwise.

        Example (Flask)::

            from bml_connect import SignatureUtils

            @app.route("/bml-webhook", methods=["POST"])
            def webhook():
                nonce     = request.headers.get("X-Signature-Nonce", "")
                timestamp = request.headers.get("X-Signature-Timestamp", "")
                signature = request.headers.get("X-Signature", "")

                if not SignatureUtils.verify_webhook_signature(nonce, timestamp, signature, API_KEY):
                    abort(403)

                payload = request.get_json()
                # ... process payload ...
                return "", 200

        Example (FastAPI)::

            @app.post("/bml-webhook")
            async def webhook(
                request: Request,
                x_signature_nonce: str = Header(default=""),
                x_signature_timestamp: str = Header(default=""),
                x_signature: str = Header(default=""),
            ):
                if not SignatureUtils.verify_webhook_signature(
                    x_signature_nonce, x_signature_timestamp, x_signature, API_KEY
                ):
                    raise HTTPException(403)
                ...
        """
        sign_string = f"{nonce}{timestamp}{api_key}"
        generated = hashlib.sha256(sign_string.encode("utf-8")).hexdigest()
        return hmac.compare_digest(generated, received_signature)

    @staticmethod
    def verify_webhook_headers(
        headers: Dict[str, str],
        api_key: str,
        *,
        nonce_header: str = "X-Signature-Nonce",
        timestamp_header: str = "X-Signature-Timestamp",
        signature_header: str = "X-Signature",
    ) -> bool:
        """Convenience wrapper - verify directly from a headers dict.

        Extracts ``X-Signature-Nonce``, ``X-Signature-Timestamp``, and
        ``X-Signature`` from the provided mapping and delegates to
        :meth:`verify_webhook_signature`.

        Args:
            headers: A dict-like object of request headers (case-sensitive keys).
            api_key: Your BML merchant API key.
            nonce_header: Header name for the nonce (default: ``X-Signature-Nonce``).
            timestamp_header: Header name for the timestamp (default: ``X-Signature-Timestamp``).
            signature_header: Header name for the signature (default: ``X-Signature``).

        Returns:
            ``True`` if the signature is valid, ``False`` otherwise.

        Example::

            # Works with any framework that exposes headers as a dict
            is_valid = SignatureUtils.verify_webhook_headers(request.headers, API_KEY)
        """
        nonce = headers.get(nonce_header, "")
        timestamp = headers.get(timestamp_header, "")
        signature = headers.get(signature_header, "")

        if not all([nonce, timestamp, signature]):
            logger.warning(
                "verify_webhook_headers: one or more signature headers are missing "
                "(%s=%r, %s=%r, %s=%r)",
                nonce_header,
                nonce,
                timestamp_header,
                timestamp,
                signature_header,
                signature,
            )
            return False

        return SignatureUtils.verify_webhook_signature(
            nonce, timestamp, signature, api_key
        )

    # ------------------------------------------------------------------
    # Deprecated - MD5 / originalSignature (v1 webhook payloads)
    # ------------------------------------------------------------------

    @staticmethod
    def verify_legacy_signature(
        data: Dict[str, Any],
        original_signature: str,
        api_key: str,
    ) -> bool:
        """Verify the deprecated ``originalSignature`` field in a v1 webhook payload.

        .. deprecated::
            BML no longer recommends relying solely on this check.  Always query
            the API (``client.transactions.get(id)``) for the authoritative
            transaction state.  Use :meth:`verify_webhook_signature` for all
            new integrations.

        The legacy signature is an MD5 base64 digest of the query string
        ``amount={amount}&currency={currency}&apiKey={api_key}``.

        Args:
            data: Webhook payload dict containing at least ``amount`` and
                ``currency``.
            original_signature: The ``originalSignature`` value from the payload.
            api_key: Your BML merchant API key.

        Returns:
            ``True`` if the signature matches.
        """
        amount = data.get("amount")
        currency = data.get("currency")

        if not amount or not currency:
            raise ValueError(
                "amount and currency are required for legacy signature verification"
            )

        sign_string = f"amount={amount}&currency={currency}&apiKey={api_key}"
        calculated = base64.b64encode(
            hashlib.md5(sign_string.encode("utf-8")).digest()
        ).decode("utf-8")

        return hmac.compare_digest(calculated, original_signature)

    @staticmethod
    def parse_and_verify_legacy_webhook(
        payload: Union[Dict[str, Any], str, bytes],
        api_key: str,
    ) -> bool:
        """Parse a JSON webhook body and verify its ``originalSignature`` field.

        .. deprecated::
            See :meth:`verify_legacy_signature`.  For new integrations use
            :meth:`verify_webhook_signature` with the HTTP headers instead.

        Args:
            payload: Raw JSON bytes/string or already-parsed dict.
            api_key: Your BML merchant API key.

        Returns:
            ``True`` if the signature is valid.

        Raises:
            :class:`.ValidationError`: If payload is not valid JSON or
                ``originalSignature`` is missing.
        """
        if isinstance(payload, (bytes, str)):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise ValidationError("Invalid JSON webhook payload") from exc

        assert isinstance(payload, dict)
        original_signature = payload.get("originalSignature")
        if not original_signature:
            raise ValidationError(
                "Missing 'originalSignature' field in webhook payload"
            )

        return SignatureUtils.verify_legacy_signature(
            payload, original_signature, api_key
        )

    # ------------------------------------------------------------------
    # Removed in v2 - generate_legacy_signature / generate_signature
    # kept as thin stubs that raise a clear error so callers notice
    # immediately rather than silently misbehaving.
    # ------------------------------------------------------------------

    @staticmethod
    def generate_legacy_signature(
        data: Dict[str, Any],
        api_key: str,
        method: Optional[Any] = None,
    ) -> str:
        """Removed in v2 - V2 transactions do not require a request signature.

        .. deprecated::
            This method existed for the legacy ``POST /public/transactions``
            (v1) endpoint which required a SHA-1/MD5 signature in the request
            body.  The current ``POST /public/v2/transactions`` endpoint does
            not use request signatures.

        Raises:
            NotImplementedError: Always.  Remove signature generation from your
                transaction payload and use :meth:`verify_webhook_signature`
                for incoming webhook verification instead.
        """
        raise NotImplementedError(
            "generate_legacy_signature() has been removed in SDK v2. "
            "The V2 transaction endpoint does not require a request signature. "
            "For webhook verification use SignatureUtils.verify_webhook_signature() "
            "with the X-Signature-Nonce, X-Signature-Timestamp, and X-Signature headers."
        )

    # Keep the old alias name pointing to the same stub
    generate_signature = generate_legacy_signature


__all__ = ["SignatureUtils"]
