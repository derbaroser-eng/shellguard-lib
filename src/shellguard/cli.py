"""Command-line interface for shellguard.

``sg run`` executes a program with untrusted text kept as ARGUMENTS, so a token
like ``(`` or a backtick stays data instead of reaching a shell parser.
``sg quote`` renders an argv as a safely POSIX-quoted command line.
``sg license`` issues and verifies the offline commercial license keys.

Exit codes: 0 success, 1 command/license failure, 2 usage error.
"""
from __future__ import annotations

import json
import sys

from . import SafetyError, Timeout, quote, run
from .license import LicenseError, issue, verify
from .delivery import DeliveryError, delivery_email

USAGE = """usage:
  sg run [--cwd DIR] [--timeout SEC] -- PROG [ARG ...]
  sg quote TEXT [TEXT ...]
  sg license issue --customer EMAIL --tier commercial --secret SECRET
  sg license verify --key KEY --secret SECRET
  sg deliver --session FILE --secret SECRET --min-cents CENTS [--currency EUR]
  sg --version

`sg run` never builds a shell string: every ARG after -- is execve'd as data.
"""


def _out(text):
    sys.stdout.write(text)


def _err(text):
    sys.stderr.write(text)


def _cmd_run(argv):
    cwd = None
    timeout = None
    rest = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--":
            rest = argv[i + 1:]
            break
        if a in ("-h", "--help"):
            _out(USAGE)
            return 0
        if a == "--cwd":
            if i + 1 >= len(argv):
                _err("sg run: --cwd needs a value\n")
                return 2
            cwd = argv[i + 1]
            i += 2
            continue
        if a.startswith("--cwd="):
            cwd = a[len("--cwd="):]
            i += 1
            continue
        if a == "--timeout":
            if i + 1 >= len(argv):
                _err("sg run: --timeout needs a value\n")
                return 2
            try:
                timeout = float(argv[i + 1])
            except ValueError:
                _err("sg run: --timeout must be a number\n")
                return 2
            i += 2
            continue
        if a.startswith("--timeout="):
            try:
                timeout = float(a[len("--timeout="):])
            except ValueError:
                _err("sg run: --timeout must be a number\n")
                return 2
            i += 1
            continue
        _err("sg run: unknown option %r (put -- before the program)\n" % a)
        return 2
    if not rest:
        _err("sg run: missing program (sg run -- PROG [ARG ...])\n")
        return 2
    try:
        res = run(rest, cwd=cwd, timeout=timeout)
    except (SafetyError, Timeout, ValueError, OSError) as exc:
        _err("sg: %s\n" % exc)
        return 1
    if res.stdout:
        _out(res.stdout)
    if res.stderr:
        _err(res.stderr)
    return res.returncode


def _cmd_quote(argv):
    if not argv:
        _err("sg quote: missing TEXT\n")
        return 2
    if argv[0] in ("-h", "--help"):
        _out(USAGE)
        return 0
    _out(" ".join(quote(t) for t in argv) + "\n")
    return 0


def _cmd_license(argv):
    if not argv:
        _err("sg license: missing subcommand (issue|verify)\n")
        return 2
    sub = argv[0]
    if sub in ("-h", "--help"):
        _out(USAGE)
        return 0
    if sub not in ("issue", "verify"):
        _err("sg license: unknown subcommand %r\n" % sub)
        return 2
    opts = {}
    i = 1
    while i < len(argv):
        a = argv[i]
        if a in ("-h", "--help"):
            _out(USAGE)
            return 0
        if a.startswith("--"):
            if "=" in a:
                k, v = a[2:].split("=", 1)
            else:
                if i + 1 >= len(argv):
                    _err("sg license %s: %s needs a value\n" % (sub, a))
                    return 2
                k, v = a[2:], argv[i + 1]
                i += 1
            opts[k] = v
        else:
            _err("sg license %s: unexpected argument %r\n" % (sub, a))
            return 2
        i += 1
    if sub == "issue":
        for req in ("customer", "tier", "secret"):
            if req not in opts:
                _err("sg license issue: --%s is required\n" % req)
                return 2
        try:
            key = issue(opts["customer"], opts["tier"], opts["secret"])
        except LicenseError as exc:
            _err("sg license issue: %s\n" % exc)
            return 1
        _out(key + "\n")
        return 0
    for req in ("key", "secret"):
        if req not in opts:
            _err("sg license verify: --%s is required\n" % req)
            return 2
    try:
        lic = verify(opts["key"], opts["secret"])
    except LicenseError as exc:
        _err("sg license verify: %s\n" % exc)
        return 1
    _out("%s\t%s\t%s\n" % (lic.customer, lic.tier, lic.key))
    return 0


def _cmd_deliver(argv):
    """Fulful a paid Stripe Checkout session from a JSON event file."""
    nl = chr(10)
    opts = {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("-h", "--help"):
            _out(USAGE)
            return 0
        if a.startswith("--"):
            if "=" in a:
                k, v = a[2:].split("=", 1)
            else:
                if i + 1 >= len(argv):
                    _err("sg deliver: " + a + " needs a value" + nl)
                    return 2
                k, v = a[2:], argv[i + 1]
                i += 1
            opts[k] = v
        else:
            _err("sg deliver: unexpected argument " + repr(a) + nl)
            return 2
        i += 1
    for req in ("session", "secret", "min-cents"):
        if req not in opts:
            _err("sg deliver: --" + req + " is required" + nl)
            return 2
    try:
        min_cents = int(opts["min-cents"])
    except ValueError:
        _err("sg deliver: --min-cents must be an integer" + nl)
        return 2
    path = opts["session"]
    try:
        with open(path, "r", encoding="utf-8") as fh:
            event = json.load(fh)
    except OSError as exc:
        _err("sg deliver: cannot read " + path + ": " + str(exc) + nl)
        return 2
    except ValueError as exc:
        _err("sg deliver: invalid JSON in " + path + ": " + str(exc) + nl)
        return 2
    try:
        _d, body = delivery_email(event, opts["secret"], min_cents=min_cents,
                                  currency=opts.get("currency"))
    except DeliveryError as exc:
        _err("sg deliver: refused: " + str(exc) + nl)
        return 1
    _out(body)
    return 0

def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        _out(USAGE)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == "run":
        return _cmd_run(rest)
    if cmd == "quote":
        return _cmd_quote(rest)
    if cmd == "license":
        return _cmd_license(rest)
    if cmd == "deliver":
        return _cmd_deliver(rest)
    if cmd in ("--version", "version"):
        from . import __version__
        _out("shellguard %s\n" % __version__)
        return 0
    _err("sg: unknown command %r\n" % cmd)
    return 2


if __name__ == "__main__":
    sys.exit(main())
