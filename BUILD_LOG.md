# BUILD_LOG — shellguard

Machine-readable evidence. One block per run.

## 2026-11-20T17:35:00+01:00 — commercial tier deliverable

- docs gate: `python scripts/docs_gate.py` -> exit 0 ("live docs fetched and studied")
- product selected: shellguard (closest to shippable: 26 attack tests green, landing live, Stripe links live)
- created `src/shellguard/license.py` (offline HMAC-SHA256 license keys: issue/verify)
- created `tests/test_license.py` (16 cases: roundtrip, determinism, forgery, wrong secret, expiry, format, tier validation)
- created `LICENSE-COMMERCIAL.md` (the EUR 49 deliverable text)
- created `LISTING.md` (title, tagline, tiers, tags, publish targets)
- modified `README.md` (license API, commercial section, corrected the `echo` example to the real output)
- full suite: `PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py"` -> Ran 42 tests, OK, exit 0
- real-output probe: `sg.run(['echo','(17*23)'])` -> '(17*23)\n'; `sg.run(['echo','`echo INJECTED`'])` -> '`echo INJECTED`\n'
- live checks: https://derbaroser-eng.github.io/shellguard/ -> 200, Stripe links present; Stripe links -> 200
- commit: (see git log)
