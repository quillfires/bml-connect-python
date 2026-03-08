"""
BML Connect SDK - Resource Managers
=====================================

Each class exposes the operations for one API tag (Transactions, Webhooks,
Shops, Products, …).  Both sync and async flavours are provided; the async
versions simply prefix every method with ``await``.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Union

from .models import (
    Category,
    ClientTokenResponse,
    Company,
    Customer,
    CustomerToken,
    CustomFee,
    OrderField,
    PaginatedResponse,
    Product,
    Shop,
    Tax,
    TokensPublicKey,
    Transaction,
    Webhook,
)
from .signature import SignatureUtils
from .transport import AsyncTransport, SyncTransport

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _coerce_list(value: Any) -> List[Any]:
    """Ensure a response value is always a list."""
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


# ===========================================================================
# Company
# ===========================================================================


class CompanyResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def get(self) -> List[Company]:
        """GET /public/me - Return merchant company details."""
        data = self._t.request("GET", "/public/me")
        return [Company.from_dict(item) for item in _coerce_list(data)]


class AsyncCompanyResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> List[Company]:
        data = await self._t.request("GET", "/public/me")
        return [Company.from_dict(item) for item in _coerce_list(data)]


# ===========================================================================
# Webhooks
# ===========================================================================


class WebhooksResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def create(self, hook_url: str) -> Webhook:
        """POST /public/webhooks - Register a webhook URL with BML.

        After registering, BML will POST transaction update notifications to
        ``hook_url``.

        Args:
            hook_url: Publicly accessible HTTPS URL.

        Returns:
            :class:`.Webhook` with the created record.
        """
        data = self._t.request(
            "POST", "/public/webhooks", json_body={"hookUrl": hook_url}
        )
        return Webhook.from_dict(data)

    def delete(self, hook_url: str) -> None:
        """DELETE /public/webhooks - Unregister a webhook URL.

        Args:
            hook_url: The exact URL used when creating the webhook.
        """
        self._t.request("DELETE", "/public/webhooks", json_body={"hookUrl": hook_url})


class AsyncWebhooksResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def create(self, hook_url: str) -> Webhook:
        data = await self._t.request(
            "POST", "/public/webhooks", json_body={"hookUrl": hook_url}
        )
        return Webhook.from_dict(data)

    async def delete(self, hook_url: str) -> None:
        await self._t.request(
            "DELETE", "/public/webhooks", json_body={"hookUrl": hook_url}
        )


# ===========================================================================
# Transactions
# ===========================================================================


class TransactionsResource:
    """Manages transaction operations (sync).

    **V2 (current)** - use :meth:`create` for order-based or amount-based
    transactions.  No request signature required.

    **V1 (legacy)** - use :meth:`create_v1` which still generates the
    deprecated SHA-1 signature.
    """

    def __init__(self, transport: SyncTransport, api_key: str) -> None:
        self._t = transport
        self._api_key = api_key

    # --- V2 (current) -------------------------------------------------------

    def create(self, data: Dict[str, Any]) -> Transaction:
        """POST /public/v2/transactions - Create a transaction.

        This is the single endpoint for all four integration methods:

        **Redirect Method** - redirect customer to the hosted payment page::

            txn = client.transactions.create({
                "redirectUrl": "https://yourstore.com/thanks",
                "localId": "INV-001",
                "customerReference": "Order #42",
                "order": {"shopId": "<shop-id>", "products": [...]},
                # Optional: customise the hosted page experience
                "paymentPortalExperience": {
                    "skipProviderSelection": True,
                    "skipCustomerForm": True,
                    "externalWebsiteTermsAccepted": True,
                    "externalWebsiteTermsUrl": "https://mysite.mv/terms",
                },
                # Optional: control failure behaviour
                "allowRetry": False,
                "paymentAttemptFailureUrl": "https://mystore.com/checkout/123",
            })
            redirect_to(txn.url)  # or txn.short_url

        **Direct Method / QR providers** (alipay, unionpay, wechatpay, bml_mobilepay)
        - encode ``vendor_qr_code`` into a QR image to display in-store::

            txn = client.transactions.create({
                "amount": 1000,
                "currency": "USD",
                "provider": "alipay",  # or unionpay / wechatpay / bml_mobilepay
                "webhook": "https://yourstore.com/bml-webhook",
                "locale": "en",
            })
            qr_data = txn.vendor_qr_code  # encode this into a QR image

        **Direct Method / card & online providers** (mpgs, debit_credit_card,
        alipay_online) - response contains ``url``, redirect customer there::

            txn = client.transactions.create({
                "amount": 1000,
                "currency": "USD",
                "provider": "mpgs",
                "webhook": "https://yourstore.com/bml-webhook",
            })
            redirect_to(txn.url)

        **Card-On-File (tokenization)** - capture card for future recurring use::

            # New customer inline
            txn = client.transactions.create({
                "amount": 100,
                "currency": "USD",
                "tokenizationDetails": {
                    "tokenize": True,
                    "paymentType": "UNSCHEDULED",
                    "recurringFrequency": "UNSCHEDULED",
                },
                "customer": {"name": "Alice", "email": "alice@example.com", ...},
                "customerAsPayer": True,
                "webhook": "https://yourstore.com/bml-webhook",
            })

            # Existing customer
            txn = client.transactions.create({
                "amount": 100,
                "currency": "USD",
                "tokenizationDetails": {
                    "tokenize": True,
                    "paymentType": "UNSCHEDULED",
                    "recurringFrequency": "UNSCHEDULED",
                },
                "customerId": "<existing-customer-id>",
                "customerAsPayer": True,
                "webhook": "https://yourstore.com/bml-webhook",
            })

        After payment, BML calls your webhook with
        ``NOTIFY_TOKENISATION_STATUS`` (card stored) and/or
        ``NOTIFY_TRANSACTION_CHANGE`` (payment state change).

        Args:
            data: Request payload dict.  See BML API docs for full field list.

        Returns:
            :class:`.Transaction` - check ``txn.state``, ``txn.url``,
            ``txn.short_url``, ``txn.vendor_qr_code`` depending on flow.
        """
        resp = self._t.request("POST", "/public/v2/transactions", json_body=data)
        return Transaction.from_dict(resp)

    def get(self, transaction_id: str) -> Transaction:
        """GET /public/transactions/{id} - Fetch a single transaction."""
        resp = self._t.request("GET", f"/public/transactions/{transaction_id}")
        return Transaction.from_dict(resp)

    def update(
        self,
        transaction_id: str,
        *,
        customer_reference: Optional[str] = None,
        local_data: Optional[str] = None,
        pnr: Optional[str] = None,
    ) -> Transaction:
        """PATCH /public/transactions/{id} - Update mutable transaction fields.

        Args:
            transaction_id: The transaction ID to update.
            customer_reference: Up to 140 chars shown to customer on receipts.
            local_data: Up to 1000 chars of merchant-side metadata.
            pnr: Up to 64 chars booking/PNR reference.

        Returns:
            Updated :class:`.Transaction`.
        """
        body: Dict[str, Any] = {}
        if customer_reference is not None:
            body["customerReference"] = customer_reference
        if local_data is not None:
            body["localData"] = local_data
        if pnr is not None:
            body["pnr"] = pnr

        resp = self._t.request(
            "PATCH", f"/public/transactions/{transaction_id}", json_body=body
        )
        return Transaction.from_dict(resp)

    def send_sms(self, transaction_id: str, mobile: str) -> Transaction:
        """POST /public/transactions/{id}/send-sms - Share payment link via SMS.

        Rate-limited to once per minute per transaction to prevent spam.

        Args:
            transaction_id: The transaction to share.
            mobile: Phone number with country code (e.g. ``"9609601234"``).
                The ``+`` prefix is optional - BML normalises it.

        Returns:
            Updated :class:`.Transaction`.
        """
        resp = self._t.request(
            "POST",
            f"/public/transactions/{transaction_id}/send-sms",
            json_body={"mobile": mobile},
        )
        return Transaction.from_dict(resp)

    def send_email(
        self,
        transaction_id: str,
        emails: Union[str, List[str]],
    ) -> Transaction:
        """POST /public/transactions/{id}/send-email - Share payment link via email.

        Rate-limited to once per minute per transaction.

        Args:
            transaction_id: The transaction to share.
            emails: A single email address string or a list of addresses.

        Returns:
            Updated :class:`.Transaction`.
        """
        resp = self._t.request(
            "POST",
            f"/public/transactions/{transaction_id}/send-email",
            json_body={"emails": emails},
        )
        return Transaction.from_dict(resp)

    # --- V1 (legacy) --------------------------------------------------------

    def create_v1(self, data: Dict[str, Any]) -> Transaction:
        """POST /public/transactions - Create a transaction using the legacy v1 API.

        .. deprecated::
            The V1 transaction endpoint and its SHA-1/MD5 signature scheme have
            been deprecated by BML.  Use :meth:`create` (V2) for new integrations.

        Automatically computes and injects the ``signature`` field.
        """
        prepared = {
            "apiVersion": "2.0",
            "signMethod": "sha1",
            "appVersion": "BML-Connect-Python",
            "deviceId": str(uuid.uuid4()),
            **data,
        }
        from .models import SignMethod

        try:
            sign_method = SignMethod(prepared.get("signMethod", "sha1"))
        except ValueError:
            sign_method = SignMethod.SHA1

        prepared["signature"] = SignatureUtils.generate_legacy_signature(
            prepared, self._api_key, sign_method
        )
        resp = self._t.request("POST", "/public/transactions", json_body=prepared)
        return Transaction.from_dict(resp)

    # Backward-compatible aliases
    create_transaction = create
    get_transaction = get
    list_transactions = None  # see below

    def list(
        self,
        page: int = 1,
        per_page: int = 20,
        state: Optional[str] = None,
        provider: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> PaginatedResponse:
        """List transactions with optional filtering.

        Note: The V2 API spec does not define a dedicated list endpoint; this
        method targets the legacy ``/public/transactions`` GET if available.
        """
        params: Dict[str, Any] = {"page": page, "perPage": per_page}
        if state:
            params["state"] = state
        if provider:
            params["provider"] = provider
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        resp = self._t.request("GET", "/public/transactions", params=params)
        if isinstance(resp, list):
            return PaginatedResponse(
                count=len(resp),
                items=[Transaction.from_dict(i) for i in resp],
                current_page=1,
                total_pages=1,
            )
        return PaginatedResponse.from_dict(resp)


# Patch alias
TransactionsResource.list_transactions = TransactionsResource.list  # type: ignore[method-assign]


class AsyncTransactionsResource:
    def __init__(self, transport: AsyncTransport, api_key: str) -> None:
        self._t = transport
        self._api_key = api_key

    async def create(self, data: Dict[str, Any]) -> Transaction:
        resp = await self._t.request("POST", "/public/v2/transactions", json_body=data)
        return Transaction.from_dict(resp)

    async def get(self, transaction_id: str) -> Transaction:
        resp = await self._t.request("GET", f"/public/transactions/{transaction_id}")
        return Transaction.from_dict(resp)

    async def update(
        self,
        transaction_id: str,
        *,
        customer_reference: Optional[str] = None,
        local_data: Optional[str] = None,
        pnr: Optional[str] = None,
    ) -> Transaction:
        body: Dict[str, Any] = {}
        if customer_reference is not None:
            body["customerReference"] = customer_reference
        if local_data is not None:
            body["localData"] = local_data
        if pnr is not None:
            body["pnr"] = pnr
        resp = await self._t.request(
            "PATCH", f"/public/transactions/{transaction_id}", json_body=body
        )
        return Transaction.from_dict(resp)

    async def send_sms(self, transaction_id: str, mobile: str) -> Transaction:
        resp = await self._t.request(
            "POST",
            f"/public/transactions/{transaction_id}/send-sms",
            json_body={"mobile": mobile},
        )
        return Transaction.from_dict(resp)

    async def send_email(
        self, transaction_id: str, emails: Union[str, List[str]]
    ) -> Transaction:
        resp = await self._t.request(
            "POST",
            f"/public/transactions/{transaction_id}/send-email",
            json_body={"emails": emails},
        )
        return Transaction.from_dict(resp)

    async def create_v1(self, data: Dict[str, Any]) -> Transaction:
        """Legacy v1 transaction creation (deprecated)."""
        prepared = {
            "apiVersion": "2.0",
            "signMethod": "sha1",
            "appVersion": "BML-Connect-Python",
            "deviceId": str(uuid.uuid4()),
            **data,
        }
        from .models import SignMethod

        try:
            sign_method = SignMethod(prepared.get("signMethod", "sha1"))
        except ValueError:
            sign_method = SignMethod.SHA1

        prepared["signature"] = SignatureUtils.generate_legacy_signature(
            prepared, self._api_key, sign_method
        )
        resp = await self._t.request("POST", "/public/transactions", json_body=prepared)
        return Transaction.from_dict(resp)

    async def list(
        self,
        page: int = 1,
        per_page: int = 20,
        state: Optional[str] = None,
        provider: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> PaginatedResponse:
        params: Dict[str, Any] = {"page": page, "perPage": per_page}
        if state:
            params["state"] = state
        if provider:
            params["provider"] = provider
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        resp = await self._t.request("GET", "/public/transactions", params=params)
        if isinstance(resp, list):
            return PaginatedResponse(
                count=len(resp),
                items=[Transaction.from_dict(i) for i in resp],
                current_page=1,
                total_pages=1,
            )
        return PaginatedResponse.from_dict(resp)

    # Aliases
    create_transaction = create
    get_transaction = get
    list_transactions = list


# ===========================================================================
# Shops
# ===========================================================================


class ShopsResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def list(self) -> List[Shop]:
        """GET /public/shops - List all shops."""
        data = self._t.request("GET", "/public/shops")
        items = data.get("items", data) if isinstance(data, dict) else data
        return [Shop.from_dict(i) for i in _coerce_list(items)]

    def create(self, payload: Dict[str, Any]) -> Shop:
        """POST /public/shops - Create a new shop."""
        data = self._t.request("POST", "/public/shops", json_body=payload)
        return Shop.from_dict(data)

    def get(self, shop_id: str) -> Shop:
        """GET /public/shops/{shopId}."""
        data = self._t.request("GET", f"/public/shops/{shop_id}")
        return Shop.from_dict(data)

    def update(self, shop_id: str, payload: Dict[str, Any]) -> Shop:
        """PATCH /public/shops/{shopId}."""
        data = self._t.request("PATCH", f"/public/shops/{shop_id}", json_body=payload)
        return Shop.from_dict(data)

    # -- Products ------------------------------------------------------------

    def list_products(self, shop_id: str) -> List[Product]:
        """GET /public/shops/{shopId}/products."""
        data = self._t.request("GET", f"/public/shops/{shop_id}/products")
        items = data.get("items", data) if isinstance(data, dict) else data
        return [Product.from_dict(i) for i in _coerce_list(items)]

    def create_product(self, shop_id: str, payload: Dict[str, Any]) -> Product:
        """POST /public/shops/{shopId}/products."""
        data = self._t.request(
            "POST", f"/public/shops/{shop_id}/products", json_body=payload
        )
        return Product.from_dict(data)

    def create_products_batch(
        self, shop_id: str, products: List[Dict[str, Any]]
    ) -> List[Product]:
        """POST /public/shops/{shopId}/products-batch - Bulk create products."""
        data = self._t.request(
            "POST", f"/public/shops/{shop_id}/products-batch", json_body=products
        )
        return [Product.from_dict(i) for i in _coerce_list(data)]

    def get_product(self, shop_id: str, product_id: str) -> Product:
        """GET /public/shops/{shopId}/products/{productId}."""
        data = self._t.request("GET", f"/public/shops/{shop_id}/products/{product_id}")
        return Product.from_dict(data)

    def update_product(
        self, shop_id: str, product_id: str, payload: Dict[str, Any]
    ) -> Product:
        """PATCH /public/shops/{shopId}/products/{productId}."""
        data = self._t.request(
            "PATCH", f"/public/shops/{shop_id}/products/{product_id}", json_body=payload
        )
        return Product.from_dict(data)

    def delete_product(self, shop_id: str, product_id: str) -> None:
        """DELETE /public/shops/{shopId}/products/{productId}."""
        self._t.request("DELETE", f"/public/shops/{shop_id}/products/{product_id}")

    def update_product_by_sku(self, shop_id: str, payload: Dict[str, Any]) -> Product:
        """PATCH /public/shops/{shopId}/products-by-sku."""
        data = self._t.request(
            "PATCH", f"/public/shops/{shop_id}/products-by-sku", json_body=payload
        )
        return Product.from_dict(data)

    def upload_product_image(
        self,
        shop_id: str,
        product_id: str,
        image_bytes: bytes,
        filename: str = "image.jpg",
    ) -> Dict[str, Any]:
        """POST /public/shops/{shopId}/products/{productId}/images."""
        files = {"file": (filename, image_bytes)}
        return self._t.request(  # type: ignore[return-value]
            "POST",
            f"/public/shops/{shop_id}/products/{product_id}/images",
            files=files,
        )

    def update_products_taxes(
        self, shop_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """PUT /public/shops/{shopId}/products-taxes - Bulk update tax assignments."""
        return self._t.request(  # type: ignore[return-value]
            "PUT", f"/public/shops/{shop_id}/products-taxes", json_body=payload
        )

    # -- Order Fields --------------------------------------------------------

    def list_order_fields(self, shop_id: str) -> List[OrderField]:
        """GET /public/shops/{shopId}/order-fields."""
        data = self._t.request("GET", f"/public/shops/{shop_id}/order-fields")
        items = data.get("items", data) if isinstance(data, dict) else data
        return [OrderField.from_dict(i) for i in _coerce_list(items)]

    def create_order_field(self, shop_id: str, payload: Dict[str, Any]) -> OrderField:
        """POST /public/shops/{shopId}/order-fields."""
        data = self._t.request(
            "POST", f"/public/shops/{shop_id}/order-fields", json_body=payload
        )
        return OrderField.from_dict(data)

    def update_order_field(
        self, shop_id: str, order_field_id: str, payload: Dict[str, Any]
    ) -> OrderField:
        """PATCH /public/shops/{shopId}/order-fields/{orderFieldId}."""
        data = self._t.request(
            "PATCH",
            f"/public/shops/{shop_id}/order-fields/{order_field_id}",
            json_body=payload,
        )
        return OrderField.from_dict(data)

    def delete_order_field(self, shop_id: str, order_field_id: str) -> None:
        """DELETE /public/shops/{shopId}/order-fields/{orderFieldId}."""
        self._t.request(
            "DELETE", f"/public/shops/{shop_id}/order-fields/{order_field_id}"
        )

    # -- Custom Fees ---------------------------------------------------------

    def list_custom_fees(self, shop_id: str) -> List[CustomFee]:
        """GET /public/shops/{shopId}/custom-fees."""
        data = self._t.request("GET", f"/public/shops/{shop_id}/custom-fees")
        items = data.get("items", data) if isinstance(data, dict) else data
        return [CustomFee.from_dict(i) for i in _coerce_list(items)]

    def create_custom_fee(self, shop_id: str, payload: Dict[str, Any]) -> CustomFee:
        """POST /public/shops/{shopId}/custom-fees."""
        data = self._t.request(
            "POST", f"/public/shops/{shop_id}/custom-fees", json_body=payload
        )
        return CustomFee.from_dict(data)

    def update_custom_fee(
        self, shop_id: str, custom_fee_id: str, payload: Dict[str, Any]
    ) -> CustomFee:
        """PATCH /public/shops/{shopId}/custom-fees/{customFeeId}."""
        data = self._t.request(
            "PATCH",
            f"/public/shops/{shop_id}/custom-fees/{custom_fee_id}",
            json_body=payload,
        )
        return CustomFee.from_dict(data)

    def delete_custom_fee(self, shop_id: str, custom_fee_id: str) -> None:
        """DELETE /public/shops/{shopId}/custom-fees/{customFeeId}."""
        self._t.request(
            "DELETE", f"/public/shops/{shop_id}/custom-fees/{custom_fee_id}"
        )

    # -- Categories ----------------------------------------------------------

    def list_categories(self, shop_id: str) -> List[Category]:
        """GET /public/shops/{shopId}/categories."""
        data = self._t.request("GET", f"/public/shops/{shop_id}/categories")
        items = data.get("items", data) if isinstance(data, dict) else data
        return [Category.from_dict(i) for i in _coerce_list(items)]

    def create_category(self, shop_id: str, payload: Dict[str, Any]) -> Category:
        """POST /public/shops/{shopId}/categories."""
        data = self._t.request(
            "POST", f"/public/shops/{shop_id}/categories", json_body=payload
        )
        return Category.from_dict(data)

    def update_category(
        self, shop_id: str, category_id: str, payload: Dict[str, Any]
    ) -> Category:
        """PATCH /public/shops/{shopId}/categories/{categoryId}."""
        data = self._t.request(
            "PATCH",
            f"/public/shops/{shop_id}/categories/{category_id}",
            json_body=payload,
        )
        return Category.from_dict(data)

    def delete_category(self, shop_id: str, category_id: str) -> None:
        """DELETE /public/shops/{shopId}/categories/{categoryId}."""
        self._t.request("DELETE", f"/public/shops/{shop_id}/categories/{category_id}")

    # -- Taxes ---------------------------------------------------------------

    def list_taxes(self, shop_id: str) -> List[Tax]:
        """GET /public/shops/{shopId}/taxes."""
        data = self._t.request("GET", f"/public/shops/{shop_id}/taxes")
        items = data.get("items", data) if isinstance(data, dict) else data
        return [Tax.from_dict(i) for i in _coerce_list(items)]

    def create_tax(self, shop_id: str, payload: Dict[str, Any]) -> Tax:
        """POST /public/shops/{shopId}/taxes."""
        data = self._t.request(
            "POST", f"/public/shops/{shop_id}/taxes", json_body=payload
        )
        return Tax.from_dict(data)

    def delete_tax(self, shop_id: str, tax_id: str) -> None:
        """DELETE /public/shops/{shopId}/taxes/{taxId}."""
        self._t.request("DELETE", f"/public/shops/{shop_id}/taxes/{tax_id}")


class AsyncShopsResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> List[Shop]:
        data = await self._t.request("GET", "/public/shops")
        items = data.get("items", data) if isinstance(data, dict) else data
        return [Shop.from_dict(i) for i in _coerce_list(items)]

    async def create(self, payload: Dict[str, Any]) -> Shop:
        data = await self._t.request("POST", "/public/shops", json_body=payload)
        return Shop.from_dict(data)

    async def get(self, shop_id: str) -> Shop:
        data = await self._t.request("GET", f"/public/shops/{shop_id}")
        return Shop.from_dict(data)

    async def update(self, shop_id: str, payload: Dict[str, Any]) -> Shop:
        data = await self._t.request(
            "PATCH", f"/public/shops/{shop_id}", json_body=payload
        )
        return Shop.from_dict(data)

    async def list_products(self, shop_id: str) -> List[Product]:
        data = await self._t.request("GET", f"/public/shops/{shop_id}/products")
        items = data.get("items", data) if isinstance(data, dict) else data
        return [Product.from_dict(i) for i in _coerce_list(items)]

    async def create_product(self, shop_id: str, payload: Dict[str, Any]) -> Product:
        data = await self._t.request(
            "POST", f"/public/shops/{shop_id}/products", json_body=payload
        )
        return Product.from_dict(data)

    async def get_product(self, shop_id: str, product_id: str) -> Product:
        data = await self._t.request(
            "GET", f"/public/shops/{shop_id}/products/{product_id}"
        )
        return Product.from_dict(data)

    async def update_product(
        self, shop_id: str, product_id: str, payload: Dict[str, Any]
    ) -> Product:
        data = await self._t.request(
            "PATCH", f"/public/shops/{shop_id}/products/{product_id}", json_body=payload
        )
        return Product.from_dict(data)

    async def delete_product(self, shop_id: str, product_id: str) -> None:
        await self._t.request(
            "DELETE", f"/public/shops/{shop_id}/products/{product_id}"
        )

    async def create_products_batch(
        self, shop_id: str, products: List[Dict[str, Any]]
    ) -> List[Product]:
        data = await self._t.request(
            "POST", f"/public/shops/{shop_id}/products-batch", json_body=products
        )
        return [Product.from_dict(i) for i in _coerce_list(data)]

    async def update_product_by_sku(
        self, shop_id: str, payload: Dict[str, Any]
    ) -> Product:
        data = await self._t.request(
            "PATCH", f"/public/shops/{shop_id}/products-by-sku", json_body=payload
        )
        return Product.from_dict(data)

    async def update_products_taxes(
        self, shop_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        return await self._t.request("PUT", f"/public/shops/{shop_id}/products-taxes", json_body=payload)  # type: ignore[return-value]

    async def list_order_fields(self, shop_id: str) -> List[OrderField]:
        data = await self._t.request("GET", f"/public/shops/{shop_id}/order-fields")
        items = data.get("items", data) if isinstance(data, dict) else data
        return [OrderField.from_dict(i) for i in _coerce_list(items)]

    async def create_order_field(
        self, shop_id: str, payload: Dict[str, Any]
    ) -> OrderField:
        data = await self._t.request(
            "POST", f"/public/shops/{shop_id}/order-fields", json_body=payload
        )
        return OrderField.from_dict(data)

    async def update_order_field(
        self, shop_id: str, order_field_id: str, payload: Dict[str, Any]
    ) -> OrderField:
        data = await self._t.request(
            "PATCH",
            f"/public/shops/{shop_id}/order-fields/{order_field_id}",
            json_body=payload,
        )
        return OrderField.from_dict(data)

    async def delete_order_field(self, shop_id: str, order_field_id: str) -> None:
        await self._t.request(
            "DELETE", f"/public/shops/{shop_id}/order-fields/{order_field_id}"
        )

    async def list_custom_fees(self, shop_id: str) -> List[CustomFee]:
        data = await self._t.request("GET", f"/public/shops/{shop_id}/custom-fees")
        items = data.get("items", data) if isinstance(data, dict) else data
        return [CustomFee.from_dict(i) for i in _coerce_list(items)]

    async def create_custom_fee(
        self, shop_id: str, payload: Dict[str, Any]
    ) -> CustomFee:
        data = await self._t.request(
            "POST", f"/public/shops/{shop_id}/custom-fees", json_body=payload
        )
        return CustomFee.from_dict(data)

    async def update_custom_fee(
        self, shop_id: str, custom_fee_id: str, payload: Dict[str, Any]
    ) -> CustomFee:
        data = await self._t.request(
            "PATCH",
            f"/public/shops/{shop_id}/custom-fees/{custom_fee_id}",
            json_body=payload,
        )
        return CustomFee.from_dict(data)

    async def delete_custom_fee(self, shop_id: str, custom_fee_id: str) -> None:
        await self._t.request(
            "DELETE", f"/public/shops/{shop_id}/custom-fees/{custom_fee_id}"
        )

    async def list_categories(self, shop_id: str) -> List[Category]:
        data = await self._t.request("GET", f"/public/shops/{shop_id}/categories")
        items = data.get("items", data) if isinstance(data, dict) else data
        return [Category.from_dict(i) for i in _coerce_list(items)]

    async def create_category(self, shop_id: str, payload: Dict[str, Any]) -> Category:
        data = await self._t.request(
            "POST", f"/public/shops/{shop_id}/categories", json_body=payload
        )
        return Category.from_dict(data)

    async def update_category(
        self, shop_id: str, category_id: str, payload: Dict[str, Any]
    ) -> Category:
        data = await self._t.request(
            "PATCH",
            f"/public/shops/{shop_id}/categories/{category_id}",
            json_body=payload,
        )
        return Category.from_dict(data)

    async def delete_category(self, shop_id: str, category_id: str) -> None:
        await self._t.request(
            "DELETE", f"/public/shops/{shop_id}/categories/{category_id}"
        )

    async def list_taxes(self, shop_id: str) -> List[Tax]:
        data = await self._t.request("GET", f"/public/shops/{shop_id}/taxes")
        items = data.get("items", data) if isinstance(data, dict) else data
        return [Tax.from_dict(i) for i in _coerce_list(items)]

    async def create_tax(self, shop_id: str, payload: Dict[str, Any]) -> Tax:
        data = await self._t.request(
            "POST", f"/public/shops/{shop_id}/taxes", json_body=payload
        )
        return Tax.from_dict(data)

    async def delete_tax(self, shop_id: str, tax_id: str) -> None:
        await self._t.request("DELETE", f"/public/shops/{shop_id}/taxes/{tax_id}")


# ===========================================================================
# Customers
# ===========================================================================


class CustomersResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def list(self) -> List[Customer]:
        """GET /public-customers - List all customers."""
        data = self._t.request("GET", "/public-customers")
        items = data.get("items", data) if isinstance(data, dict) else data
        return [Customer.from_dict(i) for i in _coerce_list(items)]

    def create(self, payload: Dict[str, Any]) -> Customer:
        """POST /public-customers - Create a new customer.

        Required fields: ``name``, ``email``, ``companyId``, ``currency``.
        """
        data = self._t.request("POST", "/public-customers", json_body=payload)
        return Customer.from_dict(data)

    def get(self, customer_id: str) -> Customer:
        """GET /public-customers/{customerId}."""
        data = self._t.request("GET", f"/public-customers/{customer_id}")
        return Customer.from_dict(data)

    def update(self, customer_id: str, payload: Dict[str, Any]) -> Customer:
        """PATCH /public-customers/{customerId}."""
        data = self._t.request(
            "PATCH", f"/public-customers/{customer_id}", json_body=payload
        )
        return Customer.from_dict(data)

    def delete(self, customer_id: str) -> None:
        """DELETE /public-customers/{customerId} - Archive customer."""
        self._t.request("DELETE", f"/public-customers/{customer_id}")

    def list_tokens(self, customer_id: str) -> List[CustomerToken]:
        """GET /public-customers/{customerId}/tokens."""
        data = self._t.request("GET", f"/public-customers/{customer_id}/tokens")
        items = data.get("items", data) if isinstance(data, dict) else data
        return [CustomerToken.from_dict(i) for i in _coerce_list(items)]

    def get_token(self, customer_id: str, token_id: str) -> CustomerToken:
        """GET /public-customers/{customerId}/tokens/{tokenId}."""
        data = self._t.request(
            "GET", f"/public-customers/{customer_id}/tokens/{token_id}"
        )
        return CustomerToken.from_dict(data)

    def delete_token(self, customer_id: str, token_id: str) -> None:
        """DELETE /public-customers/{customerId}/tokens/{tokenId}."""
        self._t.request("DELETE", f"/public-customers/{customer_id}/tokens/{token_id}")

    def charge(self, payload: Dict[str, Any]) -> Transaction:
        """POST /public-customers/charge - Charge a stored card-on-file token.

        Only ``mpgs`` and ``debit_credit_card`` providers support tokenisation.
        You must first create a transaction with ``tokenizationDetails.tokenize: true``
        and the customer must complete the initial payment to store the card.

        Three options for specifying which card to charge:

        **Option 1 - by token ID** (recommended)::

            txn = client.customers.charge({
                "customerId": "651e62e9d5d5c900086366cf",
                "transactionId": "652f4b1477b8290008d94996",
                "tokenId": "652e642589dc860008b38500",
            })

        **Option 2 - by raw token string**::

            txn = client.customers.charge({
                "customerId": "651e62e9d5d5c900086366cf",
                "transactionId": "652f4b1477b8290008d94996",
                "token": "b9c6522baa0f6f15...",
            })

        **Option 3 - default token** (no token specified)::

            txn = client.customers.charge({
                "customerId": "651e62e9d5d5c900086366cf",
                "transactionId": "652f4b1477b8290008d94996",
            })

        Always confirm the result by querying the transaction or listening
        to ``NOTIFY_TRANSACTION_CHANGE`` webhooks - do not rely solely on
        the charge response.

        Returns:
            :class:`.Transaction` for the charge attempt.
        """
        data = self._t.request("POST", "/public-customers/charge", json_body=payload)
        return Transaction.from_dict(data)


class AsyncCustomersResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> List[Customer]:
        data = await self._t.request("GET", "/public-customers")
        items = data.get("items", data) if isinstance(data, dict) else data
        return [Customer.from_dict(i) for i in _coerce_list(items)]

    async def create(self, payload: Dict[str, Any]) -> Customer:
        data = await self._t.request("POST", "/public-customers", json_body=payload)
        return Customer.from_dict(data)

    async def get(self, customer_id: str) -> Customer:
        data = await self._t.request("GET", f"/public-customers/{customer_id}")
        return Customer.from_dict(data)

    async def update(self, customer_id: str, payload: Dict[str, Any]) -> Customer:
        data = await self._t.request(
            "PATCH", f"/public-customers/{customer_id}", json_body=payload
        )
        return Customer.from_dict(data)

    async def delete(self, customer_id: str) -> None:
        await self._t.request("DELETE", f"/public-customers/{customer_id}")

    async def list_tokens(self, customer_id: str) -> List[CustomerToken]:
        data = await self._t.request("GET", f"/public-customers/{customer_id}/tokens")
        items = data.get("items", data) if isinstance(data, dict) else data
        return [CustomerToken.from_dict(i) for i in _coerce_list(items)]

    async def get_token(self, customer_id: str, token_id: str) -> CustomerToken:
        data = await self._t.request(
            "GET", f"/public-customers/{customer_id}/tokens/{token_id}"
        )
        return CustomerToken.from_dict(data)

    async def delete_token(self, customer_id: str, token_id: str) -> None:
        await self._t.request(
            "DELETE", f"/public-customers/{customer_id}/tokens/{token_id}"
        )

    async def charge(self, payload: Dict[str, Any]) -> Transaction:
        """POST /public-customers/charge - async variant.

        See :meth:`.CustomersResource.charge` for full documentation and
        all three token-specification options.
        """
        data = await self._t.request(
            "POST", "/public-customers/charge", json_body=payload
        )
        return Transaction.from_dict(data)


# ===========================================================================
# Public Client - PCI Merchant Tokenization
# ===========================================================================


class PublicClientResource:
    """Server-side counterpart for PCI Merchant Tokenization (sync).

    Uses your **public** application key (``pk_...``) rather than the private
    API key.  The public key is set via ``BMLConnect(public_key="pk_...")``.

    Workflow::

        # 1. Fetch the RSA encryption key (always fetch fresh - it rotates)
        enc_key = client.public_client.get_tokens_public_key()

        # 2. Encrypt card data on the client (browser/mobile) using enc_key.pem
        #    - see CardEncryption utility or use PomeloJS in the browser

        # 3. Submit encrypted card data → get 3DS redirect URL
        result = client.public_client.add_card(
            card_data="<base64-RSA-OAEP-encrypted-card-json>",
            key_id=enc_key.key_id,
            customer_id="<customer-id>",
            redirect="https://yourstore.com/tokenisation-callback",
            webhook="https://yourstore.com/bml-webhook",   # optional
        )

        # 4. Redirect customer to 3DS page
        redirect_to(result.next_action.url)

        # 5. On callback success: ?tokenId=<id>&status=TOKENISATION_SUCCESS
        #    Use tokenId to charge the card via client.customers.charge(...)
    """

    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def get_tokens_public_key(self) -> TokensPublicKey:
        """GET /public-client/tokens-public-key - Fetch RSA encryption key.

        .. warning::
            This key rotates.  Always fetch the latest version immediately
            before encrypting card data.  Never cache it long-term.

        Returns:
            :class:`.TokensPublicKey` with ``key_id`` and ``pem`` (PEM string).
        """
        data = self._t.request("GET", "/public-client/tokens-public-key")
        return TokensPublicKey.from_dict(data)

    def add_card(
        self,
        card_data: str,
        key_id: str,
        customer_id: str,
        redirect: str,
        webhook: Optional[str] = None,
    ) -> ClientTokenResponse:
        """POST /public-client/tokens - Submit encrypted card data for tokenisation.

        The ``card_data`` field must be Base64-encoded RSA-OAEP (SHA-256)
        ciphertext of the raw card JSON::

            {
                "cardNumberRaw": "4111111111111111",
                "cardVDRaw": "123",
                "cardExpiryMonth": 12,
                "cardExpiryYear": 29
            }

        Use :class:`.CardEncryption` to encrypt::

            from bml_connect import CardEncryption
            enc_key = client.public_client.get_tokens_public_key()
            card_data_b64 = CardEncryption.encrypt(enc_key.pem, {
                "cardNumberRaw": "4111111111111111",
                "cardVDRaw": "123",
                "cardExpiryMonth": 12,
                "cardExpiryYear": 29,
            })

        Args:
            card_data: Base64 RSA-OAEP encrypted card JSON string.
            key_id: The ``keyId`` from :meth:`get_tokens_public_key`.
            customer_id: 24-character customer ID the card is linked to.
            redirect: HTTPS URL BML redirects to after 3DS authentication.
                On success: ``?tokenId=<id>&status=TOKENISATION_SUCCESS``
                On failure: ``?clientSideTokenId=<id>&status=TOKENISATION_FAILURE``
            webhook: Optional HTTPS URL for async tokenisation status notification.

        Returns:
            :class:`.ClientTokenResponse` - redirect customer to
            ``result.next_action.url`` for 3DS authentication.

        .. important::
            ``next_action.client_side_token_id`` is **not** a payment token.
            The usable ``tokenId`` (Customer Token) is only available after
            successful 3DS, returned as a query parameter on your ``redirect`` URL.
        """
        body: Dict[str, Any] = {
            "cardData": card_data,
            "keyId": key_id,
            "customerId": customer_id,
            "redirect": redirect,
        }
        if webhook is not None:
            body["webhook"] = webhook

        data = self._t.request("POST", "/public-client/tokens", json_body=body)
        return ClientTokenResponse.from_dict(data)


class AsyncPublicClientResource:
    """Server-side counterpart for PCI Merchant Tokenization (async).

    See :class:`PublicClientResource` for full documentation.
    """

    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def get_tokens_public_key(self) -> TokensPublicKey:
        """GET /public-client/tokens-public-key - async variant.

        .. warning::
            Always fetch fresh - this key rotates.
        """
        data = await self._t.request("GET", "/public-client/tokens-public-key")
        return TokensPublicKey.from_dict(data)

    async def add_card(
        self,
        card_data: str,
        key_id: str,
        customer_id: str,
        redirect: str,
        webhook: Optional[str] = None,
    ) -> ClientTokenResponse:
        """POST /public-client/tokens - async variant.

        See :meth:`.PublicClientResource.add_card` for full documentation.
        """
        body: Dict[str, Any] = {
            "cardData": card_data,
            "keyId": key_id,
            "customerId": customer_id,
            "redirect": redirect,
        }
        if webhook is not None:
            body["webhook"] = webhook

        data = await self._t.request("POST", "/public-client/tokens", json_body=body)
        return ClientTokenResponse.from_dict(data)


__all__ = [
    "CompanyResource",
    "AsyncCompanyResource",
    "WebhooksResource",
    "AsyncWebhooksResource",
    "TransactionsResource",
    "AsyncTransactionsResource",
    "ShopsResource",
    "AsyncShopsResource",
    "CustomersResource",
    "AsyncCustomersResource",
    "PublicClientResource",
    "AsyncPublicClientResource",
]
