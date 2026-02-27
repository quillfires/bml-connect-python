"""
BML Connect Python SDK
======================

Robust Python SDK for Bank of Maldives Connect API with comprehensive sync/async support.
"""

import base64
import hashlib
import hmac
import json
import logging
import uuid
from dataclasses import dataclass
from enum import Enum
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Dict, List, Optional, Union

import aiohttp
import requests

logger = logging.getLogger("bml_connect")
logger.addHandler(logging.NullHandler())

try:
    SDK_VERSION = version("bml-connect-python")
except PackageNotFoundError:
    SDK_VERSION = "unknown"

USER_AGENT = f"BML-Connect-Python/{SDK_VERSION}"


class Environment(Enum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"

    @property
    def base_url(self) -> str:
        return {
            Environment.SANDBOX: "https://api.uat.merchants.bankofmaldives.com.mv/public",
            Environment.PRODUCTION: "https://api.merchants.bankofmaldives.com.mv/public",
        }[self]


class SignMethod(Enum):
    SHA1 = "sha1"
    MD5 = "md5"

    @classmethod
    def _missing_(cls, value: object) -> "SignMethod":
        if isinstance(value, str):
            normalized = value.lower()
            for member in cls:
                if member.value == normalized:
                    return member
        return cls.SHA1  # Default to SHA1


class TransactionState(Enum):
    CREATED = "CREATED"
    QR_CODE_GENERATED = "QR_CODE_GENERATED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    REFUND_REQUESTED = "REFUND_REQUESTED"
    REFUNDED = "REFUNDED"


@dataclass
class QRCode:
    url: str
    image: Optional[str] = None  # Base64 encoded image if available


@dataclass
class Transaction:
    transaction_id: Optional[str] = None
    local_id: Optional[str] = None
    customer_reference: Optional[str] = None
    amount: Optional[int] = None
    currency: Optional[str] = None
    provider: Optional[str] = None
    state: Optional[TransactionState] = None
    created: Optional[str] = None
    signature: Optional[str] = None
    url: Optional[str] = None
    qr_code: Optional[QRCode] = None
    redirect_url: Optional[str] = None
    app_version: Optional[str] = None
    api_version: Optional[str] = None
    device_id: Optional[str] = None
    sign_method: Optional[SignMethod] = None
    expires_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transaction":
        qr_code = None
        qr_data = data.get("qrCode", {})
        if qr_data and "url" in qr_data:
            qr_code = QRCode(url=qr_data["url"], image=qr_data.get("image"))

        state = None
        if "state" in data:
            try:
                state = TransactionState(data["state"])
            except ValueError:
                logger.warning("Unknown transaction state: %s", data["state"])
                state = None

        sign_method = None
        if "signMethod" in data:
            try:
                sign_method = SignMethod(data["signMethod"])
            except ValueError:
                logger.warning("Unknown sign method: %s", data["signMethod"])
                sign_method = None

        return cls(
            transaction_id=data.get("transactionId"),
            local_id=data.get("localId"),
            customer_reference=data.get("customerReference"),
            amount=data.get("amount"),
            currency=data.get("currency"),
            provider=data.get("provider"),
            state=state,
            created=data.get("created"),
            signature=data.get("signature"),
            url=data.get("url"),
            qr_code=qr_code,
            redirect_url=data.get("redirectUrl"),
            app_version=data.get("appVersion"),
            api_version=data.get("apiVersion"),
            device_id=data.get("deviceId"),
            sign_method=sign_method,
            expires_at=data.get("expiresAt"),
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


class BMLConnectError(Exception):
    """Base exception for BML Connect errors"""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class AuthenticationError(BMLConnectError):
    pass


class ValidationError(BMLConnectError):
    pass


class NotFoundError(BMLConnectError):
    pass


class ServerError(BMLConnectError):
    pass


class RateLimitError(BMLConnectError):
    pass


class SignatureUtils:
    @staticmethod
    def generate_signature(
        data: Dict[str, Any],
        api_key: str,
        method: Union[SignMethod, str] = SignMethod.SHA1,
    ) -> str:
        """Generate signature with proper key sorting and encoding"""
        if isinstance(method, str):
            original_value = method
            try:
                method = SignMethod(method)
            except ValueError:
                logger.warning("Invalid sign method '%s', defaulting to SHA1", original_value)
                method = SignMethod.SHA1

        amount = data.get("amount")
        currency = data.get("currency")

        if amount is None or not currency:
            raise ValueError(
                "Amount and currency are required for signature generation"
            )

        signature_string = f"amount={amount}&currency={currency}&apiKey={api_key}"

        if method == SignMethod.SHA1:
            return hashlib.sha1(signature_string.encode("utf-8")).hexdigest()
        elif method == SignMethod.MD5:
            return base64.b64encode(
                hashlib.md5(signature_string.encode("utf-8")).digest()
            ).decode("utf-8")
        else:
            raise ValueError(f"Unsupported signature method: {method}")

    @staticmethod
    def verify_signature(
        data: Dict[str, Any],
        signature: str,
        api_key: str,
        method: Union[SignMethod, str] = SignMethod.SHA1,
    ) -> bool:
        """Secure signature verification with constant-time comparison"""
        expected = SignatureUtils.generate_signature(data, api_key, method)
        return hmac.compare_digest(expected, signature)


class BaseClient:
    def __init__(
        self,
        api_key: str,
        app_id: str,
        environment: Environment = Environment.PRODUCTION,
        timeout: int = 30,
    ):
        self.api_key = api_key
        self.app_id = app_id
        self.environment = environment
        self.base_url = environment.base_url
        self.timeout = timeout
        self.session: Optional[Union[requests.Session, aiohttp.ClientSession]] = None
        logger.info("Initialized BML Client for %s environment", environment.name)

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "X-App-Id": self.app_id,
        }

    def _prepare_transaction_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare transaction data with required defaults"""
        prepared = data.copy()
        prepared.setdefault("apiVersion", "2.0")
        prepared.setdefault("signMethod", "sha1")
        prepared.setdefault("appVersion", USER_AGENT)
        prepared.setdefault("deviceId", str(uuid.uuid4()))
        return prepared

    def _handle_response(
        self,
        response: Union[requests.Response, aiohttp.ClientResponse],
        response_data: Dict[str, Any],
    ) -> None:
        """Handle API response with proper error mapping"""
        status_code = (
            response.status
            if isinstance(response, aiohttp.ClientResponse)
            else response.status_code
        )
        message = response_data.get("message", "Unknown error")
        code = response_data.get("code")

        logger.debug("API Response: %s - %s (code: %s)", status_code, message, code)

        if status_code == 400:
            raise ValidationError(message, code, status_code)
        elif status_code == 401:
            raise AuthenticationError(message, code, status_code)
        elif status_code == 404:
            raise NotFoundError(message, code, status_code)
        elif status_code == 429:
            raise RateLimitError(message, code, status_code)
        elif status_code >= 500:
            raise ServerError(message, code, status_code)
        elif status_code >= 400:
            raise BMLConnectError(message, code, status_code)


class SyncClient(BaseClient):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.session: requests.Session = requests.Session()
        self.session.headers.update(self._get_headers())
        logger.debug("Initialized synchronous HTTP session")

    def __enter__(self) -> "SyncClient":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        logger.debug("Request: %s %s %s", method, url, kwargs.get("params"))

        try:
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)

            try:
                response_data: Dict[str, Any] = response.json()
            except json.JSONDecodeError:
                logger.error("Invalid JSON response: %s", response.text[:500])
                raise ServerError(
                    "Invalid JSON response", status_code=response.status_code
                )

            logger.debug("Response: %s - %s", response.status_code, response_data)

            if not response.ok:
                self._handle_response(response, response_data)

            return response_data
        except requests.exceptions.RequestException as e:
            logger.error("Network error: %s", str(e))
            raise BMLConnectError(f"Network error: {str(e)}")

    def create_transaction(self, data: Dict[str, Any]) -> Transaction:
        logger.info("Creating new transaction")
        data = self._prepare_transaction_data(data)

        try:
            sign_method = SignMethod(data.get("signMethod", "sha1"))
        except ValueError:
            sign_method = SignMethod.SHA1
            logger.warning("Invalid sign method, defaulting to SHA1")

        data["signature"] = SignatureUtils.generate_signature(
            data, self.api_key, sign_method
        )

        response = self._request("POST", "/transactions", json=data)
        return Transaction.from_dict(response)

    def get_transaction(self, transaction_id: str) -> Transaction:
        logger.info("Fetching transaction: %s", transaction_id)
        response = self._request("GET", f"/transactions/{transaction_id}")
        return Transaction.from_dict(response)

    def cancel_transaction(self, transaction_id: str) -> Transaction:
        """Cancel a transaction by ID"""
        logger.info("Cancelling transaction: %s", transaction_id)
        response = self._request("DELETE", f"/transactions/{transaction_id}")
        return Transaction.from_dict(response)

    def list_transactions(
        self,
        page: int = 1,
        per_page: int = 20,
        state: Optional[str] = None,
        provider: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> PaginatedResponse:
        logger.info("Listing transactions: page=%s, per_page=%s", page, per_page)
        params: Dict[str, Any] = {"page": page, "perPage": per_page}

        # FIX: Use `is not None` so that an explicit empty string isn't silently dropped
        if state is not None:
            params["state"] = state
        if provider is not None:
            params["provider"] = provider
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date

        response = self._request("GET", "/transactions", params=params)
        return PaginatedResponse.from_dict(response)

    def close(self) -> None:
        """Close the HTTP session"""
        if self.session:
            self.session.close()
            logger.debug("Closed synchronous HTTP session")


class AsyncClient(BaseClient):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._session: Optional[aiohttp.ClientSession] = None
        logger.debug("Initialized asynchronous client (session deferred)")

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    def _get_session(self) -> aiohttp.ClientSession:
        """Lazily create the aiohttp session within an async context"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            )
            logger.debug("Created asynchronous HTTP session")
        return self._session

    async def _request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        logger.debug("Async Request: %s %s %s", method, url, kwargs.get("params"))

        session = self._get_session()
        try:
            async with session.request(method, url, **kwargs) as response:
                try:
                    response_data: Dict[str, Any] = await response.json()
                except aiohttp.ContentTypeError:
                    text = await response.text()
                    logger.error("Invalid JSON response: %s", text[:500])
                    raise ServerError(
                        f"Invalid JSON: {text[:200]}", status_code=response.status
                    )

                logger.debug("Async Response: %s - %s", response.status, response_data)

                if not response.ok:
                    self._handle_response(response, response_data)

                return response_data
        except aiohttp.ClientError as e:
            logger.error("Network error: %s", str(e))
            raise BMLConnectError(f"Network error: {str(e)}")

    async def create_transaction(self, data: Dict[str, Any]) -> Transaction:
        logger.info("Creating new transaction (async)")
        data = self._prepare_transaction_data(data)

        try:
            sign_method = SignMethod(data.get("signMethod", "sha1"))
        except ValueError:
            sign_method = SignMethod.SHA1
            logger.warning("Invalid sign method, defaulting to SHA1")

        data["signature"] = SignatureUtils.generate_signature(
            data, self.api_key, sign_method
        )

        response = await self._request("POST", "/transactions", json=data)
        return Transaction.from_dict(response)

    async def get_transaction(self, transaction_id: str) -> Transaction:
        logger.info("Fetching transaction (async): %s", transaction_id)
        response = await self._request("GET", f"/transactions/{transaction_id}")
        return Transaction.from_dict(response)

    async def cancel_transaction(self, transaction_id: str) -> Transaction:
        """Cancel a transaction by ID"""
        logger.info("Cancelling transaction (async): %s", transaction_id)
        response = await self._request("DELETE", f"/transactions/{transaction_id}")
        return Transaction.from_dict(response)

    async def list_transactions(
        self,
        page: int = 1,
        per_page: int = 20,
        state: Optional[str] = None,
        provider: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> PaginatedResponse:
        logger.info(
            "Listing transactions (async): page=%s, per_page=%s", page, per_page
        )
        params: Dict[str, Any] = {"page": page, "perPage": per_page}

        # FIX: Use `is not None` so that an explicit empty string isn't silently dropped
        if state is not None:
            params["state"] = state
        if provider is not None:
            params["provider"] = provider
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date

        response = await self._request("GET", "/transactions", params=params)
        return PaginatedResponse.from_dict(response)

    async def close(self) -> None:
        """Close the HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("Closed asynchronous HTTP session")


class BMLConnect:
    def __init__(
        self,
        api_key: str,
        app_id: str,
        environment: Union[Environment, str] = Environment.PRODUCTION,
        async_mode: bool = False,
        timeout: int = 30,
    ):
        """
        Initialize BML Connect client

        Args:
            api_key: Your API key from BML merchant portal
            app_id: Your application ID from BML merchant portal
            environment: 'production' or 'sandbox' (default: production)
            async_mode: Whether to use async operations (default: False)
            timeout: Request timeout in seconds (default: 30)
        """
        self.api_key = api_key
        self.app_id = app_id

        if isinstance(environment, str):
            try:
                self.environment = Environment[environment.upper()]
            except KeyError:
                raise ValueError(
                    f"Invalid environment: {environment}. Use 'production' or 'sandbox'"
                )
        else:
            self.environment = environment

        self.async_mode = async_mode
        self.client: Union[SyncClient, AsyncClient]

        if async_mode:
            self.client = AsyncClient(api_key, app_id, self.environment, timeout)
        else:
            self.client = SyncClient(api_key, app_id, self.environment, timeout)

    def __enter__(self) -> "BMLConnect":
        if isinstance(self.client, AsyncClient):
            raise TypeError(
                "Use 'async with' for async_mode=True clients"
            )
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    async def __aenter__(self) -> "BMLConnect":
        if isinstance(self.client, SyncClient):
            raise TypeError(
                "Use 'with' (not 'async with') for async_mode=False clients"
            )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.aclose()

    @property
    def transactions(self) -> Union[SyncClient, AsyncClient]:
        return self.client

    def verify_webhook_signature(
        self,
        payload: Union[Dict[str, Any], str],
        signature: str,
        method: Union[SignMethod, str] = SignMethod.SHA1,
    ) -> bool:
        """
        Verify webhook signature for data integrity

        Args:
            payload: Webhook payload data (dict or JSON string)
            signature: Received signature to verify
            method: Signature method (default: SHA1)

        Returns:
            bool: True if signature is valid, False otherwise
        """
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                raise ValidationError("Invalid JSON payload")

        if not isinstance(payload, dict):
            raise ValidationError("Payload must be a JSON object")

        verification_payload = payload.copy()
        if "signature" in verification_payload:
            del verification_payload["signature"]

        return SignatureUtils.verify_signature(
            verification_payload, signature, self.api_key, method
        )

    def close(self) -> None:
        """Clean up resources (synchronous)"""
        if isinstance(self.client, SyncClient):
            self.client.close()

    async def aclose(self) -> None:
        """Clean up resources (asynchronous)"""
        if isinstance(self.client, AsyncClient):
            await self.client.close()


__all__ = [
    "BMLConnect",
    "Transaction",
    "QRCode",
    "PaginatedResponse",
    "Environment",
    "SignMethod",
    "TransactionState",
    "BMLConnectError",
    "AuthenticationError",
    "ValidationError",
    "NotFoundError",
    "ServerError",
    "RateLimitError",
    "SignatureUtils",
]