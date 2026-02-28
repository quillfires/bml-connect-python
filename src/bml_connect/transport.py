"""
BML Connect SDK - HTTP Transport
=================================

Low-level HTTP layer shared by sync and async clients.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

import aiohttp
import requests

from .exceptions import (
    AuthenticationError,
    BMLConnectError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from .models import Environment

logger = logging.getLogger("bml_connect")

try:
    from importlib.metadata import PackageNotFoundError, version

    try:
        _SDK_VERSION = version("bml-connect-python")
    except PackageNotFoundError:
        _SDK_VERSION = "unknown"
except ImportError:
    _SDK_VERSION = "unknown"

USER_AGENT = f"BML-Connect-Python/{_SDK_VERSION}"


def _raise_for_status(status_code: int, data: Dict[str, Any]) -> None:
    message = data.get("message", "Unknown error")
    code = data.get("code")
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


class _BaseTransport:
    def __init__(self, api_key: str, environment: Environment) -> None:
        self.api_key = api_key
        self.base_url = environment.base_url

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        }


class SyncTransport(_BaseTransport):
    """Synchronous HTTP transport (uses ``requests``)."""

    def __init__(self, api_key: str, environment: Environment) -> None:
        super().__init__(api_key, environment)
        self._session = requests.Session()
        self._session.headers.update(self._headers())

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Any] = None,
        files: Optional[Any] = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        logger.debug("→ %s %s params=%s", method, url, params)
        try:
            resp = self._session.request(
                method,
                url,
                params=params,
                json=json_body,
                files=files,
                timeout=30,
            )
        except requests.exceptions.RequestException as exc:
            logger.error("Network error: %s", exc)
            raise BMLConnectError(f"Network error: {exc}") from exc

        if resp.status_code == 204:
            return None

        try:
            data: Any = resp.json()
        except json.JSONDecodeError:
            logger.error(
                "Non-JSON response (%s): %s", resp.status_code, resp.text[:500]
            )
            if not resp.ok:
                raise ServerError("Invalid JSON response", status_code=resp.status_code)
            return {}

        logger.debug("← %s %s", resp.status_code, str(data)[:200])
        if not resp.ok:
            _raise_for_status(resp.status_code, data if isinstance(data, dict) else {})

        return data

    def close(self) -> None:
        self._session.close()


class AsyncTransport(_BaseTransport):
    """Asynchronous HTTP transport (uses ``aiohttp``)."""

    def __init__(self, api_key: str, environment: Environment) -> None:
        super().__init__(api_key, environment)
        self._session = aiohttp.ClientSession(
            headers=self._headers(),
            timeout=aiohttp.ClientTimeout(total=30),
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Any] = None,
        data: Optional[Any] = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        logger.debug("→ %s %s params=%s", method, url, params)
        try:
            async with self._session.request(
                method, url, params=params, json=json_body, data=data
            ) as resp:
                if resp.status == 204:
                    return None
                try:
                    resp_data: Any = await resp.json(content_type=None)
                except (aiohttp.ContentTypeError, json.JSONDecodeError):
                    text = await resp.text()
                    logger.error("Non-JSON response (%s): %s", resp.status, text[:500])
                    if not resp.ok:
                        raise ServerError(
                            f"Invalid JSON: {text[:200]}", status_code=resp.status
                        )
                    return {}

                logger.debug("← %s %s", resp.status, str(resp_data)[:200])
                if not resp.ok:
                    _raise_for_status(
                        resp.status,
                        resp_data if isinstance(resp_data, dict) else {},
                    )
                return resp_data
        except aiohttp.ClientError as exc:
            logger.error("Network error: %s", exc)
            raise BMLConnectError(f"Network error: {exc}") from exc

    async def close(self) -> None:
        if not self._session.closed:
            await self._session.close()


__all__ = ["SyncTransport", "AsyncTransport", "USER_AGENT"]
