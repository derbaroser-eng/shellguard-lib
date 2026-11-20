# shellguard

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

sg.run(["echo", "(17*23)"])          # -> "391\n"
sg.run(["echo", "`echo INJECTED`"])  # -> "`echo INJECTED`\n"  (data, not a command)
sg.run(["echo", "$(rm -rf /)"])      # -> literal text
sg.run(["false"])                    # Result(returncode=1, ok=False, ...)
```

## Install

```bash
pip install shellguard
```

Zero dependencies. Python 3.8+.

## API

- `run(argv, cwd=None, env=None, timeout=None, check=False)` -> `Result`
- `build(command, args)` -> argv list
- `quote(text)` -> POSIX single-quoted token (only for explicit shell mode)
- `Timeout`, `SafetyError` exceptions
- `shell=True` is refused by design; a bare string command is refused by design.

## Tests

```bash
python tests/test_shellguard.py
```

27 real attack cases: parentheses, backticks, `$( )`, `;`, `|`, `&&`, newline,
quotes, globs, tilde, `$VAR`, redirection, unicode, empty args, binary bytes,
timeouts, cwd, env, exit codes, and stdout/stderr separation.

## License

MIT. See LICENSE.
