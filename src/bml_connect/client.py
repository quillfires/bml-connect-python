"""
BML Connect Python SDK
======================

Robust Python SDK for Bank of Maldives Connect API v2 with comprehensive
sync/async support.

Four Integration Methods
------------------------

**Redirect Method** - hosted payment page, easiest to integrate::

    from bml_connect import BMLConnect, Environment

    with BMLConnect(api_key="sk_...", environment=Environment.SANDBOX) as client:
        txn = client.transactions.create({
            "redirectUrl": "https://yourapp.com/thanks",
            "localId": "INV-001",
            "order": {"shopId": "SHOP_ID", "products": [...]},
        })
        redirect_to(txn.url)          # full URL
        redirect_to(txn.short_url)    # short URL for SMS / messaging

**Direct Method** - your UI, you control everything::

    txn = client.transactions.create({
        "amount": 1000, "currency": "USD",
        "provider": "alipay",          # QR providers: vendorQrCode in response
        "webhook": "https://...",      # mandatory for Direct Method
    })
    qr_img = encode_qr(txn.vendor_qr_code)   # show in-store

**Card-On-File / Tokenization** - recurring / one-click::

    # First charge - capture and tokenize
    txn = client.transactions.create({
        "amount": 100, "currency": "USD",
        "tokenizationDetails": {"tokenize": True, "paymentType": "UNSCHEDULED",
                                 "recurringFrequency": "UNSCHEDULED"},
        "customerId": "CUSTOMER_ID", "customerAsPayer": True,
        "webhook": "https://...",
    })
    # After NOTIFY_TOKENISATION_STATUS webhook → list tokens
    tokens = client.customers.list_tokens("CUSTOMER_ID")

    # Subsequent charges - no customer interaction needed
    new_txn = client.transactions.create({"amount": 200, "currency": "USD",
                                           "customerId": "CUSTOMER_ID"})
    result = client.customers.charge({"customerId": "CUSTOMER_ID",
                                       "transactionId": new_txn.id,
                                       "tokenId": tokens[0].id})

**PCI Merchant Tokenization** - encrypt card details server-side::

    with BMLConnect(api_key="sk_...", public_key="pk_...",
                    environment=Environment.SANDBOX) as client:
        enc_key = client.public_client.get_tokens_public_key()
        card_b64 = CardEncryption.encrypt(enc_key.pem, {
            "cardNumberRaw": "4111111111111111", "cardVDRaw": "123",
            "cardExpiryMonth": 12, "cardExpiryYear": 29,
        })
        result = client.public_client.add_card(
            card_data=card_b64, key_id=enc_key.key_id,
            customer_id="CUSTOMER_ID",
            redirect="https://yourapp.com/tokenisation-callback",
        )
        redirect_to(result.next_action.url)   # 3DS authentication
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional, Union

from . import __version__
from .exceptions import ValidationError
from .models import Environment
from .resources import (
    AsyncCompanyResource,
    AsyncCustomersResource,
    AsyncPublicClientResource,
    AsyncShopsResource,
    AsyncTransactionsResource,
    AsyncWebhooksResource,
    CompanyResource,
    CustomersResource,
    PublicClientResource,
    ShopsResource,
    TransactionsResource,
    WebhooksResource,
)
from .signature import SignatureUtils
from .transport import AsyncTransport, SyncTransport

logger = logging.getLogger("bml_connect")
logger.addHandler(logging.NullHandler())


class BMLConnect:
    """Primary entry point for the BML Connect SDK.

    Args:
        api_key: Your private API key (``sk_...`` or legacy format) from the
            BML merchant portal.
        environment: :attr:`Environment.PRODUCTION` (default) or
            :attr:`Environment.SANDBOX`.
        async_mode: Set ``True`` to use async/await.  All resource methods
            become coroutines and must be awaited.
        public_key: Your public application key (``pk_...``).  Required only
            for PCI Merchant Tokenization via ``client.public_client``.
            Must be from the **same app** as ``api_key`` - keys cannot be
            mixed across apps.

    Attributes:
        company: :class:`~.resources.CompanyResource` - ``GET /public/me``.
        webhooks: :class:`~.resources.WebhooksResource` - register / remove
            webhook URLs in the BML backend.
        transactions: :class:`~.resources.TransactionsResource` - all four
            integration methods; create, retrieve, update, SMS/email share.
        shops: :class:`~.resources.ShopsResource` - full CRUD for shops,
            products, categories, taxes, order fields, custom fees.
        customers: :class:`~.resources.CustomersResource` - customer CRUD,
            token management, charge stored card-on-file tokens.
        public_client: :class:`~.resources.PublicClientResource` - PCI
            Merchant Tokenization.  Fetch RSA encryption key and submit
            encrypted card data.  Only available when ``public_key`` is set.

    Example (sync)::

        client = BMLConnect(api_key="sk_...", environment=Environment.SANDBOX)
        txn = client.transactions.create({...})

    Example (async)::

        async with BMLConnect(api_key="sk_...", environment=Environment.SANDBOX,
                               async_mode=True) as client:
            txn = await client.transactions.create({...})

    Example (PCI tokenization)::

        with BMLConnect(api_key="sk_...", public_key="pk_...",
                        environment=Environment.SANDBOX) as client:
            enc_key = client.public_client.get_tokens_public_key()
    """

    def __init__(
        self,
        api_key: str,
        environment: Union[Environment, str] = Environment.PRODUCTION,
        *,
        async_mode: bool = False,
        public_key: Optional[str] = None,
        # Legacy positional arg - kept for backward compat with SDK v1.x
        app_id: Optional[str] = None,
    ) -> None:
        self.api_key = api_key
        self.public_key = public_key

        if isinstance(environment, str):
            try:
                self.environment = Environment[environment.upper()]
            except KeyError:
                raise ValueError(
                    f"Invalid environment '{environment}'. Use 'production' or 'sandbox'."
                )
        else:
            self.environment = environment

        self.async_mode = async_mode

        if async_mode:
            _t: AsyncTransport = AsyncTransport(api_key, self.environment)
            self.company: Union[CompanyResource, AsyncCompanyResource] = (
                AsyncCompanyResource(_t)
            )
            self.webhooks: Union[WebhooksResource, AsyncWebhooksResource] = (
                AsyncWebhooksResource(_t)
            )
            self.transactions: Union[
                TransactionsResource, AsyncTransactionsResource
            ] = AsyncTransactionsResource(_t, api_key)
            self.shops: Union[ShopsResource, AsyncShopsResource] = AsyncShopsResource(
                _t
            )
            self.customers: Union[CustomersResource, AsyncCustomersResource] = (
                AsyncCustomersResource(_t)
            )
            self._async_transport = _t
            self._sync_transport: Optional[SyncTransport] = None
            # PCI Tokenization - requires public_key
            if public_key:
                _pt: AsyncTransport = AsyncTransport(public_key, self.environment)
                self.public_client: Union[
                    PublicClientResource, AsyncPublicClientResource, None
                ] = AsyncPublicClientResource(_pt)
                self._public_async_transport: Optional[AsyncTransport] = _pt
            else:
                self.public_client = None
                self._public_async_transport = None
            self._public_sync_transport: Optional[SyncTransport] = None
        else:
            _st: SyncTransport = SyncTransport(api_key, self.environment)
            self.company = CompanyResource(_st)
            self.webhooks = WebhooksResource(_st)
            self.transactions = TransactionsResource(_st, api_key)
            self.shops = ShopsResource(_st)
            self.customers = CustomersResource(_st)
            self._sync_transport = _st
            self._async_transport = None  # type: ignore[assignment]
            # PCI Tokenization - requires public_key
            if public_key:
                _pst: SyncTransport = SyncTransport(public_key, self.environment)
                self.public_client = PublicClientResource(_pst)
                self._public_sync_transport = _pst
            else:
                self.public_client = None
                self._public_sync_transport = None
            self._public_async_transport = None

        logger.info("██████╗ ███╗   ███╗██╗      ")
        logger.info("██╔══██╗████╗ ████║██║      ")
        logger.info("██████╔╝██╔████╔██║██║      ")
        logger.info("██╔══██╗██║╚██╔╝██║██║      ")
        logger.info("██████╔╝██║ ╚═╝ ██║███████╗ ")
        logger.info("╚═════╝ ╚═╝     ╚═╝╚══════╝ ")
        logger.info(" ██████╗ ██████╗ ███╗   ██╗███╗   ██╗███████╗ ██████╗████████╗")
        logger.info("██╔════╝██╔═══██╗████╗  ██║████╗  ██║██╔════╝██╔════╝╚══██╔══╝")
        logger.info("██║     ██║   ██║██╔██╗ ██║██╔██╗ ██║█████╗  ██║        ██║   ")
        logger.info("██║     ██║   ██║██║╚██╗██║██║╚██╗██║██╔══╝  ██║        ██║   ")
        logger.info("╚██████╗╚██████╔╝██║ ╚████║██║ ╚████║███████╗╚██████╗   ██║   ")
        logger.info(" ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝ ╚═════╝   ╚═╝   ")
        logger.info("Python SDK for Bank of Maldives Connect API")
        logger.info("Author: Ali Fayaz (Quill) (quillfires)")
        logger.info("Version: v%s", __version__)
        logger.info("copyright (c) 2025-present Ali Fayaz (Quill) (quillfires)")
        logger.info(
            "env=%s  async=%s  public_key=%s",
            self.environment.name,
            async_mode,
            bool(public_key),
        )

    # ------------------------------------------------------------------
    # Webhook signature verification helpers
    # ------------------------------------------------------------------

    def verify_webhook_signature(
        self,
        nonce: str,
        timestamp: str,
        received_signature: str,
    ) -> bool:
        """Verify an incoming BML webhook request using the current SHA-256 scheme.

        BML sends three headers with every webhook POST:

        - ``X-Signature-Nonce`` - unique request identifier
        - ``X-Signature-Timestamp`` - request timestamp
        - ``X-Signature`` - ``SHA-256("{nonce}{timestamp}{api_key}")`` as hex

        Args:
            nonce: Value of the ``X-Signature-Nonce`` header.
            timestamp: Value of the ``X-Signature-Timestamp`` header.
            received_signature: Value of the ``X-Signature`` header.

        Returns:
            ``True`` if the signature is valid.

        Example (Flask)::

            nonce     = request.headers.get("X-Signature-Nonce", "")
            timestamp = request.headers.get("X-Signature-Timestamp", "")
            signature = request.headers.get("X-Signature", "")

            if not client.verify_webhook_signature(nonce, timestamp, signature):
                abort(403)

        Example (FastAPI)::

            @app.post("/bml-webhook")
            async def webhook(
                request: Request,
                x_signature_nonce: str = Header(default=""),
                x_signature_timestamp: str = Header(default=""),
                x_signature: str = Header(default=""),
            ):
                if not client.verify_webhook_signature(
                    x_signature_nonce, x_signature_timestamp, x_signature
                ):
                    raise HTTPException(403)
        """
        return SignatureUtils.verify_webhook_signature(
            nonce, timestamp, received_signature, self.api_key
        )

    def verify_webhook_headers(self, headers: Dict[str, str]) -> bool:
        """Convenience wrapper - verify directly from a headers dict.

        Extracts ``X-Signature-Nonce``, ``X-Signature-Timestamp``, and
        ``X-Signature`` from ``headers`` and verifies the signature.

        Args:
            headers: Dict-like request headers object.

        Returns:
            ``True`` if the signature is valid.

        Example (Flask)::

            if not client.verify_webhook_headers(request.headers):
                abort(403)

        Example (FastAPI)::

            if not client.verify_webhook_headers(dict(request.headers)):
                raise HTTPException(403)
        """
        return SignatureUtils.verify_webhook_headers(headers, self.api_key)

    def verify_legacy_webhook_signature(
        self,
        payload: Union[Dict[str, Any], str, bytes],
        original_signature: str,
    ) -> bool:
        """Verify the deprecated ``originalSignature`` field in a v1 webhook payload.

        .. deprecated::
            BML no longer recommends relying solely on this check.  Always query
            the API (``client.transactions.get(id)``) for the authoritative
            transaction state.  Use :meth:`verify_webhook_signature` or
            :meth:`verify_webhook_headers` for all new integrations.

        Args:
            payload: Parsed dict or raw JSON string/bytes.
            original_signature: The ``originalSignature`` value from the payload.

        Returns:
            ``True`` if the signature is valid.
        """
        if isinstance(payload, (str, bytes)):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise ValidationError("Invalid JSON payload") from exc

        assert isinstance(payload, dict)
        return SignatureUtils.verify_legacy_signature(
            payload, original_signature, self.api_key
        )

    # ------------------------------------------------------------------
    # Context manager / cleanup
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Release synchronous HTTP resources."""
        if self._sync_transport:
            self._sync_transport.close()
        if self._public_sync_transport:
            self._public_sync_transport.close()

    async def aclose(self) -> None:
        """Release asynchronous HTTP resources."""
        if self._async_transport:
            await self._async_transport.close()
        if self._public_async_transport:
            await self._public_async_transport.close()

    def __enter__(self) -> "BMLConnect":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    async def __aenter__(self) -> "BMLConnect":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()


__all__ = ["BMLConnect"]
