"""
Tests for authentication service.

Verifies user registration and token validation.
"""

from adsp.app.auth_service import AuthService


def test_register_new_user():
    auth = AuthService()
    auth.register("alice", "secret123")

    assert auth.is_authorized("alice", "secret123")


def test_wrong_token():
    auth = AuthService()
    auth.register("bob", "correct_token")

    assert not auth.is_authorized("bob", "wrong_token")


def test_unregistered_user():
    auth = AuthService()
    assert not auth.is_authorized("charlie", "any_token")


def test_multiple_users():
    auth = AuthService()
    auth.register("user1", "token1")
    auth.register("user2", "token2")

    assert auth.is_authorized("user1", "token1")
    assert auth.is_authorized("user2", "token2")
    assert not auth.is_authorized("user1", "token2")
