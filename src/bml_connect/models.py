"""
BML Connect SDK - Data Models
==============================

All dataclass models representing API resources.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("bml_connect")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Environment(Enum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"

    @property
    def base_url(self) -> str:
        return {
            Environment.SANDBOX: "https://api.uat.merchants.bankofmaldives.com.mv",
            Environment.PRODUCTION: "https://api.merchants.bankofmaldives.com.mv",
        }[self]


class TransactionState(Enum):
    """All possible states a BML Connect transaction can be in."""

    INITIATED = "INITIATED"             # Created; QR asset not yet ready
    CREATED = "CREATED"                 # Legacy alias for INITIATED
    QR_CODE_GENERATED = "QR_CODE_GENERATED"  # Pending, awaiting customer action
    CONFIRMED = "CONFIRMED"             # Payment completed
    CANCELLED = "CANCELLED"             # User cancelled or timed out
    FAILED = "FAILED"                   # Permanently failed
    EXPIRED = "EXPIRED"                 # Link expired
    VOIDED = "VOIDED"                   # Payment reversed
    REFUND_REQUESTED = "REFUND_REQUESTED"  # Refund under review
    REFUNDED = "REFUNDED"               # Refund completed
    AUTHORIZED = "AUTHORIZED"           # Pre-auth approved, not yet captured


class Provider(Enum):
    """Payment provider values for use in transaction creation."""

    MPGS = "mpgs"                       # Domestic card (supports tokenisation)
    DEBIT_CREDIT_CARD = "debit_credit_card"  # International card (supports tokenisation)
    ALIPAY = "alipay"                   # Alipay in-person QR
    ALIPAY_ONLINE = "alipay_online"     # Alipay online / e-commerce
    UNIONPAY = "unionpay"               # UnionPay QR
    WECHATPAY = "wechatpay"             # WechatPay QR
    BML_MOBILEPAY = "bml_mobilepay"     # BML MobilePay QR
    CASH = "cash"                       # Cash

    @classmethod
    def _missing_(cls, value: object) -> Optional["Provider"]:
        return None


class WebhookEventType(Enum):
    """Event types carried in BML webhook notification payloads."""
    NOTIFY_TRANSACTION_CHANGE = "NOTIFY_TRANSACTION_CHANGE"
    NOTIFY_TOKENISATION_STATUS = "NOTIFY_TOKENISATION_STATUS"

    @classmethod
    def _missing_(cls, value: object) -> Optional["WebhookEventType"]:
        return None


class TokenisationStatus(Enum):
    SUCCESS = "TOKENISATION_SUCCESS"
    FAILURE = "TOKENISATION_FAILURE"

    @classmethod
    def _missing_(cls, value: object) -> Optional["TokenisationStatus"]:
        return None


class SignMethod(Enum):
    """Legacy signature methods - no longer used for V2 transactions."""
    SHA1 = "sha1"
    MD5 = "md5"

    @classmethod
    def _missing_(cls, value: object) -> "SignMethod":
        if isinstance(value, str):
            for member in cls:
                if member.value == value.lower():
                    return member
        return cls.SHA1


# ---------------------------------------------------------------------------
# Core transaction model
# ---------------------------------------------------------------------------

@dataclass
class QRCode:
    url: str
    image: Optional[str] = None


@dataclass
class Transaction:
    """Represents a BML Connect transaction (V2 API).

    Integration method guide:
    - **Redirect**: send customer to ``url`` or ``short_url``
    - **Direct / QR providers** (alipay, unionpay, wechatpay, bml_mobilepay):
      encode ``vendor_qr_code`` into a QR image
    - **Direct / card providers** (mpgs, debit_credit_card, alipay_online):
      redirect to ``url``
    - **Card-On-File**: ``customer_id`` links to stored ``CustomerToken`` records
    - **3DS / PCI tokenization**: follow ``next_action`` URL for authentication
    """

    # Core identifiers
    id: Optional[str] = None
    transaction_id: Optional[str] = None       # backward-compat alias for id
    local_id: Optional[str] = None
    external_id: Optional[str] = None
    external_source: Optional[str] = None
    customer_reference: Optional[str] = None

    # Financial - amounts in cents / smallest currency unit
    amount: Optional[int] = None
    amount_fractional: Optional[float] = None  # human-readable decimal e.g. 10.00
    amount_formatted: Optional[str] = None     # e.g. "USD 10.00"
    amount_as_decimal: Optional[str] = None    # string e.g. "5.10"
    amount_before_discount: Optional[int] = None
    amount_discounted: Optional[int] = None
    available_balance: Optional[int] = None
    currency: Optional[str] = None
    pay_currency: Optional[str] = None
    sub_total: Optional[int] = None
    taxes_total: Optional[int] = None
    service_charge_total: Optional[int] = None
    pay_amount: Optional[int] = None
    captured_amount: Optional[int] = None
    preauthorized_amount: Optional[int] = None
    preauthorized_expiry_date: Optional[str] = None

    # State & provider
    provider: Optional[str] = None
    provider_display_name: Optional[str] = None
    provider_brand_name: Optional[str] = None
    state: Optional[TransactionState] = None
    accounting_state: Optional[str] = None
    order_state: Optional[str] = None
    order_state_slug: Optional[str] = None

    # Links & QR
    url: Optional[str] = None
    short_url: Optional[str] = None
    url_hash: Optional[str] = None
    redirect_url: Optional[str] = None
    payment_attempt_failure_url: Optional[str] = None
    vendor_qr_code: Optional[str] = None       # QR data string for direct QR providers
    vendor_url: Optional[str] = None
    qr_code: Optional[QRCode] = None

    # Timestamps
    created: Optional[str] = None
    updated: Optional[str] = None
    expires: Optional[str] = None
    refund_expiry_date: Optional[str] = None
    last_shared: Optional[str] = None

    # Card details
    padded_card_number: Optional[str] = None
    card_exp_month: Optional[str] = None
    card_exp_year: Optional[str] = None
    card_funding: Optional[str] = None
    card_country: Optional[str] = None
    eci_indicator: Optional[str] = None
    avsr: Optional[str] = None

    # Refund chain
    refund_id: Optional[str] = None
    refund_reason: Optional[str] = None
    parent_transaction_id: Optional[str] = None
    refund_transaction_ids: List[str] = field(default_factory=list)
    refund_transactions: List[Dict[str, Any]] = field(default_factory=list)

    # Boolean flags
    is_payment_link: Optional[bool] = None
    is_shop: Optional[bool] = None
    is_pre_authorization: Optional[bool] = None
    is_tap_to_pay: Optional[bool] = None
    is_test: Optional[bool] = None
    three_d_secure: Optional[bool] = None
    tokenize: Optional[bool] = None
    dcc: Optional[bool] = None
    implicit_dcc: Optional[bool] = None
    has_error: Optional[bool] = None
    allow_retry: Optional[bool] = None
    can_refund_if_confirmed: Optional[bool] = None
    can_incremental_partial_refund_if_confirmed: Optional[bool] = None
    can_partial_refund_if_confirmed: Optional[bool] = None
    can_void: Optional[bool] = None
    on_hold: Optional[bool] = None
    send_customer_email_receipt: Optional[bool] = None
    self_topup: Optional[bool] = None
    external_import: Optional[bool] = None
    billing_info_provided_via_api: Optional[bool] = None

    # Counters
    loop_count: Optional[int] = None
    rating: Optional[int] = None

    # 3DS / next action
    next_action: Optional[str] = None

    # Relations
    customer_id: Optional[str] = None
    merchant_id: Optional[str] = None
    shift_id: Optional[str] = None
    remittance_id: Optional[str] = None

    # Lists
    attachments: List[Any] = field(default_factory=list)
    custom_providers: List[Any] = field(default_factory=list)
    payment_links: List[Any] = field(default_factory=list)
    provider_history: List[Any] = field(default_factory=list)
    history: List[Any] = field(default_factory=list)
    payment_error_history: List[Any] = field(default_factory=list)

    # Legacy / meta
    signature: Optional[str] = None
    original_signature: Optional[str] = None
    sign_method: Optional[SignMethod] = None
    app_version: Optional[str] = None
    api_version: Optional[str] = None
    device_id: Optional[str] = None
    security_word: Optional[str] = None

    # Mutable update fields (PATCH endpoint)
    local_data: Optional[str] = None
    pnr: Optional[str] = None

    # Raw pass-through for unmapped fields
    _raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transaction":
        qr_code: Optional[QRCode] = None
        qr_data = data.get("qr") or data.get("qrCode") or {}
        if qr_data and "url" in qr_data:
            qr_code = QRCode(url=qr_data["url"], image=qr_data.get("image"))

        state: Optional[TransactionState] = None
        if raw_state := data.get("state"):
            try:
                state = TransactionState(raw_state)
            except ValueError:
                logger.warning("Unknown transaction state: %s", raw_state)

        sign_method: Optional[SignMethod] = None
        if raw_sm := data.get("signMethod"):
            try:
                sign_method = SignMethod(raw_sm)
            except ValueError:
                logger.warning("Unknown sign method: %s", raw_sm)

        return cls(
            id=data.get("id"),
            transaction_id=data.get("id") or data.get("transactionId"),
            local_id=data.get("localId"),
            external_id=data.get("externalId"),
            external_source=data.get("externalSource"),
            customer_reference=data.get("customerReference"),
            amount=data.get("amount"),
            amount_fractional=data.get("amountFractional"),
            amount_formatted=data.get("amountFormatted"),
            amount_as_decimal=data.get("amountAsDecimal"),
            amount_before_discount=data.get("amountBeforeDiscount"),
            amount_discounted=data.get("amountDiscounted"),
            available_balance=data.get("availableBalance"),
            currency=data.get("currency"),
            pay_currency=data.get("payCurrency"),
            sub_total=data.get("subTotal"),
            taxes_total=data.get("taxesTotal"),
            service_charge_total=data.get("serviceChargeTotal"),
            pay_amount=data.get("payAmount"),
            captured_amount=data.get("capturedAmount"),
            preauthorized_amount=data.get("preauthorizedAmount"),
            preauthorized_expiry_date=data.get("preauthorizedExpiryDate"),
            provider=data.get("provider"),
            provider_display_name=data.get("providerDisplayName"),
            provider_brand_name=data.get("providerBrandName"),
            state=state,
            accounting_state=data.get("accountingState"),
            order_state=data.get("orderState"),
            order_state_slug=data.get("orderStateSlug"),
            url=data.get("url"),
            short_url=data.get("shortUrl"),
            url_hash=data.get("urlHash"),
            redirect_url=data.get("redirectUrl"),
            payment_attempt_failure_url=data.get("paymentAttemptFailureUrl"),
            vendor_qr_code=data.get("vendorQrCode"),
            vendor_url=data.get("vendorUrl"),
            qr_code=qr_code,
            created=data.get("created"),
            updated=data.get("updated"),
            expires=data.get("expires"),
            refund_expiry_date=data.get("refundExpiryDate"),
            last_shared=data.get("lastShared"),
            padded_card_number=data.get("paddedCardNumber"),
            card_exp_month=data.get("cardExpMonth"),
            card_exp_year=data.get("cardExpYear"),
            card_funding=data.get("cardFunding"),
            card_country=data.get("cardCountry"),
            eci_indicator=data.get("eciIndicator"),
            avsr=data.get("avsr"),
            refund_id=data.get("refundId"),
            refund_reason=data.get("refundReason"),
            parent_transaction_id=data.get("parentTransactionId"),
            refund_transaction_ids=data.get("refundTransactionIds") or [],
            refund_transactions=data.get("refundTransactions") or [],
            is_payment_link=data.get("isPaymentLink"),
            is_shop=data.get("isShop"),
            is_pre_authorization=data.get("isPreAuthorization"),
            is_tap_to_pay=data.get("isTapToPay"),
            is_test=data.get("isTest"),
            three_d_secure=data.get("threeDSecure"),
            tokenize=data.get("tokenize"),
            dcc=data.get("dcc"),
            implicit_dcc=data.get("implicitDcc"),
            has_error=data.get("hasError"),
            allow_retry=data.get("allowRetry"),
            can_refund_if_confirmed=data.get("canRefundIfConfirmed"),
            can_incremental_partial_refund_if_confirmed=data.get("canIncrementalPartialRefundIfConfirmed"),
            can_partial_refund_if_confirmed=data.get("canPartialRefundIfConfirmed"),
            can_void=data.get("canVoid"),
            on_hold=data.get("onHold"),
            send_customer_email_receipt=data.get("sendCustomerEmailReceipt"),
            self_topup=data.get("selfTopup"),
            external_import=data.get("externalImport"),
            billing_info_provided_via_api=data.get("billingInfoProvidedViaAPI"),
            loop_count=data.get("loopCount"),
            rating=data.get("rating"),
            next_action=data.get("nextAction"),
            customer_id=data.get("customerId"),
            merchant_id=data.get("merchantId"),
            shift_id=data.get("shiftId"),
            remittance_id=data.get("remittanceId"),
            attachments=data.get("attachments") or [],
            custom_providers=data.get("customProviders") or [],
            payment_links=data.get("paymentLinks") or [],
            provider_history=data.get("providerHistory") or [],
            history=data.get("history") or [],
            payment_error_history=data.get("paymentErrorHistory") or [],
            signature=data.get("signature"),
            original_signature=data.get("originalSignature"),
            sign_method=sign_method,
            app_version=data.get("appVersion"),
            api_version=data.get("apiVersion"),
            device_id=data.get("deviceId"),
            security_word=data.get("securityWord"),
            local_data=data.get("localData"),
            pnr=data.get("pnr"),
            _raw=data,
        )


@dataclass
class PaginatedResponse:
    count: int
    items: List[Transaction]
    current_page: int
    total_pages: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PaginatedResponse":
        items = [Transaction.from_dict(item) for item in data.get("items", [])]
        return cls(
            count=data.get("count", 0),
            items=items,
            current_page=data.get("currentPage", 1),
            total_pages=data.get("totalPages", 1),
        )


# ---------------------------------------------------------------------------
# Webhook notification payload
# ---------------------------------------------------------------------------

@dataclass
class WebhookEvent:
    """Parsed BML webhook notification body.

    BML POSTs this to your registered URL on transaction changes and
    tokenisation updates.  Two event types exist:

    - ``NOTIFY_TRANSACTION_CHANGE`` - state change (CONFIRMED, CANCELLED, etc.)
    - ``NOTIFY_TOKENISATION_STATUS`` - card stored or tokenisation failed

    Always verify the request first::

        if not client.verify_webhook_headers(request.headers):
            abort(403)
        event = WebhookEvent.from_dict(request.get_json())
    """

    id: Optional[str] = None
    event_type: Optional[WebhookEventType] = None
    transaction_id: Optional[str] = None
    company_id: Optional[str] = None
    customer_id: Optional[str] = None

    # NOTIFY_TRANSACTION_CHANGE fields
    state: Optional[TransactionState] = None
    amount: Optional[int] = None
    amount_fractional: Optional[float] = None
    amount_formatted: Optional[str] = None
    currency: Optional[str] = None
    provider: Optional[str] = None
    local_id: Optional[str] = None
    customer_reference: Optional[str] = None
    security_word: Optional[str] = None
    signature: Optional[str] = None
    original_signature: Optional[str] = None
    qr_code: Optional[QRCode] = None
    external_source: Optional[str] = None

    # NOTIFY_TOKENISATION_STATUS fields
    tokenisation_status: Optional[TokenisationStatus] = None

    # Meta
    notify_url: Optional[str] = None
    response: Optional[Any] = None
    deleted: Optional[bool] = None
    updated_keys: List[str] = field(default_factory=list)
    created: Optional[str] = None
    updated: Optional[str] = None

    _raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebhookEvent":
        event_type: Optional[WebhookEventType] = None
        if raw_et := data.get("eventType"):
            try:
                event_type = WebhookEventType(raw_et)
            except ValueError:
                logger.warning("Unknown webhook event type: %s", raw_et)

        state: Optional[TransactionState] = None
        if raw_state := data.get("state"):
            try:
                state = TransactionState(raw_state)
            except ValueError:
                logger.warning("Unknown transaction state in webhook: %s", raw_state)

        tokenisation_status: Optional[TokenisationStatus] = None
        if raw_ts := data.get("tokenisationStatus"):
            try:
                tokenisation_status = TokenisationStatus(raw_ts)
            except ValueError:
                logger.warning("Unknown tokenisation status: %s", raw_ts)

        qr_code: Optional[QRCode] = None
        if qr_data := (data.get("qrCode") or {}):
            if "url" in qr_data:
                qr_code = QRCode(url=qr_data["url"], image=qr_data.get("image"))

        return cls(
            id=data.get("id"),
            event_type=event_type,
            transaction_id=data.get("transactionId"),
            company_id=data.get("companyId"),
            customer_id=data.get("customerId"),
            state=state,
            amount=data.get("amount"),
            amount_fractional=data.get("amountFractional"),
            amount_formatted=data.get("amountFormatted"),
            currency=data.get("currency"),
            provider=data.get("provider"),
            local_id=data.get("localId"),
            customer_reference=data.get("customerReference"),
            security_word=data.get("securityWord"),
            signature=data.get("signature"),
            original_signature=data.get("originalSignature"),
            qr_code=qr_code,
            external_source=data.get("externalSource"),
            tokenisation_status=tokenisation_status,
            notify_url=data.get("notifyUrl"),
            response=data.get("response"),
            deleted=data.get("deleted"),
            updated_keys=data.get("updatedKeys") or [],
            created=data.get("created") or data.get("createdAt"),
            updated=data.get("updated") or data.get("updatedAt"),
            _raw=data,
        )


# ---------------------------------------------------------------------------
# Webhook registration record
# ---------------------------------------------------------------------------

@dataclass
class Webhook:
    id: Optional[str] = None
    hook_url: Optional[str] = None
    company_id: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Webhook":
        return cls(
            id=data.get("id"),
            hook_url=data.get("hookUrl"),
            company_id=data.get("companyId"),
            created=data.get("created"),
            updated=data.get("updated"),
        )


# ---------------------------------------------------------------------------
# Company / Merchant
# ---------------------------------------------------------------------------

@dataclass
class PaymentProvider:
    value: str
    description: Optional[str] = None
    customer_description: Optional[str] = None
    ecommerce: Optional[bool] = None
    mobile: Optional[bool] = None
    shop_badge: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PaymentProvider":
        return cls(
            value=data.get("value", ""),
            description=data.get("description"),
            customer_description=data.get("customerDescription"),
            ecommerce=data.get("ecommerce"),
            mobile=data.get("mobile"),
            shop_badge=data.get("shopBadge"),
        )


@dataclass
class Company:
    id: Optional[str] = None
    trading_name: Optional[str] = None
    registered_name: Optional[str] = None
    company_number: Optional[str] = None
    vat_number: Optional[str] = None
    review_status: Optional[str] = None
    country: Optional[str] = None
    enabled_currencies: List[str] = field(default_factory=list)
    payment_providers: List[PaymentProvider] = field(default_factory=list)
    created: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Company":
        providers = [
            PaymentProvider.from_dict(p) for p in data.get("paymentProviders", [])
        ]
        return cls(
            id=data.get("id"),
            trading_name=data.get("tradingName"),
            registered_name=data.get("registeredName"),
            company_number=data.get("companyNumber"),
            vat_number=data.get("vatNumber"),
            review_status=data.get("reviewStatus"),
            country=data.get("country"),
            enabled_currencies=data.get("enabledCurrencies", []),
            payment_providers=providers,
            created=data.get("created"),
        )


# ---------------------------------------------------------------------------
# Shop & related
# ---------------------------------------------------------------------------

@dataclass
class Shop:
    id: Optional[str] = None
    name: Optional[str] = None
    reference: Optional[str] = None
    status: Optional[str] = None
    basket_enabled: Optional[bool] = None
    company_id: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    deleted: Optional[bool] = None
    qr_url: Optional[str] = None
    _raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Shop":
        qr = data.get("qr") or {}
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            reference=data.get("reference"),
            status=data.get("status"),
            basket_enabled=data.get("basketEnabled"),
            company_id=data.get("companyId"),
            created=data.get("created"),
            updated=data.get("updated"),
            deleted=data.get("deleted"),
            qr_url=qr.get("url"),
            _raw=data,
        )


@dataclass
class Product:
    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    currency: Optional[str] = None
    sku: Optional[str] = None
    stock: Optional[int] = None
    deleted: Optional[bool] = None
    shop_id: Optional[str] = None
    company_id: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    _raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Product":
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            description=data.get("description"),
            price=data.get("price"),
            currency=data.get("currency"),
            sku=data.get("sku"),
            stock=data.get("stock"),
            deleted=data.get("deleted"),
            shop_id=data.get("shopId"),
            company_id=data.get("companyId"),
            created=data.get("created"),
            updated=data.get("updated"),
            _raw=data,
        )


@dataclass
class Category:
    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    shop_id: Optional[str] = None
    company_id: Optional[str] = None
    deleted: Optional[bool] = None
    created: Optional[str] = None
    updated: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Category":
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            description=data.get("description"),
            shop_id=data.get("shopId"),
            company_id=data.get("companyId"),
            deleted=data.get("deleted"),
            created=data.get("created"),
            updated=data.get("updated"),
        )


@dataclass
class Tax:
    id: Optional[str] = None
    name: Optional[str] = None
    code: Optional[str] = None
    percentage: Optional[float] = None
    apply_on: Optional[str] = None
    shop_id: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Tax":
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            code=data.get("code"),
            percentage=data.get("percentage"),
            apply_on=data.get("applyOn"),
            shop_id=data.get("shopId"),
            created=data.get("created"),
            updated=data.get("updated"),
        )


@dataclass
class OrderField:
    id: Optional[str] = None
    label: Optional[str] = None
    type: Optional[str] = None
    checked: Optional[bool] = None
    can_delete: Optional[bool] = None
    shop_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderField":
        return cls(
            id=data.get("id"),
            label=data.get("label"),
            type=data.get("type"),
            checked=data.get("checked"),
            can_delete=data.get("canDelete"),
            shop_id=data.get("shopId"),
        )


@dataclass
class CustomFee:
    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    fee: Optional[int] = None
    slug: Optional[str] = None
    shop_id: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CustomFee":
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            description=data.get("description"),
            fee=data.get("fee"),
            slug=data.get("slug"),
            shop_id=data.get("shopId"),
            created=data.get("created"),
            updated=data.get("updated"),
        )


# ---------------------------------------------------------------------------
# Customer & Tokens (Card-On-File)
# ---------------------------------------------------------------------------

@dataclass
class Customer:
    id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    billing_email: Optional[str] = None
    billing_address1: Optional[str] = None
    billing_address2: Optional[str] = None
    billing_city: Optional[str] = None
    billing_country: Optional[str] = None
    billing_post_code: Optional[str] = None
    currency: Optional[str] = None
    company_id: Optional[str] = None
    customer_group_id: Optional[str] = None
    tax_id: Optional[str] = None
    deleted: Optional[bool] = None
    created: Optional[str] = None
    updated: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Customer":
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            email=data.get("email"),
            billing_email=data.get("billingEmail"),
            billing_address1=data.get("billingAddress1"),
            billing_address2=data.get("billingAddress2"),
            billing_city=data.get("billingCity"),
            billing_country=data.get("billingCountry"),
            billing_post_code=data.get("billingPostCode"),
            currency=data.get("currency"),
            company_id=data.get("companyId"),
            customer_group_id=data.get("customerGroupId"),
            tax_id=data.get("taxId"),
            deleted=data.get("deleted"),
            created=data.get("created") or data.get("createdAt"),
            updated=data.get("updated") or data.get("updatedAt"),
        )


@dataclass
class CustomerToken:
    """A stored card-on-file token linked to a Customer.

    Only ``mpgs`` and ``debit_credit_card`` providers support tokenisation.
    Pass ``id`` as ``tokenId`` or ``token`` as ``token`` to
    :meth:`.CustomersResource.charge`.
    """
    id: Optional[str] = None
    brand: Optional[str] = None
    provider: Optional[str] = None
    token: Optional[str] = None
    token_type: Optional[str] = None
    token_provider: Optional[str] = None
    token_agreement_id: Optional[str] = None
    token_agreement_type: Optional[str] = None
    token_expiry_month: Optional[str] = None
    token_expiry_year: Optional[str] = None
    padded_card_number: Optional[str] = None
    customer_id: Optional[str] = None
    company_id: Optional[str] = None
    default_token: Optional[bool] = None
    deleted: Optional[bool] = None
    created: Optional[str] = None
    updated: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CustomerToken":
        return cls(
            id=data.get("id") or data.get("_id"),
            brand=data.get("brand"),
            provider=data.get("provider"),
            token=data.get("token"),
            token_type=data.get("tokenType"),
            token_provider=data.get("tokenProvider"),
            token_agreement_id=data.get("tokenAgreementId"),
            token_agreement_type=data.get("tokenAgreementType"),
            token_expiry_month=data.get("tokenExpiryMonth"),
            token_expiry_year=data.get("tokenExpiryYear"),
            padded_card_number=data.get("paddedCardNumber"),
            customer_id=data.get("customerId"),
            company_id=data.get("companyId"),
            default_token=data.get("defaultToken"),
            deleted=data.get("deleted"),
            created=data.get("created") or data.get("createdAt"),
            updated=data.get("updated") or data.get("updatedAt"),
        )


# ---------------------------------------------------------------------------
# PCI Merchant Tokenization models
# ---------------------------------------------------------------------------

@dataclass
class TokensPublicKey:
    """RSA public key for encrypting card data on the client side.

    Fetched from ``GET /public-client/tokens-public-key`` using your
    **public** application key (``pk_...``).

    .. warning::
        This key can be rotated at any time.  Always fetch the latest version
        immediately before encrypting - never cache it long-term.
    """
    key_id: str = ""
    public_key: str = ""    # SPKI PEM-formatted RSA public key

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokensPublicKey":
        return cls(
            key_id=data.get("keyId", ""),
            public_key=data.get("publicKey", ""),
        )

    @property
    def pem(self) -> str:
        """Return the key as a proper PEM block (adds header/footer if missing)."""
        pk = self.public_key.strip()
        if pk.startswith("-----"):
            return pk
        return f"-----BEGIN PUBLIC KEY-----\n{pk}\n-----END PUBLIC KEY-----"


@dataclass
class ClientTokenNextAction:
    """Next-action object returned after submitting encrypted card data."""
    url: str = ""
    client_side_token_id: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClientTokenNextAction":
        return cls(
            url=data.get("url", ""),
            client_side_token_id=data.get("clientSideTokenId", ""),
        )


@dataclass
class ClientTokenResponse:
    """Response from ``POST /public-client/tokens``.

    Redirect the customer to ``next_action.url`` for 3DS authentication.
    After success BML redirects back to your ``redirect`` URL with
    ``tokenId`` (Customer Token ID) as a query parameter - that is what
    you use for charging.

    ``next_action.client_side_token_id`` is **not** a payment token.
    """
    next_action: Optional[ClientTokenNextAction] = None
    _raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClientTokenResponse":
        next_action = None
        if na := data.get("nextAction"):
            next_action = ClientTokenNextAction.from_dict(na)
        return cls(next_action=next_action, _raw=data)


__all__ = [
    # Enums
    "Environment",
    "TransactionState",
    "Provider",
    "WebhookEventType",
    "TokenisationStatus",
    "SignMethod",
    # Transaction
    "QRCode",
    "Transaction",
    "PaginatedResponse",
    # Webhook
    "WebhookEvent",
    "Webhook",
    # Company
    "PaymentProvider",
    "Company",
    # Shop
    "Shop",
    "Product",
    "Category",
    "Tax",
    "OrderField",
    "CustomFee",
    # Customers
    "Customer",
    "CustomerToken",
    # PCI Tokenization
    "TokensPublicKey",
    "ClientTokenNextAction",
    "ClientTokenResponse",
]