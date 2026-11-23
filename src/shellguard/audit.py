"""Static audit for shell-injection bugs in Python source.

`sg run` keeps untrusted text as argv data at the call site. This module finds
the call sites that do NOT: `shell=True`, `os.system`/`os.popen`, and subprocess
calls whose first argument is a string instead of an argv list.

AST-based, stdlib only, no third-party dependency. Unparseable files fall back
to a line scan so a syntax error never silently hides a finding.
"""
from __future__ import annotations

import ast
import os
import re
from collections import namedtuple

__all__ = ["Finding", "Report", "AuditError", "RULES", "scan_text",
           "scan_file", "audit", "render"]

SHELL_TRUE = "SG001"
OS_EXEC = "SG002"
STRING_ARGV = "SG003"
ASYNC_SHELL = "SG004"
SHELL_ARGV_C = "SG005"

RULES = {
    SHELL_TRUE: "shell=True hands untrusted text to a shell parser",
    OS_EXEC: "os.system/os.popen builds a command string for a shell",
    STRING_ARGV: "subprocess call passes a string, not an argv list",
    ASYNC_SHELL: "asyncio.create_subprocess_shell runs a command string through a shell",
    SHELL_ARGV_C: "argv invokes a shell with -c on a non-literal command",
}

Finding = namedtuple("Finding", ["file", "line", "col", "rule", "code"])
Report = namedtuple("Report", ["files_scanned", "findings", "errors"])


class AuditError(Exception):
    """A path could not be audited."""


_SUBPROCESS_FUNCS = frozenset([
    "run", "call", "check_call", "check_output", "Popen", "getoutput",
    "getstatusoutput",
])
_OS_EXEC = frozenset(["system", "popen"])
_DEFAULT_EXCLUDE = frozenset([
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv",
    "env", ".tox", ".mypy_cache", ".pytest_cache", "dist", "build",
])
_SHELLS = frozenset([
    "sh", "bash", "dash", "zsh", "ksh", "fish", "csh", "tcsh",
    "cmd", "powershell", "pwsh",
])
_SHELL_C_SWITCHES = frozenset(["-c", "/c", "-lc", "-xc", "-ec", "-fc"])
_QUOTES = frozenset([chr(34), chr(39)])


def _shell_c_command(node, short):
    """Return the command expr when argv shells out with ``-c``, else None.

    ``subprocess.run(['sh', '-c', cmd])`` has a safe-looking argv list but still
    hands ``cmd`` to a shell parser. A literal command is safe by definition,
    so only a non-literal command expression is reported.
    """
    argv = node.args
    if argv and isinstance(argv[0], (ast.List, ast.Tuple)):
        if short not in _SUBPROCESS_FUNCS:
            return None
        argv = argv[0].elts
    elif short != "create_subprocess_exec":
        return None
    if len(argv) < 3:
        return None
    prog = argv[0]
    if not isinstance(prog, ast.Constant) or not isinstance(prog.value, str):
        return None
    base = prog.value.replace("\\", "/").rsplit("/", 1)[-1].lower()
    if base.endswith(".exe"):
        base = base[:-4]
    if base not in _SHELLS:
        return None
    for i, item in enumerate(argv[:-1]):
        if isinstance(item, ast.Constant) and isinstance(item.value, str) \
                and item.value.lower() in _SHELL_C_SWITCHES:
            command = argv[i + 1]
            if isinstance(command, ast.Constant) and isinstance(command.value, str):
                return None
            return command
    return None


def _dotted(node):
    """Render ``subprocess.run`` from an Attribute chain, else ''."""
    parts = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
    return ".".join(reversed(parts))


def _stringy(node):
    """True when an expression builds a string rather than a list/tuple."""
    if isinstance(node, ast.Constant):
        return isinstance(node.value, str)
    if isinstance(node, (ast.JoinedStr, ast.BinOp)):
        return True
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Name) and func.id == "str":
            return True
        if isinstance(func, ast.Attribute) and func.attr in ("join", "format"):
            return True
        return _dotted(func).endswith("format")
    return False


def _resolve(dotted, aliases):
    """Resolve the leading name of a dotted call through import aliases."""
    if not dotted:
        return dotted
    head, _, rest = dotted.partition(".")
    target = aliases.get(head)
    if target is None:
        return dotted
    return target + ("." + rest if rest else "")


def _aliases(tree):
    """Map local names to fully-qualified targets from import statements."""
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                if name.asname:
                    aliases[name.asname] = name.name
                else:
                    head = name.name.split(".")[0]
                    aliases.setdefault(head, head)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for name in node.names:
                if name.name == "*":
                    continue
                local = name.asname or name.name
                aliases[local] = module + "." + name.name if module else name.name
    return aliases


