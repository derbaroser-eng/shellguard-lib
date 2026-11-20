"""Automated delivery for the shellguard commercial tier.

A buyer pays on Stripe Checkout; Stripe emits a ``checkout.session.completed``
event. This module turns that event into the deliverable the buyer actually
receives: a signed commercial license key bound to the buyer email and session,
plus the email body to send.
"""
from __future__ import annotations

import time
from collections import namedtuple

from .license import issue, verify

__all__ = ["DeliveryError", "Delivery", "parse_session", "fulfill",
           "render_email", "delivery_email"]

Delivery = namedtuple("Delivery", ["email", "session_id", "amount_cents",
                                   "currency", "license_key", "issued",
                                   "expires"])


class DeliveryError(Exception):
    """A checkout session cannot be fulfilled."""


def _session_from(event):
    """Accept either a Stripe event envelope or a bare session object."""
    if not isinstance(event, dict):
        raise DeliveryError("event must be a JSON object")
    if "data" in event or event.get("object") == "event":
        data = event.get("data")
        if not isinstance(data, dict):
            raise DeliveryError("event has no data object")
        obj = data.get("object")
        if not isinstance(obj, dict):
            raise DeliveryError("event data has no session object")
        return obj
    if event.get("object") == "checkout.session":
        return event
    raise DeliveryError("not a Stripe checkout session")


def parse_session(event, *, min_cents, currency=None):
    """Validate a checkout session and return the fields delivery needs."""
    obj = _session_from(event)

    status = obj.get("status")
    if status != "complete":
        raise DeliveryError("session status is %r, not complete" % (status,))

    paid = obj.get("payment_status")
    if paid != "paid":
        raise DeliveryError("session payment_status is %r, not paid" % (paid,))

    amount = obj.get("amount_received")
    if not isinstance(amount, int) or isinstance(amount, bool):
        raise DeliveryError("session has no integer amount_received")
    if amount < int(min_cents):
        raise DeliveryError("amount_received %d is below minimum %d"
                            % (amount, int(min_cents)))

    cur = obj.get("currency")
    if not isinstance(cur, str) or not cur:
        raise DeliveryError("session has no currency")
    cur = cur.upper()
    if currency is not None and cur != str(currency).upper():
        raise DeliveryError("currency %s does not match %s"
                            % (cur, str(currency).upper()))

    details = obj.get("customer_details")
    email = None
    if isinstance(details, dict):
        email = details.get("email")
    if not email:
        email = obj.get("customer_email")
    if not email and isinstance(obj.get("customer"), str):
        email = obj.get("customer")
    if not isinstance(email, str) or "@" not in email:
        raise DeliveryError("session has no buyer email")

    sid = obj.get("id")
    if not isinstance(sid, str) or not sid:
        raise DeliveryError("session has no id")

    created = obj.get("created")
    if not isinstance(created, int) or isinstance(created, bool):
        created = None

    return {"session_id": sid, "email": email.strip(), "amount_cents": amount,
            "currency": cur, "created": created}


def fulfill(event, secret, *, min_cents, currency=None):
    """Return a :class:`Delivery` for a paid checkout session.

    The license ``now`` is the Stripe session ``created`` timestamp, so the
    same session always mints the same key (idempotent retries).
    """
    sess = parse_session(event, min_cents=min_cents, currency=currency)
    key = issue(sess["email"], "commercial", secret, now=sess["created"])
    lic = verify(key, secret)
    return Delivery(sess["email"], sess["session_id"], sess["amount_cents"],
                    sess["currency"], key, lic.issued, lic.expires)


def _expiry(epoch):
    return time.strftime("%Y-%m-%d", time.gmtime(int(epoch)))


def render_email(delivery, *, product="shellguard commercial license"):
    """Render the buyer-facing delivery email for a :class:`Delivery`."""
    return (
        "Subject: Your {product}\n"
        "\n"
        "Hi,\n"
        "\n"
        "Thanks for buying {product}. Your license key is below. It is bound\n"
        "to this order and to your email.\n"
        "\n"
        "  {key}\n"
        "\n"
        "Order: {sid}\n"
        "Amount: {cents} {cur}\n"
        "Valid until: {exp}\n"
        "\n"
        "Install (zero dependencies):\n"
        "  pip install https://github.com/derbaroser-eng/shellguard-lib/releases/download/v1.1.0/shellguard-1.1.0-py3-none-any.whl\n"
        "\n"
        "The MIT source is free forever; this key covers commercial use without\n"
        "MIT attribution.\n"
    ).format(product=product, key=delivery.license_key, sid=delivery.session_id,
             cents=delivery.amount_cents, cur=delivery.currency,
             exp=_expiry(delivery.expires))


def delivery_email(event, secret, *, min_cents, currency=None, product=None):
    """Fulfil a session and return ``(Delivery, email_text)``."""
    d = fulfill(event, secret, min_cents=min_cents, currency=currency)
    kwargs = {} if product is None else {"product": product}
    return d, render_email(d, **kwargs)
