"""Tests for GitHub webhook signature verification."""

import hashlib
import hmac

from src.github.webhooks import verify_signature


def _make_sig(payload: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_valid_signature():
    payload = b'{"action": "push"}'
    secret = "my-secret"
    sig = _make_sig(payload, secret)
    assert verify_signature(payload, sig, secret) is True


def test_invalid_signature():
    payload = b'{"action": "push"}'
    secret = "my-secret"
    assert verify_signature(payload, "sha256=bad", secret) is False


def test_missing_prefix():
    payload = b'{"action": "push"}'
    secret = "my-secret"
    assert verify_signature(payload, "badsignature", secret) is False


def test_empty_signature():
    payload = b'{"action": "push"}'
    assert verify_signature(payload, "", "secret") is False


def test_empty_secret():
    payload = b'{"action": "push"}'
    assert verify_signature(payload, "sha256=abc", "") is False
