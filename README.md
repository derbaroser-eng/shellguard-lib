# shellguard

[![shellguard self-audit](https://github.com/derbaroser-eng/shellguard-lib/actions/workflows/shellguard-audit.yml/badge.svg)](https://github.com/derbaroser-eng/shellguard-lib/actions/workflows/shellguard-audit.yml)

Run untrusted text as **arguments**, never as shell syntax.

## The bug

```python
full = f"cd {cd} && {oc} run --model {model} {prompt}"
```

A prompt containing `(` makes bash abort:

```
bash: -c: line 1: syntax error near unexpected token `('
```

A prompt containing backticks or `$( )` executes attacker-chosen commands.
Both failures were observed in production in a real automation system.

## The rule

Never build a shell string from untrusted text. Build an argv list; execve
semantics keep each token a token.

## Usage

```python
import shellguard as sg

sg.run(["echo", "(17*23)"])            # -> "(17*23)\n"
sg.run(["echo", "`echo INJECTED`"])    # -> "`echo INJECTED`\n"  (data, not a command)
sg.run(["echo", "$(touch pwned)"])     # -> literal text, no file written
sg.run(["false"])                      # Result(returncode=1, ok=False, ...)
```

## Install

The `shellguard` name on PyPI belongs to an unrelated package. Install the
published release wheel directly (zero dependencies, Python 3.8+):

```bash
pip install https://github.com/derbaroser-eng/shellguard-lib/releases/download/v1.4.0/shellguard-1.4.0-py3-none-any.whl
```

Or run from a clone without installing:

```bash
git clone https://github.com/derbaroser-eng/shellguard-lib.git
cd shellguard-lib && PYTHONPATH=src python -c "import shellguard; print(shellguard.__version__)"
```

## API

- `run(argv, cwd=None, env=None, timeout=None, check=False)` -> `Result`
- `build(command, args)` -> argv list
- `quote(text)` -> POSIX single-quoted token (only for explicit shell mode)
- `audit(paths)` -> `Report(files_scanned, findings, errors)`; `scan_text(text)` -> findings; `render(finding)` -> one line
- `issue(customer, tier, secret)` -> signed commercial license key
- `verify(key, secret)` -> `License` (or raises `LicenseError`)
- `Timeout`, `SafetyError`, `LicenseError` exceptions
- `shell=True` is refused by design; a bare string command is refused by design.

## Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

111 contract tests: 26 real attack cases (parentheses, backticks, `$( )`, `;`,
`|`, `&&`, newline, quotes, globs, tilde, `$VAR`, redirection, unicode, empty
args, binary bytes, timeouts, cwd, env, exit codes, and stdout/stderr
separation) plus 16 license issuance and validation cases (forgery, wrong
issuer secret, expiry, tampered payload, format) plus 24 CLI cases (run, quote,
license, exit codes, entry point) plus 18 delivery cases (license issue, signed key, packaged artifact, email text, Stripe session handoff) plus 27 audit cases (shell=True, os.system/os.popen, asyncio.create_subprocess_shell, string argv, from-import names, import aliases, join/str-built argv, unparseable-source fallback, directory walk, excluded dirs, CLI exit codes).

## CI gate (GitHub Action)

The badge above is this repo's live self-audit: every push runs the published
action against `src`. Add the same gate to any repository:

```yaml
- uses: actions/checkout@v4
- uses: derbaroser-eng/shellguard-action@v1
  with:
    path: src
```

Exit 0 clean, 1 findings (build fails), 2 bad input. The release wheel is
sha256-verified before install. Action repo:
<https://github.com/derbaroser-eng/shellguard-action>.

## Commercial license

The MIT source is free forever. Companies that need to embed shellguard in a
proprietary product without MIT attribution buy a commercial license: a
packaged download plus an offline HMAC-SHA256 license key and email support.

```python
from shellguard.license import verify, LicenseError

try:
    lic = verify(key, issuer_secret)
except LicenseError as exc:
    print("not licensed:", exc)
```

See `LICENSE-COMMERCIAL.md`. Checkout and delivery are on the landing page:
<https://derbaroser-eng.github.io/shellguard/>.

## License

MIT. See LICENSE. The commercial tier is licensed separately; see
`LICENSE-COMMERCIAL.md`.
