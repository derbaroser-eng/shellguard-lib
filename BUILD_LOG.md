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

## 2026-11-20T18:05:00+01:00 — CLI entry point + PEP 561 typing marker

- docs gate: `python scripts/docs_gate.py` -> exit 0 ("live docs fetched and studied"); guard() 0.57s, receipt valid; system_state() captured (Hermes v0.23.1, Python 3.14.9)
- created `src/shellguard/cli.py` (`sg run|quote|license`, exit codes 0/1/2)
- created `src/shellguard/py.typed` (PEP 561 typed-package marker)
- created `tests/test_cli.py` (19 cases: run/quote/license/top-level/entrypoint)
- modified `pyproject.toml` (`[project.scripts] shellguard = shellguard.cli:main`; package-data py.typed)
- full suite: `PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py"` -> Ran 61 tests, OK, exit 0
- build: `uv build` -> exit 0; dist/shellguard-1.0.0-py3-none-any.whl + dist/shellguard-1.0.0.tar.gz; wheel contains cli.py, license.py, py.typed, entry_points.txt
- install: `uv venv` + `uv pip install --no-deps --offline dist/shellguard-1.0.0-py3-none-any.whl` -> exit 0, `+ shellguard==1.0.0`
- installed CLI evidence: `shellguard --version` -> `shellguard 1.0.0` (exit 0); `quote "a b" "it's"` -> `'a b' 'it'\''s'` (exit 0); `run -- echo "(17*23)"` -> `(17*23)` (exit 0); `run -- false` -> exit 1; license issue->verify roundtrip -> exit 0; wrong secret -> exit 1
- next blocker: PyPI upload needs owner credentials (twine `__token__`); Stripe checkout links already live on the landing page

## 2026-11-20T19:4x+01:00 — landing page locked to reality + install fix

- docs gate: `docs_gate.guard()` -> exit 0 (`{}`); `system_state()` captured (Hermes v0.23.1, Python 3.14.9)
- created `tests/test_landing.py` (6 acceptance tests: real total, itemized counts, usage output, release asset, checkout links)
- modified `README.md` (install points at the release wheel, not the unrelated PyPI `shellguard`; test count 42 -> 61)
- modified `../shellguard-site/index.html` (61 tests green; real usage output; real suite command/count)
- suite: `PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py"` -> Ran 67 tests, OK, exit 0
- PyPI metadata GET: shellguard=200 (taken); shellguard-argv/shell-guard/shellguard-run/sg-run=404 (free)
- next blocker: PyPI token absent (owner step)