def _from_call(node, aliases):
    """Rule violated by an ast.Call, or None."""
    func = node.func
    dotted = _resolve(_dotted(func), aliases)
    short = dotted.rsplit(".", 1)[-1]
    bare = func.id if isinstance(func, ast.Name) else None

    if dotted in ("os.system", "os.popen") or bare in _OS_EXEC:
        return OS_EXEC
    if dotted in ("subprocess.getoutput", "subprocess.getstatusoutput"):
        return OS_EXEC
    if short == "create_subprocess_shell":
        return ASYNC_SHELL
    if short in _SUBPROCESS_FUNCS or bare in _SUBPROCESS_FUNCS:
        for kw in node.keywords:
            if kw.arg == "shell" and isinstance(kw.value, ast.Constant) \
                    and kw.value.value is True:
                return SHELL_TRUE
        if node.args and _stringy(node.args[0]):
            return STRING_ARGV
    if (short in _SUBPROCESS_FUNCS or bare in _SUBPROCESS_FUNCS
            or short == "create_subprocess_exec") \
            and _shell_c_command(node, short) is not None:
        return SHELL_ARGV_C
    return None


def _fallback_shell_c(compact):
    """True when a line shells out through an argv ``-c`` on a live command."""
    for sh in _SHELLS:
        for q in ("'", '"'):
            for needle in (q + sh + q, "/" + sh + q, q + sh + ".exe" + q):
                pos = compact.find(needle)
                if pos < 0:
                    continue
                for sw in _SHELL_C_SWITCHES:
                    for sq in ("'", '"'):
                        token = sq + sw + sq
                        swpos = compact.find(token, pos)
                        if swpos < 0:
                            continue
                        rest = compact[swpos + len(token):]
                        if not rest.startswith(","):
                            continue
                        cmd = rest[1:]
                        if cmd[:1] in ("'", '"'):
                            continue
                        if (len(cmd) > 1 and cmd[0] in "rRuUbBfF"
                                and cmd[1] in _QUOTES):
                            continue
                        return True
    return False


def _regex_fallback(text):
    """Line scan for source that does not parse.

    All five rules stay reachable here: a syntax error must never hide a
    finding. The scan trades precision for coverage, so unusual formatting
    can over-report, but a dangerous call is not silently dropped.
    """
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        found = False
        if re.search(r"\bshell\s*=\s*True\b", line):
            out.append((i, line.find("shell") + 1, SHELL_TRUE, line.strip()))
            found = True
        elif re.search(r"\bos\.(system|popen)\s*\(", line):
            out.append((i, line.find("os.") + 1, OS_EXEC, line.strip()))
            found = True
        if found:
            continue
        compact = "".join(line.split())
        if "create_subprocess_shell(" in compact:
            out.append((i, compact.find("create_subprocess_shell(") + 1,
                        ASYNC_SHELL, stripped))
            continue
        for name in _SUBPROCESS_FUNCS:
            pos = compact.find(name + "(")
            if pos < 0:
                continue
            arg = compact[pos + len(name) + 1:pos + len(name) + 4]
            if arg[:1] in ("'", '"') or (len(arg) > 1
                    and arg[0] in "rRuUbBfF" and arg[1] in ("'", '"')):
                out.append((i, line.find(name) + 1, STRING_ARGV, stripped))
                break
        if out and out[-1][0] == i and out[-1][2] == STRING_ARGV:
            continue
        if _fallback_shell_c(compact):
            out.append((i, line.find("-c") + 1, SHELL_ARGV_C, stripped))
    return out


def scan_text(text, filename="<text>"):
    """Return a list of :class:`Finding` for one source file's text."""
    findings = []
    try:
        tree = ast.parse(text, filename=filename)
    except SyntaxError:
        for line, col, rule, code in _regex_fallback(text):
            findings.append(Finding(filename, line, col, rule, code))
        return findings

    aliases = _aliases(tree)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        rule = _from_call(node, aliases)
        if rule is None:
            continue
        code = ""
        try:
            code = ast.get_source_segment(text, node) or ""
        except Exception:
            code = ""
        code = " ".join(code.split())[:120]
        findings.append(Finding(filename, node.lineno, node.col_offset + 1,
                                rule, code))
    findings.sort(key=lambda f: (f.line, f.col, f.rule))
    return findings


def scan_file(path):
    """Return findings for one file, or raise AuditError if unreadable."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        raise AuditError("%s: %s" % (path, exc)) from exc
    return scan_text(text, filename=path)


def _iter_files(paths, exclude):
    for path in paths:
        if os.path.isfile(path):
            yield path
            continue
        if not os.path.isdir(path):
            raise AuditError("no such file or directory: %s" % path)
        for root, dirs, files in os.walk(path):
            dirs[:] = sorted(d for d in dirs
                             if d not in exclude and not d.startswith("."))
            for name in sorted(files):
                if name.endswith((".py", ".pyw")):
                    yield os.path.join(root, name)


def audit(paths, *, exclude=_DEFAULT_EXCLUDE):
    """Audit every Python file under ``paths``.

    Returns a :class:`Report`. ``errors`` holds unreadable paths; it is not a
    failure of the audit itself.
    """
    findings, errors, scanned = [], [], 0
    for path in _iter_files(list(paths), frozenset(exclude)):
        scanned += 1
        try:
            findings.extend(scan_file(path))
        except AuditError as exc:
            errors.append(str(exc))
    findings.sort(key=lambda f: (f.file, f.line, f.col, f.rule))
    return Report(scanned, findings, errors)


def render(finding):
    """One human-readable finding line."""
    return "%s:%d:%d: %s %s" % (finding.file, finding.line, finding.col,
                                finding.rule, RULES[finding.rule])
