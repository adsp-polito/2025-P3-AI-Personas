"""
Basic tests for API client methods.

These check that methods are callable and return expected types.
Does not test actual HTTP requests.
"""

from adsp.fe.api_client import APIClient


def test_client_initialization():
    client = APIClient(base_url="http://localhost:8000")
    assert client.base_url == "http://localhost:8000"
    assert client.username is None
    assert client.token is None


def test_client_with_auth():
    client = APIClient(
        base_url="http://test.com",
        username="alice",
        token="secret"
    )
    assert client.username == "alice"
    assert client.token == "secret"


def test_get_headers_no_auth():
    client = APIClient(base_url="http://test.com")
    headers = client._get_headers()

    assert "Content-Type" in headers
    assert headers["Content-Type"] == "application/json"
    assert "X-User" not in headers


def test_get_headers_with_auth():
    client = APIClient(
        base_url="http://test.com",
        username="bob",
        token="token123"
    )
    headers = client._get_headers()

    assert headers["X-User"] == "bob"
    assert headers["X-Token"] == "token123"
