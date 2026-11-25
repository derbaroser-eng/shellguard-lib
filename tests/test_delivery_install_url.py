"""Acceptance: the buyer delivery email must link the CURRENT release wheel.

A paying customer follows this link. A stale version here ships an obsolete
product, so the URL is derived from the installed version and checked against
the real dist/ asset, like every other public surface.
"""
from __future__ import annotations

import unittest
from pathlib import Path

import shellguard as sg
from shellguard.delivery import Delivery, render_email

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def _delivery():
    return Delivery("buyer@example.com", "cs_test_1", 4900, "eur",
                    "SG1-test.fake", 1700000000, 1700000000 + 3650 * 86400)


class DeliveryEmailInstallUrlTests(unittest.TestCase):
    def test_install_url_points_at_current_version(self):
        email = render_email(_delivery())
        expected = "releases/download/v%s/shellguard-%s-py3-none-any.whl" % (
            sg.__version__, sg.__version__)
        self.assertIn(expected, email, "delivery email links a stale wheel")

    def test_installed_version_wheel_is_present_in_dist(self):
        email = render_email(_delivery())
        wheel = "shellguard-%s-py3-none-any.whl" % sg.__version__
        self.assertIn(wheel, email)
        self.assertIn(wheel, [p.name for p in DIST.iterdir()])


if __name__ == "__main__":
    unittest.main()
