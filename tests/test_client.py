import pytest

from bml_connect import BMLConnect, Environment


def test_client_init_minimal():
    """api_key and environment are the only required args in v2."""
    client = BMLConnect(api_key="test", environment=Environment.SANDBOX)
    assert client.api_key == "test"
    assert client.environment == Environment.SANDBOX
    client.close()


def test_client_init_with_app_id():
    """app_id is now optional but must not break when passed (backward compat)."""
    client = BMLConnect(
        api_key="test", environment=Environment.SANDBOX, app_id="legacy-app-id"
    )
    assert client.api_key == "test"
    client.close()


def test_client_init_string_environment():
    client = BMLConnect(api_key="test", environment="sandbox")
    assert client.environment == Environment.SANDBOX
    client.close()


def test_client_init_invalid_environment():
    with pytest.raises(ValueError, match="Invalid environment"):
        BMLConnect(api_key="test", environment="staging")


def test_client_has_all_resources():
    client = BMLConnect(api_key="test", environment=Environment.SANDBOX)
    assert hasattr(client, "transactions")
    assert hasattr(client, "webhooks")
    assert hasattr(client, "shops")
    assert hasattr(client, "customers")
    assert hasattr(client, "company")
    client.close()


def test_client_sync_mode_default():
    client = BMLConnect(api_key="test", environment=Environment.SANDBOX)
    assert not client.async_mode
    client.close()


@pytest.mark.asyncio
async def test_client_async_mode():
    client = BMLConnect(
        api_key="test", environment=Environment.SANDBOX, async_mode=True
    )
    assert client.async_mode
    await client.aclose()


def test_sync_context_manager():
    with BMLConnect(api_key="test", environment=Environment.SANDBOX) as client:
        assert client.api_key == "test"


@pytest.mark.asyncio
async def test_async_context_manager():
    async with BMLConnect(
        api_key="test", environment=Environment.SANDBOX, async_mode=True
    ) as client:
        assert client.api_key == "test"


def test_production_environment_url():
    client = BMLConnect(api_key="test", environment=Environment.PRODUCTION)
    assert "uat" not in client.environment.base_url
    assert "merchants.bankofmaldives.com.mv" in client.environment.base_url
    client.close()


def test_sandbox_environment_url():
    client = BMLConnect(api_key="test", environment=Environment.SANDBOX)
    assert "uat" in client.environment.base_url
    client.close()
