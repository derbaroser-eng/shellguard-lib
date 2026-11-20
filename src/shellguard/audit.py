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

RULES = {
    SHELL_TRUE: "shell=True hands untrusted text to a shell parser",
    OS_EXEC: "os.system/os.popen builds a command string for a shell",
    STRING_ARGV: "subprocess call passes a string, not an argv list",
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
        return _dotted(node.func).endswith("format")
    return False


def _from_call(node):
    """Rule violated by an ast.Call, or None."""
    func = node.func
    dotted = _dotted(func)
    short = dotted.rsplit(".", 1)[-1]
    bare = func.id if isinstance(func, ast.Name) else None

    if dotted in ("os.system", "os.popen") or bare in _OS_EXEC:
        return OS_EXEC
    if dotted in ("subprocess.getoutput", "subprocess.getstatusoutput"):
        return OS_EXEC
    if short in _SUBPROCESS_FUNCS or bare in _SUBPROCESS_FUNCS:
        for kw in node.keywords:
            if kw.arg == "shell" and isinstance(kw.value, ast.Constant) \
                    and kw.value.value is True:
                return SHELL_TRUE
        if node.args and _stringy(node.args[0]):
            return STRING_ARGV
    return None


def _regex_fallback(text):
    """Line scan for files that do not parse."""
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        if re.search(r"\bshell\s*=\s*True\b", line):
            out.append((i, line.find("shell") + 1, SHELL_TRUE, line.strip()))
        elif re.search(r"\bos\.(system|popen)\s*\(", line):
            out.append((i, line.find("os.") + 1, OS_EXEC, line.strip()))
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

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        rule = _from_call(node)
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
