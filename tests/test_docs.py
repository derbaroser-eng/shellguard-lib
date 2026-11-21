"""Acceptance tests: README.md and LISTING.md must match the real product.

The landing page is held to reality by test_landing.py. The repo README and the
marketplace listing copy are the other two public surfaces a buyer reads, so
they get the same standard: the install command must point at the real release
asset, and every stated test count must equal the suite counted from source.
Offline and deterministic.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

import shellguard as sg

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
LISTING = ROOT / "LISTING.md"
DIST = ROOT / "dist"
TESTS = ROOT / "tests"

# Meta-tests assert on docs/landing, not on library behaviour.
META_TESTS = {"test_landing.py", "test_docs.py"}


def _test_method_counts():
    """Counts of the *product* suite (meta-tests excluded)."""
    counts = {}
    for path in sorted(TESTS.glob("test_*.py")):
        if path.name in META_TESTS:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        n = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                    and node.name.startswith("test_"):
                n += 1
        counts[path.name] = n
    return counts


def _readme():
    return README.read_text(encoding="utf-8")


def _listing():
    return LISTING.read_text(encoding="utf-8")


def _release_asset_url():
    wheel = "shellguard-%s-py3-none-any.whl" % sg.__version__
    return "releases/download/v%s/%s" % (sg.__version__, wheel), wheel


class PublicDocsMatchProductTests(unittest.TestCase):
    def test_readme_install_command_is_the_release_wheel(self):
        url, wheel = _release_asset_url()
        readme = _readme()
        self.assertIn(url, readme,
                      "README install command does not point at the release asset")
        names = [p.name for p in DIST.iterdir()] if DIST.is_dir() else []
        self.assertIn(wheel, names, "release wheel missing from dist/")

    def test_readme_does_not_send_buyers_to_the_taken_pypi_name(self):
        readme = _readme()
        self.assertNotIn("pip install shellguard\n", readme,
                         "README still tells buyers to pip install the taken PyPI name")

    def test_readme_stated_total_is_real(self):
        total = sum(_test_method_counts().values())
        self.assertIn("%d contract tests" % total, _readme())

    def test_readme_counts_are_itemized(self):
        counts = _test_method_counts()
        readme = _readme()
        self.assertIn("%d real attack cases" % counts["test_shellguard.py"], readme)
        self.assertIn("%d license issuance" % counts["test_license.py"], readme)
        self.assertIn("%d CLI cases" % counts["test_cli.py"], readme)
        self.assertIn("%d delivery cases" % counts["test_delivery.py"], readme)
        self.assertIn("%d audit cases" % counts["test_audit.py"], readme)

    def test_listing_install_command_is_the_release_wheel(self):
        url, _wheel = _release_asset_url()
        listing = _listing()
        self.assertIn(url, listing, "LISTING does not point at the release asset")
        self.assertNotIn("pip install shellguard", listing,
                         "LISTING still tells buyers to pip install the taken PyPI name")

    def test_listing_stated_counts_are_real(self):
        counts = _test_method_counts()
        listing = _listing()
        self.assertIn("%d real attack cases" % counts["test_shellguard.py"], listing)
        for stale in ("42 contract tests", "61 contract tests"):
            self.assertNotIn(stale, listing, "stale total left in LISTING")

    def test_readme_ci_badge_and_action_usage(self):
        readme = _readme()
        badge = ("https://github.com/derbaroser-eng/shellguard-lib/actions/"
                 "workflows/shellguard-audit.yml/badge.svg")
        self.assertIn(badge, readme, "README has no live CI badge")
        self.assertIn("uses: derbaroser-eng/shellguard-action@v1", readme,
                      "README does not show the GitHub Action usage")
        wf = ROOT / ".github" / "workflows" / "shellguard-audit.yml"
        self.assertTrue(wf.is_file(), "dogfood workflow missing from lib repo")


if __name__ == "__main__":
    unittest.main()
