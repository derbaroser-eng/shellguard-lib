# STATUS — shellguard (2026-11-22 cron run)

## This run
- docs gate: `python scripts/docs_gate.py check` -> allowed=true, exit 0.
- product chosen: shellguard — closest to shippable (v1.4.0 released, suite green,
  landing live, gh authenticated with repo scope).
- found a real false negative: `subprocess.run(['sh','-c', cmd])` passes an argv
  list, so SG003 never fires, yet the command still reaches a shell parser.
  Literal `['sh','-c','true']` is safe and stays unflagged.
- RED: 9 new contract tests in `tests/test_audit.py` -> Ran 135 tests,
  FAILED (failures=4, errors=6), exit 1.
- GREEN: added rule SG005 (SHELL_ARGV_C) in `src/shellguard/audit.py` — detects
  shell interpreters (sh/bash/dash/zsh/ksh/fish/csh/tcsh/cmd/powershell/pwsh,
  absolute paths, .exe) invoked with -c/-lc/... on a NON-literal command,
  including import aliases and `asyncio.create_subprocess_exec`.
  -> Ran 135 tests, OK, exit 0.
- public claims locked to source: README 120 contract tests / 36 audit cases;
  LISTING 120 contract tests; landing 135 tests green / 36 audit cases + rule text.
- version 1.4.0 -> 1.5.0; `uv build --offline` exit 0 ->
  dist/shellguard-1.5.0-py3-none-any.whl + .tar.gz (zero downloads).
- wheel inspected with zipfile: SG005 code present, METADATA Version: 1.5.0.
- self-audit: `audit(['src','tests'])` -> files=12, findings=0, errors=0, exit 0.

## Next concrete step
- Distribution: post the v1.5.0 release and landing to Python/security channels
  (awesome-list PRs, r/Python, HN Show); drive traffic to the store URL.

## Blocker
- PyPI token absent (owner step). GitHub release rail is unblocked.

## 2026-11-22 release evidence (post-push)
- lib pushed: 5e67232..8adf2f9 master -> master, exit 0 (rebased onto remote human-voice README).
- release v1.5.0 created: https://github.com/derbaroser-eng/shellguard-lib/releases/tag/v1.5.0, exit 0.
- assets verified: shellguard-1.5.0-py3-none-any.whl + shellguard-1.5.0.tar.gz.
- site pushed: f37b4e9..b40ff23 master -> master, exit 0 (rebased onto remote field-note page).
- suite after both rebases: Ran 135 tests, OK, exit 0.
- live HTTP: release wheel 200/17645B; landing 200/10046B; EUR49 checkout 200; pay-what-you-can 200.
- live page contains 135 tests green, 36 audit cases, ['sh','-c', cmd], v1.5.0 install URL; zero stale 126 claims.

---

# STATUS — shellguard (2026-11-21, 02:42 cron run)

## This run
- docs gate: `python scripts/docs_gate.py check` -> allowed=true ("live docs fetched and studied"), exit 0.
- product chosen: shellguard — closest to shippable (v1.4.0 released, suite green, landing live).
- executed the next step from last run: live CI badge + GitHub Action usage snippet on the landing page and README (distribution surface for shellguard-action).
- TDD: 3 new acceptance tests (2 in tests/test_landing.py, 1 in tests/test_docs.py) lock the badge to the real dogfood workflow (.github/workflows/shellguard-audit.yml uses derbaroser-eng/shellguard-action@v1) and require the usage snippet. RED: Ran 126 tests, FAILED (failures=3), exit 1. GREEN after page/README patches: Ran 126 tests, OK, exit 0.
- fixed ResourceWarning: tests/test_shellguard.py unclosed file now a context manager; `PYTHONPATH="src;tests" python -W error::ResourceWarning -m unittest test_shellguard` -> Ran 26 tests, OK, exit 0.
- action README suite count 123 -> 126; synced to the published repo via staging clone (remote README blob sha == local git hash-object 44716cfa...), push exit 0. action.yml + LICENSE verified byte-identical to remote (blob sha match).
- badge live: badge.svg HTTP 200, SVG says "passing"; workflow page HTTP 200.
- pushed lib (ab311926) + site; Pages status=built; live landing (cache-busted) serves badge + CI gate section + 111-test claim + Stripe CTA (6/6 checks, 9311 bytes).
- dogfood CI re-run on the new HEAD: run 44853953763 conclusion=success at ab311926.
- action tests: `python -m unittest test_action test_action_hardening` -> Ran 10 tests, OK, exit 0.

## Next concrete step
- distribution: post the landing + action to Python/security channels (awesome-list PRs, r/Python, HN Show); NULL TIDE Game Jolt rail (gj-1).

## Blocker
- PyPI token absent (owner step); itch.io credential absent. Neither blocks the GitHub rail.

---

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

---

# STATUS — shellguard (2026-11-21T01:55+01:00)

## This run
- docs gate: `docs_gate.guard()` -> `{}` exit 0 (live-docs receipt valid).
- verified v1.4.0 already shipped: release asset digests == local dist sha256 (wheel d0415ac..., sdist 61f27f5...); lib+landing repos pushed (0/0 ahead); live landing serves 111 product tests + v1.4.0.
- real gap found: shellguard-action had 3 RED hardening tests (path guard, wheel sha256 verification, pinned default hash).
- patched `../shellguard-action/action.yml`: `case "$SG_PATHS"` guard (`-*` -> exit 2), curl + `sha256sum -c` before pip install, `wheel-sha256` input pinned to the real v1.4.0 wheel hash.
- tests: `python -m unittest test_action test_action_hardening` -> Ran 10 tests, OK, exit 0 (before patch: FAILED failures=3).
- runtime simulation, both directions: option-like path -> 2; clean src -> 0 (5 files, 0 findings); dirty dir -> 1 (SG002 + ::error::); correct sha256 -> OK/0; wrong sha256 -> FAILED/1.
- published: https://github.com/derbaroser-eng/shellguard-action (public), release v1.0.0 + tags v1.0.0/v1, all exit 0.
- dogfood CI: shellguard-lib workflow uses `derbaroser-eng/shellguard-action@v1` on src; run 44849099251 conclusion=success at HEAD 9c5f8853; log lines: "shellguard-1.4.0-py3-none-any.whl: OK", "Successfully installed shellguard-1.4.0", {"files_scanned": 5, "findings": [], "errors": []}.
- Marketplace URL -> 404 (API-created release not auto-listed; action fully usable via uses:@v1).

## Next concrete step
- add action badge + usage snippet to the landing page/README (distribution), then NULL TIDE Game Jolt rail (gj-1).
- minor: ResourceWarning at tests/test_shellguard.py:109 (unclosed file) — cosmetic.

## Blocker
- PyPI token absent (owner step); itch.io credential absent. Neither blocks the GitHub rail.
