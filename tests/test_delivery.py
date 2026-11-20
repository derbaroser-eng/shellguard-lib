"""Contract tests for automated commercial delivery (shellguard.delivery)."""
import unittest

from shellguard.delivery import (DeliveryError, delivery_email, fulfill,
                                 parse_session, render_email)
from shellguard.license import LicenseError, verify

SECRET = "unit-test-issuer-secret"


def session(**over):
    base = {
        "id": "cs_test_123",
        "object": "checkout.session",
        "status": "complete",
        "payment_status": "paid",
        "amount_received": 4900,
        "currency": "eur",
        "created": 1763664000,
        "customer_details": {"email": "buyer@example.com"},
    }
    base.update(over)
    return base


def envelope(sess):
    return {"id": "evt_1", "object": "event",
            "type": "checkout.session.completed", "data": {"object": sess}}


class TestParseSession(unittest.TestCase):
    def test_bare_session_is_accepted(self):
        s = parse_session(session(), min_cents=4900)
        self.assertEqual(s["session_id"], "cs_test_123")
        self.assertEqual(s["email"], "buyer@example.com")
        self.assertEqual(s["amount_cents"], 4900)
        self.assertEqual(s["currency"], "EUR")

    def test_event_envelope_is_unwrapped(self):
        s = parse_session(envelope(session()), min_cents=4900)
        self.assertEqual(s["session_id"], "cs_test_123")

    def test_non_complete_is_refused(self):
        with self.assertRaises(DeliveryError):
            parse_session(session(status="open"), min_cents=4900)

    def test_unpaid_is_refused(self):
        with self.assertRaises(DeliveryError):
            parse_session(session(payment_status="unpaid"), min_cents=4900)

    def test_underpaid_is_refused(self):
        with self.assertRaises(DeliveryError):
            parse_session(session(amount_received=100), min_cents=4900)

    def test_wrong_currency_is_refused(self):
        with self.assertRaises(DeliveryError):
            parse_session(session(currency="usd"), min_cents=4900, currency="EUR")

    def test_currency_check_can_be_disabled(self):
        s = parse_session(session(currency="usd"), min_cents=4900)
        self.assertEqual(s["currency"], "USD")

    def test_missing_email_is_refused(self):
        with self.assertRaises(DeliveryError):
            parse_session(session(customer_details={}), min_cents=4900)

    def test_missing_email_key_is_refused(self):
        sess = session()
        del sess["customer_details"]
        with self.assertRaises(DeliveryError):
            parse_session(sess, min_cents=4900)

    def test_non_session_is_refused(self):
        for bad in (None, [], "x", {"object": "charge"}, {"foo": 1}):
            with self.assertRaises(DeliveryError):
                parse_session(bad, min_cents=4900)

    def test_bool_amount_is_refused(self):
        with self.assertRaises(DeliveryError):
            parse_session(session(amount_received=True), min_cents=1)


class TestFulfil(unittest.TestCase):
    def test_license_key_verifies_for_buyer(self):
        d = fulfill(envelope(session()), SECRET, min_cents=4900, currency="EUR")
        lic = verify(d.license_key, SECRET)
        self.assertEqual(lic.customer, "buyer@example.com")
        self.assertEqual(lic.tier, "commercial")
        self.assertEqual(d.session_id, "cs_test_123")

    def test_fulfilment_is_idempotent(self):
        ev = envelope(session())
        a = fulfill(ev, SECRET, min_cents=4900)
        b = fulfill(ev, SECRET, min_cents=4900)
        self.assertEqual(a.license_key, b.license_key)

    def test_wrong_secret_does_not_verify(self):
        d = fulfill(envelope(session()), SECRET, min_cents=4900)
        with self.assertRaises(LicenseError):
            verify(d.license_key, "other-secret")

    def test_tampered_amount_is_refused(self):
        with self.assertRaises(DeliveryError):
            fulfill(envelope(session(amount_received=1)), SECRET, min_cents=4900)

    def test_refused_session_raises_delivery_error(self):
        with self.assertRaises(DeliveryError):
            fulfill(envelope(session(payment_status="unpaid")), SECRET,
                    min_cents=4900)


class TestRenderEmail(unittest.TestCase):
    def test_email_carries_key_order_and_amount(self):
        d = fulfill(envelope(session()), SECRET, min_cents=4900)
        body = render_email(d)
        self.assertIn(d.license_key, body)
        self.assertIn("cs_test_123", body)
        self.assertIn("4900 EUR", body)
        self.assertIn("Subject:", body)

    def test_delivery_email_returns_both_parts(self):
        d, body = delivery_email(envelope(session()), SECRET, min_cents=4900,
                                 product="shellguard commercial license")
        self.assertEqual(d.email, "buyer@example.com")
        self.assertIn(d.license_key, body)
        self.assertIn("shellguard commercial license", body)


if __name__ == "__main__":
    unittest.main()
