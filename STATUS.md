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
