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

## 2026-11-21T01:55:00+01:00 — shellguard-action hardened + published + dogfooded

- docs gate: `docs_gate.guard()` -> `{}` exit 0
- RED confirmed: `python -m unittest test_action test_action_hardening` -> FAILED (failures=3) on unpatched action.yml
- patched action.yml: option-injection path guard, sha256sum -c wheel verification, wheel-sha256 input pinned to d0415acbb2327cb2a1ed5dd3bfbaea02bc203b7952dd4f2f1162548125f07c6f (== real dist wheel)
- GREEN: same command -> Ran 10 tests, OK, exit 0
- gate simulation (scratch, real wheel, no download): guard path '--json' -> exit 2; clean src -> exit 0; dirty dir -> exit 1 (SG002); sha256 correct -> OK exit 0; sha256 zeroed -> FAILED exit 1
- published repo derbaroser-eng/shellguard-action (public) + release v1.0.0 + tags v1.0.0/v1 -> exit 0
- dogfood: .github/workflows/shellguard-audit.yml in shellguard-lib uses the published action@v1; commit 9c5f8853 pushed; gh run 44849099251 -> conclusion=success; log: wheel ": OK", "Successfully installed shellguard-1.4.0", {"files_scanned": 5, "findings": [], "errors": []}
- product suite re-verified this run: Ran 123 tests, OK, exit 0

## 2026-11-21T02:42 cron run — CI badge + action usage on public surfaces (TDD)

- docs gate: check -> allowed=true, exit 0
- RED: 3 new acceptance tests (test_landing +2, test_docs +1) -> Ran 126 tests, FAILED (failures=3), exit 1
- patched ../shellguard-site/index.html (badge + CI gate section), README.md (badge + CI gate section), tests/test_shellguard.py (unclosed file -> context manager)
- GREEN: Ran 126 tests, OK, exit 0; -W error::ResourceWarning on test_shellguard -> Ran 26 tests, OK, exit 0
- action tests: Ran 10 tests, OK, exit 0; action README 123->126 synced via staging clone, push exit 0; remote README blob sha == local git hash-object 44716cfaa8dbe6b09a105e62e40b69df1867d69f; action.yml/LICENSE blob shas already matched
- badge.svg HTTP 200 "passing"; workflow page HTTP 200
- privacy scan on all changed public files: clean (grep exit 1)
- lib push ab311926 exit 0; site push exit 0; Pages status=built; live cache-busted page 6/6 checks true (9311 bytes)
- dogfood CI on new HEAD: run 44853953763 conclusion=success at ab311926
