"""Offline license keys for the shellguard commercial tier.

The MIT source is free forever. A paying customer buys a *commercial license*:
a signed key naming the customer and the tier. Verification is offline and
uses HMAC-SHA256 over a canonical payload, so a key cannot be forged, edited
or replayed without the issuer secret. No network, no dependencies.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from collections import namedtuple

__all__ = ["issue", "verify", "LicenseError", "License", "TIERS"]

TIERS = ("commercial",)

License = namedtuple("License", ["customer", "tier", "issued", "expires", "key"])


class LicenseError(Exception):
    """A key is malformed, forged, for the wrong issuer, or expired."""


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sign(secret: str, body: str) -> str:
    return _b64e(hmac.new(secret.encode("utf-8"), body.encode("ascii"),
                          hashlib.sha256).digest())


def issue(customer, tier, secret, *, now=None, days=3650):
    """Return a signed license key for ``customer``.

    Deterministic for a given (customer, tier, secret, now): the same inputs
    always produce the same key, so a reissued key never surprises a buyer.
    """
    if not isinstance(customer, str) or not customer.strip():
        raise LicenseError("customer must be a non-empty string")
    if tier not in TIERS:
        raise LicenseError("unknown tier %r" % (tier,))
    if not isinstance(secret, str) or not secret:
        raise LicenseError("issuer secret must be a non-empty string")
    if days <= 0:
        raise LicenseError("days must be positive")
    now = int(time.time() if now is None else now)
    payload = {"c": customer.strip(), "t": tier, "i": now,
               "e": now + int(days) * 86400}
    body = _b64e(json.dumps(payload, separators=(",", ":"),
                            sort_keys=True).encode("utf-8"))
    return "SG1-%s.%s" % (body, _sign(secret, body))


def verify(key, secret, *, now=None):
    """Validate a key and return a :class:`License`.

    Raises :class:`LicenseError` on bad format, forged signature, wrong
    issuer secret, or expiry. Never raises on attacker input.
    """
    if not isinstance(key, str) or not key.startswith("SG1-"):
        raise LicenseError("bad key format")
    try:
        body, sig = key[4:].split(".", 1)
    except ValueError:
        raise LicenseError("bad key format") from None
    if not isinstance(secret, str) or not secret:
        raise LicenseError("issuer secret must be a non-empty string")
    if not hmac.compare_digest(sig, _sign(secret, body)):
        raise LicenseError("bad signature")
    try:
        payload = json.loads(_b64d(body).decode("utf-8"))
        customer, tier = payload["c"], payload["t"]
        issued, expires = int(payload["i"]), int(payload["e"])
    except Exception:
        raise LicenseError("bad payload") from None
    if not isinstance(customer, str) or tier not in TIERS:
        raise LicenseError("bad payload")
    now = int(time.time() if now is None else now)
    if expires < now:
        raise LicenseError("license expired")
    return License(customer, tier, issued, expires, key)
