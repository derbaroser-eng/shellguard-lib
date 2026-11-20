"""shellguard - run untrusted text as ARGUMENTS, never as shell syntax.

The bug this library exists to kill:
    full = f"cd {cd} && {oc} run --model {model} {prompt}"
A prompt containing "(" makes bash abort with
    syntax error near unexpected token `('
and a prompt containing backticks or $( ) executes attacker-chosen commands.

Rule: NEVER build a shell string from untrusted text. Build an argv list and let
execve-style semantics keep each token a token.
"""
from __future__ import annotations

import subprocess
from collections import namedtuple

__version__ = "1.0.0"
__all__ = ["run", "build", "quote", "Result", "Timeout", "SafetyError"]

Result = namedtuple("Result", ["returncode", "stdout", "stderr", "ok", "argv"])


class Timeout(Exception):
    """The command exceeded its time budget."""


class SafetyError(Exception):
    """A caller asked for an unsafe mode."""


def quote(text):
    """Single-quote one token for POSIX shells (used only by shell=True mode)."""
    return "'" + str(text).replace("'", "'\\''") + "'"


def build(command, args=()):
    """Return an argv list. Nothing here is ever parsed by a shell."""
    if not isinstance(command, (str, bytes)):
        raise TypeError("command must be a single program name")
    return [command] + [str(a) for a in (args or [])]


def run(argv, cwd=None, env=None, timeout=None, shell=False, check=False):
    """Run a command from an argv list. Untrusted text stays data.

    ``shell`` is opt-in and must be True explicitly; passing any other truthy
    marker (e.g. "required") raises, so the dangerous path cannot be the
    accidental default.
    """
    if shell is not False and shell is not True:
        raise ValueError("shell must be an explicit boolean; refusing to guess")
    if shell:
        raise SafetyError(
            "shell=True is refused: a shell parses untrusted text. "
            "Pass an argv list to run() instead.")

    if isinstance(argv, (str, bytes)):
        raise SafetyError(
            "a bare string command is refused: it would be shell-parsed. "
            "Pass a list, e.g. run(['echo', user_text]).")

    argv = [str(a) for a in argv]
    if not argv:
        raise ValueError("empty argv")

    real_env = None
    if env is not None:
        real_env = dict(env)

    try:
        proc = subprocess.run(
            argv, cwd=cwd, env=real_env, timeout=timeout,
            capture_output=True, text=True, errors="replace",
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired as exc:
        raise Timeout("command exceeded %ss: %r" % (timeout, argv[:2])) from exc

    res = Result(proc.returncode, proc.stdout or "", proc.stderr or "",
                 proc.returncode == 0, argv)
    if check and proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, argv,
                                            output=res.stdout, stderr=res.stderr)
    return res
