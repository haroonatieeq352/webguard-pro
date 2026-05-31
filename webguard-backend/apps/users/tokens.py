"""
WebGuard Pro — HMAC Token Utility
Secure, time-limited tokens for email verification and password reset.

Token Format (URL-safe base64):
    <version>.<payload_b64>.<hmac_signature>

Payload JSON:
    { "user_id": "<uuid>", "email": "<email>", "type": "verify|reset", "exp": <unix_ts> }
"""

import base64
import hashlib
import hmac
import json
import time
import logging

from django.conf import settings
from django.contrib.auth import get_user_model

logger = logging.getLogger('apps.users')

# Token type constants
TOKEN_TYPE_VERIFY = 'verify'
TOKEN_TYPE_RESET  = 'reset'

# Expiry durations (seconds)
VERIFY_TOKEN_TTL = 24 * 60 * 60   # 24 hours
RESET_TOKEN_TTL  = 1  * 60 * 60   # 1 hour

# Token version — bump if format changes
TOKEN_VERSION = 'v1'


def _get_secret(token_type: str) -> bytes:
    """Return the correct HMAC secret for the token type."""
    if token_type == TOKEN_TYPE_RESET:
        # Use a separate secret for password-reset to prevent cross-use
        return settings.EMAIL_HMAC_SECRET.encode() + b':reset'
    return settings.EMAIL_HMAC_SECRET.encode()


def _encode_b64(data: bytes) -> str:
    """URL-safe base64 encode, strip padding."""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _decode_b64(s: str) -> bytes:
    """URL-safe base64 decode, add padding."""
    padding = 4 - len(s) % 4
    if padding != 4:
        s += '=' * padding
    return base64.urlsafe_b64decode(s)


def _sign(payload_b64: str, secret: bytes) -> str:
    """HMAC-SHA256 sign the payload."""
    sig = hmac.new(secret, payload_b64.encode('ascii'), hashlib.sha256).digest()
    return _encode_b64(sig)


def _build_token(user, token_type: str, ttl: int) -> str:
    """
    Build a signed token string.
    Format: v1.<payload_b64>.<signature>
    """
    payload = {
        'user_id': str(user.id),
        'email':   user.email,
        'type':    token_type,
        'exp':     int(time.time()) + ttl,
    }
    payload_json = json.dumps(payload, separators=(',', ':'), sort_keys=True)
    payload_b64  = _encode_b64(payload_json.encode('utf-8'))
    secret       = _get_secret(token_type)
    signature    = _sign(payload_b64, secret)
    return f"{TOKEN_VERSION}.{payload_b64}.{signature}"


def _parse_token(token: str, expected_type: str) -> dict:
    """
    Parse and validate a signed token.
    Returns the payload dict on success.
    Raises ValueError with a descriptive message on any failure.
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid token format.")

        version, payload_b64, provided_sig = parts

        if version != TOKEN_VERSION:
            raise ValueError("Unsupported token version.")

        # Verify signature
        secret       = _get_secret(expected_type)
        expected_sig = _sign(payload_b64, secret)
        if not hmac.compare_digest(expected_sig, provided_sig):
            raise ValueError("Token signature is invalid.")

        # Decode payload
        payload_json = _decode_b64(payload_b64).decode('utf-8')
        payload      = json.loads(payload_json)

        # Check token type
        if payload.get('type') != expected_type:
            raise ValueError("Token type mismatch.")

        # Check expiry
        if time.time() > payload.get('exp', 0):
            raise ValueError("Token has expired.")

        return payload

    except (ValueError, KeyError, json.JSONDecodeError) as e:
        # Re-raise ValueError as-is; wrap everything else
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Token parsing error: {e}") from e


# ============================================================
# PUBLIC API — Email Verification
# ============================================================

def generate_email_verification_token(user) -> str:
    """
    Generate a 24-hour HMAC-signed email verification token.
    Safe to call multiple times — old tokens are invalidated by email change.
    """
    token = _build_token(user, TOKEN_TYPE_VERIFY, VERIFY_TOKEN_TTL)
    logger.debug(f"Generated verify token for {user.email} (expires in {VERIFY_TOKEN_TTL}s)")
    return token


def verify_email_token(token: str):
    """
    Validate an email verification token.
    Returns the User object on success.
    Raises ValueError with a user-friendly message on failure.
    """
    User = get_user_model()

    payload = _parse_token(token, TOKEN_TYPE_VERIFY)

    try:
        user = User.objects.get(id=payload['user_id'])
    except User.DoesNotExist:
        raise ValueError("User not found.")

    # Check email matches — prevents using old token after email change
    if user.email != payload['email']:
        raise ValueError("Token is no longer valid (email changed).")

    if user.is_verified:
        raise ValueError("Email is already verified.")

    return user


# ============================================================
# PUBLIC API — Password Reset
# ============================================================

def generate_password_reset_token(user) -> str:
    """
    Generate a 1-hour HMAC-signed password reset token.
    """
    token = _build_token(user, TOKEN_TYPE_RESET, RESET_TOKEN_TTL)
    logger.debug(f"Generated reset token for {user.email} (expires in {RESET_TOKEN_TTL}s)")
    return token


def verify_password_reset_token(token: str):
    """
    Validate a password reset token.
    Returns the User object on success.
    Raises ValueError with a user-friendly message on failure.
    """
    User = get_user_model()

    payload = _parse_token(token, TOKEN_TYPE_RESET)

    try:
        user = User.objects.get(id=payload['user_id'])
    except User.DoesNotExist:
        raise ValueError("User not found.")

    # Check email still matches
    if user.email != payload['email']:
        raise ValueError("Token is no longer valid.")

    return user
