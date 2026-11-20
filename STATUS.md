# STATUS — shellguard (2026-11-20T22:45+01:00)

## This run
- docs gate: `python scripts/docs_gate.py check` -> allowed=true ("live docs fetched and studied"), exit 0; `state` captured (Hermes v0.23.1, Python 3.14.9).
- product chosen: shellguard — closest to shippable (suite green, landing live, release v1.2.0 live; PyPI blocked).
- found a real false negative: `sg audit` did NOT flag `asyncio.create_subprocess_shell` (a common async shell-injection sink). Probe before fix: `asyncio.create_subprocess_shell('ls')` -> 0 findings.
- added rule SG004 (ASYNC_SHELL) in `src/shellguard/audit.py`: matches the dotted call, the `import asyncio as a` alias, and `from asyncio import create_subprocess_shell`. `asyncio.create_subprocess_exec` is correctly NOT flagged.
- added 2 contract tests in `tests/test_audit.py` (positive + negative): 19 -> 21.
- docs locked to the new counts: README / LISTING / landing 103 -> 105 product tests, 19 -> 21 audit cases.
- version 1.2.0 -> 1.3.0; `uv build` exit 0 -> dist/shellguard-1.3.0-py3-none-any.whl + .tar.gz.
- suite: `PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py"` -> Ran 117 tests, OK, exit 0 (105 product + 6 landing + 6 docs).
- self-audit: `audit(['src','tests'])` -> 0 findings.

## Next concrete step
- Publish release v1.3.0 on shellguard-lib (wheel + sdist) and push the landing to derbaroser-eng/shellguard so Pages serves the 105-test page and the v1.3.0 install URL. Then post the landing + release to Python/security channels.

## Blocker
- PyPI publish still needs a `PYPI_API_TOKEN` (owner step).

---

# STATUS — shellguard (2026-11-20T19:4x+01:00)

## This run
- docs gate: `docs_gate.guard()` -> `{}` (exit 0, live docs fetched, receipt valid);
  `docs_gate.system_state()` captured (Hermes v0.23.1, Python 3.14.9).
- product chosen: shellguard (closest to shippable: product suite green, landing
  live, Stripe links live, release v1.0.0 published).
- fixed README install line: `pip install shellguard` installed an UNRELATED PyPI
  package (metadata GET `https://pypi.org/pypi/shellguard/json` -> HTTP 200, not
  ours). README now points at the release wheel and gives a clone-and-run path.
- fixed landing-page drift in `shellguard-site/index.html`:
  "26 attack cases green" -> "61 tests green" (26 attack + 16 license + 19 CLI);
  usage example `# -> "391\n"` -> the real output `"(17*23)\n"`;
  demo block -> the real suite command and real count.
- added `tests/test_landing.py` (6 acceptance tests): counts the product suite
  from source and asserts the landing's stated total, itemized counts, usage
  output, release-wheel install URL and Stripe checkout links match reality.
- suite: `PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py"`
  -> Ran 67 tests, OK, exit 0 (61 product + 6 landing acceptance).
- PyPI name check (metadata GET, no download): shellguard=200 (taken);
  shellguard-argv / shell-guard / shellguard-run / sg-run = 404 (free).

## Blocker (needs owner)
- PyPI upload: no `PYPI_API_TOKEN` / `TWINE_PASSWORD`. The `shellguard` name is
  taken; free alternatives: shellguard-argv, shell-guard, shellguard-run, sg-run.
  Human step: create a PyPI account + token, pick a name, `uv publish`.

## Next concrete step
- Publish the wheel to PyPI under a free name, then point the README and landing
  install line at `pip install <name>`.

---

# STATUS — shellguard (2026-11-20T21:35+01:00)

## This run
- docs gate: `docs_gate.guard()` -> `{}`, exit 0 (live docs fetched, receipt valid); `docs_gate.system_state()` captured.
- product chosen: shellguard — closest to shippable (suite green, release v1.1.0 published, landing live).
- found + fixed stale public docs: README claimed "61 contract tests" and "19 CLI cases";
  the real product suite is 84 tests (26 attack + 16 license + 24 CLI + 18 delivery).
  LISTING claimed "42 contract tests" and told buyers to `pip install shellguard`
  (that PyPI name belongs to an unrelated package).
- added `tests/test_docs.py` (6 acceptance tests) locking README + LISTING to the suite
  counted from source, to the release wheel URL, and to the absence of the taken PyPI
  install command. `tests/test_landing.py` now excludes both meta-tests so adding a
  docs test cannot break the landing's stated count.
- install-and-run proof: clean venv -> `pip install dist/shellguard-1.1.0-py3-none-any.whl`
  exit 0; `import shellguard` -> 1.1.0; `sg.run(["echo","(17*23)"])` -> `'(17*23)\n'`;
  `sg.run(["echo","$(touch pwned)"])` -> literal, no `pwned` file created;
  `shellguard --version` and `sg run` exit 0.
- release check: `gh api repos/derbaroser-eng/shellguard-lib/releases/tags/v1.1.0`
  -> 2 assets uploaded (wheel 12840 B, sdist 17875 B), draft=false; asset URLs HTTP 302.
- suite: `PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py"`
  -> Ran 96 tests, OK, exit 0.
- commit d6c113c pushed to origin/master, push exit 0.

## Next concrete step
- PyPI publish still blocked (no PYPI_API_TOKEN) — not required: README, LISTING and the
  landing all point at the release wheel. Distribution is the remaining gap: post the
  landing + release to Python/security channels.
