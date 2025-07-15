"""
BML Connect Python SDK
======================

Robust Python SDK for Bank of Maldives Connect API with comprehensive sync/async support.
"""

import hashlib
import hmac
import base64
import json
import uuid
from typing import Optional, Dict, Any, Union, List
from urllib.parse import urlencode
import requests
import aiohttp
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger("bml_connect")
logger.addHandler(logging.NullHandler())

SDK_VERSION = "1.1.0"
USER_AGENT = f"BML-Connect-Python/{SDK_VERSION}"


class Environment(Enum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"
    
    @property
    def base_url(self) -> str:
        return {
            Environment.SANDBOX: "https://api.uat.merchants.bankofmaldives.com.mv/public",
            Environment.PRODUCTION: "https://api.merchants.bankofmaldives.com.mv/public"
        }[self]


class SignMethod(Enum):
    SHA1 = "sha1"
    MD5 = "md5"
    
    @classmethod
    def _missing_(cls, value: str) -> 'SignMethod':
        value = value.lower()
        for member in cls:
            if member.value == value:
                return member
        return cls.SHA1  # Default to SHA1


class TransactionState(Enum):
    CREATED = "CREATED"
    QR_CODE_GENERATED = "QR_CODE_GENERATED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


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
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        qr_code = None
        qr_data = data.get('qrCode', {})
        if qr_data and 'url' in qr_data:
            qr_code = QRCode(
                url=qr_data['url'],
                image=qr_data.get('image')
            )
        
        # Parse state enum
        state = None
        if 'state' in data:
            try:
                state = TransactionState(data['state'])
            except ValueError:
                logger.warning(f"Unknown transaction state: {data['state']}")
                state = None
        
        # Parse sign method enum
        sign_method = None
        if 'signMethod' in data:
            try:
                sign_method = SignMethod(data['signMethod'])
            except ValueError:
                logger.warning(f"Unknown sign method: {data['signMethod']}")
                sign_method = None
        
        return cls(
            transaction_id=data.get('transactionId'),
            local_id=data.get('localId'),
            customer_reference=data.get('customerReference'),
            amount=data.get('amount'),
            currency=data.get('currency'),
            provider=data.get('provider'),
            state=state,
            created=data.get('created'),
            signature=data.get('signature'),
            url=data.get('url'),
            qr_code=qr_code,
            redirect_url=data.get('redirectUrl'),
            app_version=data.get('appVersion'),
            api_version=data.get('apiVersion'),
            device_id=data.get('deviceId'),
            sign_method=sign_method,
            expires_at=data.get('expiresAt')
        )


@dataclass
class PaginatedResponse:
    count: int
    items: List[Transaction]
    current_page: int
    total_pages: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PaginatedResponse':
        items = [Transaction.from_dict(item) for item in data.get('items', [])]
        return cls(
            count=data.get('count', 0),
            items=items,
            current_page=data.get('currentPage', 1),
            total_pages=data.get('totalPages', 1)
        )


class BMLConnectError(Exception):
    """Base exception for BML Connect errors"""
    def __init__(self, message: str, code: Optional[str] = None, status_code: Optional[int] = None):
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
    def generate_signature(data: Dict[str, Any], api_key: str, method: Union[SignMethod, str] = SignMethod.SHA1) -> str:
        """Generate signature with proper key sorting and encoding"""
        if isinstance(method, str):
            try:
                method = SignMethod(method)
            except ValueError:
                method = SignMethod.SHA1
                logger.warning(f"Invalid sign method '{method}', defaulting to SHA1")
        
        amount = data.get('amount')
        currency = data.get('currency')
        
        if not amount or not currency:
            raise ValueError("Amount and currency are required for signature generation")
        
        signature_string = f"amount={amount}&currency={currency}&apiKey={api_key}"
        
        if method == SignMethod.SHA1:
            return hashlib.sha1(signature_string.encode('utf-8')).hexdigest()
        elif method == SignMethod.MD5:
            return base64.b64encode(hashlib.md5(signature_string.encode('utf-8')).digest()).decode('utf-8')
        else:
            raise ValueError(f"Unsupported signature method: {method}")

    @staticmethod
    def verify_signature(data: Dict[str, Any], signature: str, api_key: str, method: Union[SignMethod, str] = SignMethod.SHA1) -> bool:
        """Secure signature verification with constant-time comparison"""
        expected = SignatureUtils.generate_signature(data, api_key, method)
        return hmac.compare_digest(expected, signature)


class BaseClient:
    def __init__(self, api_key: str, app_id: str, environment: Environment = Environment.PRODUCTION):
        self.api_key = api_key
        self.app_id = app_id
        self.environment = environment
        self.base_url = environment.base_url
        self.session = None  # Will be set in child classes
        logger.info(f"Initialized BML Client for {environment.name} environment")

    def _get_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f"{self.api_key}",
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': USER_AGENT,
            'X-App-Id': self.app_id
        }

    def _prepare_transaction_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare transaction data with required defaults"""
        prepared = data.copy()
        prepared.setdefault('apiVersion', '2.0')
        prepared.setdefault('signMethod', 'sha1')
        prepared.setdefault('appVersion', USER_AGENT)
        prepared.setdefault('deviceId', str(uuid.uuid4()))
        return prepared

    def _handle_response(self, response: Union[requests.Response, aiohttp.ClientResponse], response_data: Dict[str, Any]):
        """Handle API response with proper error mapping"""
        status_code = response.status if isinstance(response, aiohttp.ClientResponse) else response.status_code
        message = response_data.get('message', 'Unknown error')
        code = response_data.get('code')
        
        logger.debug(f"API Response: {status_code} - {message}")
        
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = requests.Session()
        self.session.headers.update(self._get_headers())
        logger.debug("Initialized synchronous HTTP session")

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"Request: {method} {url} {kwargs.get('params')}")
        
        try:
            response = self.session.request(
                method,
                url,
                timeout=30,
                **kwargs
            )
            
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response: {response.text[:500]}")
                raise ServerError("Invalid JSON response", status_code=response.status_code)
            
            logger.debug(f"Response: {response.status_code} - {response_data}")
            
            if not response.ok:
                self._handle_response(response, response_data)
                
            return response_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {str(e)}")
            raise BMLConnectError(f"Network error: {str(e)}")

    def create_transaction(self, data: Dict[str, Any]) -> Transaction:
        logger.info("Creating new transaction")
        data = self._prepare_transaction_data(data)
        
        try:
            sign_method = SignMethod(data.get('signMethod', 'sha1'))
        except ValueError:
            sign_method = SignMethod.SHA1
            logger.warning(f"Invalid sign method, defaulting to SHA1")
        
        data['signature'] = SignatureUtils.generate_signature(data, self.api_key, sign_method)
        
        response = self._request('POST', '/transactions', json=data)
        return Transaction.from_dict(response)

    def get_transaction(self, transaction_id: str) -> Transaction:
        logger.info(f"Fetching transaction: {transaction_id}")
        response = self._request('GET', f'/transactions/{transaction_id}')
        return Transaction.from_dict(response)

    def list_transactions(
        self, 
        page: int = 1, 
        per_page: int = 20,
        state: Optional[str] = None,
        provider: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> PaginatedResponse:
        logger.info(f"Listing transactions: page={page}, per_page={per_page}")
        params = {'page': page, 'perPage': per_page}
        
        # Add filters
        if state:
            params['state'] = state
        if provider:
            params['provider'] = provider
        if start_date:
            params['startDate'] = start_date
        if end_date:
            params['endDate'] = end_date
        
        response = self._request('GET', '/transactions', params=params)
        return PaginatedResponse.from_dict(response)
    
    def close(self):
        """Close the HTTP session"""
        if self.session:
            self.session.close()
            logger.debug("Closed synchronous HTTP session")


class AsyncClient(BaseClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = aiohttp.ClientSession(
            headers=self._get_headers(),
            timeout=aiohttp.ClientTimeout(total=30)
        )
        logger.debug("Initialized asynchronous HTTP session")

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"Async Request: {method} {url} {kwargs.get('params')}")
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                try:
                    response_data = await response.json()
                except aiohttp.ContentTypeError:
                    text = await response.text()
                    logger.error(f"Invalid JSON response: {text[:500]}")
                    raise ServerError(f"Invalid JSON: {text[:200]}", status_code=response.status)
                
                logger.debug(f"Async Response: {response.status} - {response_data}")
                
                if not response.ok:
                    self._handle_response(response, response_data)
                    
                return response_data
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {str(e)}")
            raise BMLConnectError(f"Network error: {str(e)}")

    async def create_transaction(self, data: Dict[str, Any]) -> Transaction:
        logger.info("Creating new transaction (async)")
        data = self._prepare_transaction_data(data)
        
        try:
            sign_method = SignMethod(data.get('signMethod', 'sha1'))
        except ValueError:
            sign_method = SignMethod.SHA1
            logger.warning(f"Invalid sign method, defaulting to SHA1")
        
        data['signature'] = SignatureUtils.generate_signature(data, self.api_key, sign_method)
        
        response = await self._request('POST', '/transactions', json=data)
        return Transaction.from_dict(response)

    async def get_transaction(self, transaction_id: str) -> Transaction:
        logger.info(f"Fetching transaction (async): {transaction_id}")
        response = await self._request('GET', f'/transactions/{transaction_id}')
        return Transaction.from_dict(response)

    async def list_transactions(
        self, 
        page: int = 1, 
        per_page: int = 20,
        state: Optional[str] = None,
        provider: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> PaginatedResponse:
        logger.info(f"Listing transactions (async): page={page}, per_page={per_page}")
        params = {'page': page, 'perPage': per_page}
        
        # Add filters
        if state:
            params['state'] = state
        if provider:
            params['provider'] = provider
        if start_date:
            params['startDate'] = start_date
        if end_date:
            params['endDate'] = end_date
        
        response = await self._request('GET', '/transactions', params=params)
        return PaginatedResponse.from_dict(response)
    
    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug("Closed asynchronous HTTP session")


class BMLConnect:
    def __init__(
        self,
        api_key: str,
        app_id: str,
        environment: Union[Environment, str] = Environment.PRODUCTION,
        async_mode: bool = False
    ):
        """
        Initialize BML Connect client
        
        Args:
            api_key: Your API key from BML merchant portal
            app_id: Your application ID from BML merchant portal
            environment: 'production' or 'sandbox' (default: production)
            async_mode: Whether to use async operations (default: False)
        """
        self.api_key = api_key
        self.app_id = app_id
        
        if isinstance(environment, str):
            try:
                self.environment = Environment[environment.upper()]
            except KeyError:
                raise ValueError(f"Invalid environment: {environment}. Use 'production' or 'sandbox'")
        else:
            self.environment = environment
            
        self.async_mode = async_mode
        
        if async_mode:
            self.client = AsyncClient(api_key, app_id, self.environment)
        else:
            self.client = SyncClient(api_key, app_id, self.environment)
    
    @property
    def transactions(self):
        return self.client

    def verify_webhook_signature(
        self,
        payload: Union[Dict[str, Any], str],
        signature: str,
        method: Union[SignMethod, str] = SignMethod.SHA1
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
                
        # Create a copy and remove signature if present
        verification_payload = payload.copy()
        if 'signature' in verification_payload:
            del verification_payload['signature']
            
        return SignatureUtils.verify_signature(verification_payload, signature, self.api_key, method)
    
    def close(self):
        """Clean up resources (synchronous)"""
        if not self.async_mode and hasattr(self.client, 'close'):
            self.client.close()
    
    async def aclose(self):
        """Clean up resources (asynchronous)"""
        if self.async_mode and hasattr(self.client, 'close'):
            await self.client.close()


__all__ = [
    'BMLConnect',
    'Transaction',
    'QRCode',
    'PaginatedResponse',
    'Environment',
    'SignMethod',
    'TransactionState',
    'BMLConnectError',
    'AuthenticationError',
    'ValidationError',
    'NotFoundError',
    'ServerError',
    'RateLimitError',
    'SignatureUtils'
]