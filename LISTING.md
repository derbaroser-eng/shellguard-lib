# LISTING — shellguard

**Title:** shellguard
**Tagline (60 chars):** Run untrusted text as arguments, never shell syntax.
**Category:** Developer Tools / Security / Libraries
**Pricing:** Free (MIT) · EUR 49 one-time (download + commercial license)

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
- 42 contract tests, all running real subprocesses and asserting real output

## Pricing tiers

| Tier | Price | What you get |
|---|---|---|
| Free | EUR 0 | MIT source, full test suite, `pip install shellguard` |
| Commercial | EUR 49 one-time | Packaged download, commercial license, offline license key, email support |
| Support | from EUR 1 | Pay what you want to support development |

## Tags

python, security, subprocess, shell-injection, devtools, library, cli, mit,
supply-chain

## Screenshots / proof

- `site/index.html` — landing page, live at https://derbaroser-eng.github.io/shellguard/
- `tests/test_shellguard.py` — 26 real attack cases
- `tests/test_license.py` — 16 license issuance/validation cases

## Publish targets

- PyPI: `shellguard` (free MIT wheel)
- GitHub: https://github.com/derbaroser-eng/shellguard-lib
- Landing: https://derbaroser-eng.github.io/shellguard/
- Checkout: Stripe payment link (EUR 49) and support link (from EUR 1)

## Status

Tests green (42/42, exit 0). Landing page live (HTTP 200, Stripe links present).
License module and commercial license text shipped. Listing publishable as-is.
