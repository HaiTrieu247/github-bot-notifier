"""GitHub Webhook HMAC-SHA256 signature verification."""

from __future__ import annotations

import hashlib
import hmac
import logging

logger = logging.getLogger(__name__)


def verify_signature(payload_bytes: bytes, signature_header: str, secret: str) -> bool:
    """
    Verify the X-Hub-Signature-256 header from GitHub.
    Returns True if valid, False otherwise.
    """
    if not signature_header or not secret:
        return False

    if not signature_header.startswith("sha256="):
        logger.warning("Invalid signature format: missing 'sha256=' prefix")
        return False

    expected_signature = "sha256=" + hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()

    is_valid = hmac.compare_digest(expected_signature, signature_header)
    if not is_valid:
        logger.warning("Webhook signature verification failed")
    return is_valid
