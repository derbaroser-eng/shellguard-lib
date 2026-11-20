# LISTING — shellguard

**Title:** shellguard
**Tagline (60 chars):** Run untrusted text as arguments, never shell syntax.
**Category:** Developer Tools / Security / Libraries
**Pricing:** Free (MIT) · EUR 49 one-time (download + commercial license)

## Install

```bash
pip install https://github.com/derbaroser-eng/shellguard-lib/releases/download/v1.3.0/shellguard-1.3.0-py3-none-any.whl
```

The `shellguard` name on PyPI belongs to an unrelated package, so the wheel ships
as a GitHub release asset (zero dependencies, Python 3.8+).

## Description

shellguard is a zero-dependency Python library that executes untrusted input as
argv data, eliminating shell injection at the call site. Every attack token —
`(`, `)`, quotes, backticks, `$( )`, `;`, `|`, `&&`, `*`, `~`, `$VAR`,
redirection, newlines — stays data and never reaches a shell parser.

The bug it kills was observed in production: a prompt containing `(` made bash
abort with `syntax error near unexpected token`, and a prompt containing
backticks executed attacker-chosen commands. Both failures looked like an
unavailable service while short probes still worked.

- Zero dependencies, Python 3.8+
- `shell=True` and bare-string commands are refused by design
- Real exit codes, separate stdout/stderr, timeouts, cwd and env control
- Offline HMAC-SHA256 license keys for the commercial tier
- `sg audit`: AST scanner that flags `shell=True`, `os.system`/`os.popen`, `asyncio.create_subprocess_shell` and string subprocess commands (exit 1 on findings, `--json` for CI)
- 105 contract tests, all running real subprocesses and asserting real output
- 26 real attack cases (parentheses, backticks, `$( )`, `;`, `|`, `&&`, newline,
  quotes, globs, tilde, `$VAR`, redirection, unicode, empty args, binary bytes,
  timeouts, cwd, env, exit codes, stdout/stderr separation)

## Pricing tiers

| Tier | Price | What you get |
|---|---|---|
| Free | EUR 0 | MIT source, full test suite, release wheel (install command above) |
| Commercial | EUR 49 one-time | Packaged download, commercial license, offline license key, email support |
| Support | from EUR 1 | Pay what you want to support development |

## Tags

python, security, subprocess, shell-injection, devtools, library, cli, mit,
supply-chain

## Screenshots / proof

- `site/index.html` — landing page, live at https://derbaroser-eng.github.io/shellguard/
- `tests/test_shellguard.py` — 26 real attack cases
- `tests/test_license.py` — 16 license issuance/validation cases
- `tests/test_cli.py` — 24 CLI cases
- `tests/test_delivery.py` — 18 commercial delivery cases

## Publish targets

- Release wheel: https://github.com/derbaroser-eng/shellguard-lib/releases/tag/v1.3.0
- GitHub: https://github.com/derbaroser-eng/shellguard-lib
- Landing: https://derbaroser-eng.github.io/shellguard/
- Checkout: Stripe payment link (EUR 49) and support link (from EUR 1)

## Status

Tests green (105 product + 6 landing + 6 docs = 117, exit 0). The wheel installs
into a clean venv and the `shellguard` CLI runs (verified exit 0). Landing page
live (HTTP 200, Stripe links present). Listing publishable as-is; PyPI publish is
blocked on a `PYPI_API_TOKEN` (the `shellguard` PyPI name is taken anyway).
