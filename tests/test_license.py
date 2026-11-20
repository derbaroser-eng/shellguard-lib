"""Contract tests for shellguard.license (the paid commercial tier)."""
import unittest

from shellguard.license import LicenseError, issue, verify


class TestIssue(unittest.TestCase):
    def test_roundtrip_returns_named_customer(self):
        key = issue("acme@example.com", "commercial", "s3cret")
        lic = verify(key, "s3cret", now=1000)
        self.assertEqual(lic.customer, "acme@example.com")
        self.assertEqual(lic.tier, "commercial")

    def test_key_is_prefixed_and_has_two_parts(self):
        key = issue("acme", "commercial", "s3cret", now=1000)
        self.assertTrue(key.startswith("SG1-"))
        self.assertEqual(len(key[4:].split(".")), 2)

    def test_issue_is_deterministic(self):
        a = issue("acme", "commercial", "s3cret", now=1000)
        b = issue("acme", "commercial", "s3cret", now=1000)
        self.assertEqual(a, b)

    def test_different_customers_get_different_keys(self):
        a = issue("one", "commercial", "s3cret", now=1000)
        b = issue("two", "commercial", "s3cret", now=1000)
        self.assertNotEqual(a, b)

    def test_customer_is_stripped(self):
        key = issue("  acme  ", "commercial", "s3cret", now=1000)
        self.assertEqual(verify(key, "s3cret", now=1000).customer, "acme")

    def test_unknown_tier_refused(self):
        with self.assertRaises(LicenseError):
            issue("acme", "enterprise", "s3cret")

    def test_empty_customer_refused(self):
        with self.assertRaises(LicenseError):
            issue("   ", "commercial", "s3cret")

    def test_empty_secret_refused(self):
        with self.assertRaises(LicenseError):
            issue("acme", "commercial", "")

    def test_nonpositive_days_refused(self):
        with self.assertRaises(LicenseError):
            issue("acme", "commercial", "s3cret", days=0)


class TestVerify(unittest.TestCase):
    def test_wrong_secret_rejected(self):
        key = issue("acme", "commercial", "s3cret")
        with self.assertRaises(LicenseError):
            verify(key, "wrong")

    def test_tampered_body_rejected(self):
        key = issue("acme", "commercial", "s3cret", now=1000)
        body, sig = key[4:].split(".")
        forged = "SG1-" + body[:-3] + "zzz." + sig
        with self.assertRaises(LicenseError):
            verify(forged, "s3cret")

    def test_garbage_key_rejected(self):
        for bad in ("", "SG1-", "SG1-nodot", "XYZ-abc.def", "SG1-!!!.???", None, 123):
            with self.assertRaises(LicenseError):
                verify(bad, "s3cret")

    def test_expired_key_rejected(self):
        key = issue("acme", "commercial", "s3cret", now=1000, days=30)
        with self.assertRaises(LicenseError):
            verify(key, "s3cret", now=1000 + 31 * 86400)

    def test_valid_before_expiry_boundary(self):
        key = issue("acme", "commercial", "s3cret", now=1000, days=30)
        lic = verify(key, "s3cret", now=1000 + 30 * 86400 - 1)
        self.assertEqual(lic.expires, 1000 + 30 * 86400)

    def test_license_carries_key_and_times(self):
        key = issue("acme", "commercial", "s3cret", now=1000)
        lic = verify(key, "s3cret", now=1000)
        self.assertEqual(lic.key, key)
        self.assertEqual(lic.issued, 1000)
        self.assertGreater(lic.expires, lic.issued)

    def test_empty_secret_does_not_leak_validity(self):
        key = issue("acme", "commercial", "s3cret")
        with self.assertRaises(LicenseError):
            verify(key, "")


if __name__ == "__main__":
    unittest.main()
