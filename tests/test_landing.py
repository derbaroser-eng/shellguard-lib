"""Acceptance tests: the public landing page must match the real product.

Every numeric claim on the checkout page is checked against the actual test
suite (counted from source) and the actual release asset, so the marketing
surface cannot drift away from the code. Offline and deterministic.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

import shellguard as sg

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT.parent / "shellguard-site" / "index.html"
DIST = ROOT / "dist"
TESTS = ROOT / "tests"
BS = chr(92)  # backslash, built explicitly to avoid escaping ambiguity


def _landing():
    return SITE.read_text(encoding="utf-8")


META_TESTS = {"test_landing.py", "test_docs.py"}
LANDING_TEST = "test_landing.py"


def _test_method_counts():
    """Counts of the full suite, matching the landing's stated total.

    The landing reports the whole `unittest discover` run (product tests plus
    the two meta-tests that hold the docs to reality), so the total asserted
    here must include them too. Per-file counts are unaffected.
    """
    counts = {}
    for path in sorted(TESTS.glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        n = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                    and node.name.startswith("test_"):
                n += 1
        counts[path.name] = n
    return counts


class LandingPageMatchesProductTests(unittest.TestCase):
    def test_landing_page_exists(self):
        self.assertTrue(SITE.is_file(), "landing page not found at %s" % SITE)

    def test_stated_test_total_is_real(self):
        counts = _test_method_counts()
        total = sum(counts.values())
        self.assertGreater(total, 0, "no tests discovered")
        landing = _landing()
        self.assertIn("%d tests green" % total, landing)
        self.assertIn("Ran %d tests" % total, landing)
        self.assertNotIn("Ran 26 tests", landing)
        self.assertNotIn("26 attack cases green", landing)

    def test_counts_are_itemized(self):
        counts = _test_method_counts()
        landing = _landing()
        self.assertIn("%d real attack cases" % counts["test_shellguard.py"], landing)
        self.assertIn("%d license" % counts["test_license.py"], landing)
        self.assertIn("%d CLI" % counts["test_cli.py"], landing)
        self.assertIn("%d delivery" % counts["test_delivery.py"], landing)
        self.assertIn("%d audit cases" % counts["test_audit.py"], landing)

    def test_usage_example_matches_real_output(self):
        landing = _landing()
        real = sg.run(["echo", "(17*23)"]).stdout
        body = real.rstrip("\n")
        shown = '"' + body + BS + 'n"'
        self.assertIn(shown, landing)
        self.assertNotIn("391", landing)

    def test_install_url_matches_release_asset(self):
        landing = _landing()
        wheel = "shellguard-%s-py3-none-any.whl" % sg.__version__
        self.assertIn(wheel, landing)
        if DIST.is_dir():
            self.assertIn(wheel, [p.name for p in DIST.iterdir()])

    def test_checkout_links_present(self):
        landing = _landing()
        self.assertIn("buy.stripe.com", landing)
        self.assertIn("EUR49", landing)

    def test_ci_badge_points_at_real_dogfood_workflow(self):
        landing = _landing()
        badge = ("https://github.com/derbaroser-eng/shellguard-lib/actions/"
                 "workflows/shellguard-audit.yml/badge.svg")
        self.assertIn(badge, landing, "landing has no live CI badge")
        wf = ROOT / ".github" / "workflows" / "shellguard-audit.yml"
        self.assertTrue(wf.is_file(), "dogfood workflow missing from lib repo")
        self.assertIn("derbaroser-eng/shellguard-action@v1",
                      wf.read_text(encoding="utf-8"),
                      "badge workflow does not dogfood the published action")

    def test_ci_usage_snippet_present(self):
        landing = _landing()
        self.assertIn("uses: derbaroser-eng/shellguard-action@v1", landing,
                      "landing does not show how to add the CI gate")


if __name__ == "__main__":
    unittest.main()
