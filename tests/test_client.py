import pytest
from bml_connect import BMLConnect, Environment

def test_client_init():
    client = BMLConnect(api_key="test", app_id="test", environment=Environment.SANDBOX)
    assert client.api_key == "test"
    assert client.app_id == "test"
    assert client.environment == Environment.SANDBOX
