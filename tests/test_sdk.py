import pytest
import asyncio
from bml_connect import BMLConnect, Environment, SignatureUtils, BMLConnectError


def test_webhook_signature_verification():
    api_key = "testkey"
    payload = {"amount": 1000, "currency": "MVR", "localId": "order_1"}
    signature = SignatureUtils.generate_signature(payload, api_key)
    assert SignatureUtils.verify_signature(payload, signature, api_key)


def test_invalid_environment():
    with pytest.raises(ValueError):
        BMLConnect(api_key="test", app_id="test", environment="invalid")

@pytest.mark.asyncio
async def test_async_client_creation():
    client = BMLConnect(api_key="test", app_id="test", environment=Environment.SANDBOX, async_mode=True)
    assert client.async_mode
    await client.aclose()

def test_sync_client_creation():
    client = BMLConnect(api_key="test", app_id="test", environment=Environment.SANDBOX)
    assert not client.async_mode
    client.close()
