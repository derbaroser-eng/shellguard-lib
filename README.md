# shellguard

[![shellguard self-audit](https://github.com/derbaroser-eng/shellguard-lib/actions/workflows/shellguard-audit.yml/badge.svg)](https://github.com/derbaroser-eng/shellguard-lib/actions/workflows/shellguard-audit.yml)

Run untrusted text as **arguments**, never as shell syntax. Zero dependencies, Python 3.8+.

## The bug this exists to prevent

```python
full = f"cd {cd} && {oc} run --model {model} {prompt}"
```

I have watched that line fail in production. A prompt containing `(` made bash abort with a syntax error. A prompt containing backticks or `$( )` would have executed commands chosen by whoever typed the prompt. Both came from ordinary user input, not an attacker — which is the part that should worry you.

## The rule

Never build a shell string from text you do not control. Build an argv list instead. With `execve` semantics, every element is one token, so parentheses, backticks, pipes, semicolons and newlines stay data.

## Usage

```python
import shellguard as sg

sg.run(["echo", "(17*23)"])            # -> "(17*23)\n"
sg.run(["echo", "`echo INJECTED`"])    # -> "`echo INJECTED`\n"  — data, not a command
sg.run(["echo", "$(touch pwned)"])     # -> literal text; no file is written
sg.run(["false"])                      # -> Result(returncode=1, ok=False, ...)
```

There is no escaping step and no denylist. If a value needs to become an option, validate its shape or place it after `--` where the tool supports it — an argv list fixes shell injection, not CWE-88 argument injection.

## Install

The `shellguard` name on PyPI belongs to an unrelated package, so install the release wheel directly:

```bash
pip install https://github.com/derbaroser-eng/shellguard-lib/releases/download/v1.5.1/shellguard-1.5.1-py3-none-any.whl
```

Or from a clone, without installing:

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

140 tests, all green — 125 contract tests and 15 meta-tests that keep the public pages honest. The contract suite is 26 real attack cases, 16 license issuance cases, 24 CLI cases, 18 delivery cases and 41 audit cases. The attack cases cover parentheses, backticks, `$( )`, `;`, `|`, `&&`, newline, quotes, globs, tilde, `$VAR`, redirection, unicode, empty args, binary bytes, timeouts, cwd, env, exit codes, and stdout/stderr separation. The audit cases include SG005: an argv list like `['sh', '-c', cmd]` still hands the command to a shell parser when cmd comes from untrusted text.

The test suite is the product as much as the library is: it turns "we hope the prompt is clean" into "the prompt cannot be parsed as syntax."

## CI gate

The badge above is this repo's live self-audit — every push runs the published action against `src`. Add the same gate to your own repository:

```yaml
- uses: actions/checkout@v4
- uses: derbaroser-eng/shellguard-action@v1
  with:
    path: src
```

Exit 0 clean, 1 on findings (build fails), 2 on bad input. The release wheel is sha256-verified before install. Action repo: <https://github.com/derbaroser-eng/shellguard-action>.

## Field note

I wrote up the production failure and the quieter CWE-88 cases in [A parenthesis broke our command](https://derbaroser-eng.github.io/shellguard/why-argv/). It is a proper write-up, not a sales page.


I also wrote [A CI gate for the shell-injection bug that shell=False doesn't fix](https://dev.to/aurum_revenue/a-ci-gate-for-the-shell-injection-bug-that-shellfalse-doesnt-fix-2inf) — the three cases I keep finding in review, and the limits the scanner reports honestly.

## Commercial license

The MIT source is free forever. Companies that want to embed shellguard in a proprietary product without MIT attribution buy a commercial license: packaged source, an offline HMAC-SHA256 license key, and email support.

```python
from shellguard.license import verify, LicenseError

try:
    lic = verify(key, issuer_secret)
except LicenseError as exc:
    print("not licensed:", exc)
```

See `LICENSE-COMMERCIAL.md`. Checkout and delivery are on the product page: <https://derbaroser-eng.github.io/shellguard/>.

## Limitations (restated in every report)

Taint is intra-file and intra-function. An argv token is reported only where the hazard is provable from its own literals. Non-literal `shell=` is handled conservatively. Unsupported languages, parse failures, binary and oversized files are reported as skipped with reasons — never silently dropped. This tool does not claim compliance, certification or a guarantee; it produces dated evidence and says what it could not see.

## License

MIT. See LICENSE. The commercial tier is licensed separately; see `LICENSE-COMMERCIAL.md`.
