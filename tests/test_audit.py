"""Contract tests for shellguard.audit and the `sg audit` CLI.

Every test runs against real source text and real temp files - no mocking, no
network. The negative cases matter as much as the positive ones: a scanner that
flags safe argv lists would be worse than no scanner.
"""
import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest

from shellguard import audit as A
from shellguard import cli


def run_cli(args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = cli.main(list(args))
    return rc, out.getvalue(), err.getvalue()


class ScanTextTests(unittest.TestCase):
    def test_shell_true_is_flagged(self):
        f = A.scan_text("import subprocess\nsubprocess.run(['ls'], shell=True)\n")
        self.assertEqual([x.rule for x in f], [A.SHELL_TRUE])
        self.assertEqual(f[0].line, 2)

    def test_string_argv_is_flagged(self):
        f = A.scan_text("import subprocess\nsubprocess.run('ls')\n")
        self.assertEqual([x.rule for x in f], [A.STRING_ARGV])

    def test_fstring_argv_is_flagged(self):
        f = A.scan_text("import subprocess\nsubprocess.run(f'ls {d}')\n")
        self.assertEqual([x.rule for x in f], [A.STRING_ARGV])

    def test_os_system_and_popen_are_flagged(self):
        f = A.scan_text("import os\nos.system('ls')\nos.popen('ls')\n")
        self.assertEqual([x.rule for x in f], [A.OS_EXEC, A.OS_EXEC])

    def test_asyncio_shell_is_flagged(self):
        f = A.scan_text("import asyncio\n"
                        "asyncio.create_subprocess_shell('ls')\n")
        self.assertEqual([x.rule for x in f], [A.ASYNC_SHELL])
        self.assertEqual(f[0].line, 2)

    def test_asyncio_exec_is_not_flagged(self):
        f = A.scan_text("import asyncio\n"
                        "asyncio.create_subprocess_exec('ls', '-l')\n")
        self.assertEqual(f, [])

    def test_bare_from_import_name_is_flagged(self):
        f = A.scan_text("from subprocess import run\nrun('ls')\n")
        self.assertEqual([x.rule for x in f], [A.STRING_ARGV])

    def test_list_argv_is_not_flagged(self):
        f = A.scan_text("import subprocess\n"
                        "subprocess.run(['ls', user])\n"
                        "subprocess.run(['sh', '-c', 'true'])\n")
        self.assertEqual(f, [])

    def test_variable_argv_is_not_flagged(self):
        self.assertEqual(A.scan_text("import subprocess\nsubprocess.run(cmd)\n"), [])

    def test_unparseable_source_falls_back_to_line_scan(self):
        f = A.scan_text("def broken(:\nsubprocess.run('x', shell=True)\n")
        self.assertIn(A.SHELL_TRUE, [x.rule for x in f])

    def test_render_is_one_positional_line(self):
        f = A.Finding("a.py", 3, 5, A.SHELL_TRUE, "x")
        self.assertEqual(A.render(f),
                         "a.py:3:5: SG001 " + A.RULES[A.SHELL_TRUE])

    def test_aliased_os_system_is_flagged(self):
        f = A.scan_text("""import os as o
o.system('ls')
""")
        self.assertEqual([x.rule for x in f], [A.OS_EXEC])

    def test_aliased_os_popen_is_flagged(self):
        f = A.scan_text("""import os as os2
os2.popen('ls')
""")
        self.assertEqual([x.rule for x in f], [A.OS_EXEC])

    def test_aliased_from_import_async_shell_is_flagged(self):
        f = A.scan_text("""from asyncio import create_subprocess_shell as c
c('ls')
""")
        self.assertEqual([x.rule for x in f], [A.ASYNC_SHELL])

    def test_join_string_argv_is_flagged(self):
        f = A.scan_text("""import subprocess
subprocess.run(' '.join(['ls', 'x']))
""")
        self.assertEqual([x.rule for x in f], [A.STRING_ARGV])

    def test_str_call_argv_is_flagged(self):
        f = A.scan_text("""import subprocess
subprocess.run(str(cmd))
""")
        self.assertEqual([x.rule for x in f], [A.STRING_ARGV])

    def test_unrelated_alias_is_not_flagged(self):
        self.assertEqual(A.scan_text("""import os as o
o.getcwd()
"""), [])


class AuditPathsTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def _write(self, rel, text):
        path = os.path.join(self.d, rel)
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def test_audit_collects_findings_across_files(self):
        self._write("bad.py", "import os\nos.system('ls')\n")
        self._write("bad2.py", "import subprocess\nsubprocess.run('ls')\n")
        rep = A.audit([self.d])
        self.assertEqual(rep.files_scanned, 2)
        self.assertEqual(len(rep.findings), 2)

    def test_audit_skips_excluded_directories(self):
        self._write(os.path.join("__pycache__", "junk.py"),
                    "import os\nos.system('ls')\n")
        self._write(os.path.join(".git", "hook.py"),
                    "import os\nos.system('ls')\n")
        rep = A.audit([self.d])
        self.assertEqual(rep.files_scanned, 0)
        self.assertEqual(rep.findings, [])

    def test_audit_ignores_non_python_files(self):
        self._write("notes.txt", "os.system('ls')\n")
        rep = A.audit([self.d])
        self.assertEqual(rep.files_scanned, 0)

    def test_audit_missing_path_raises(self):
        with self.assertRaises(A.AuditError):
            A.audit([os.path.join(self.d, "nope")])


class AuditCliTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def _write(self, name, text):
        path = os.path.join(self.d, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def test_clean_source_exits_zero(self):
        p = self._write("ok.py", "import subprocess\nsubprocess.run(['ls'])\n")
        rc, out, err = run_cli(["audit", p])
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")

    def test_findings_exit_one_and_print_positions(self):
        p = self._write("bad.py", "import os\nos.system('ls')\n")
        rc, out, err = run_cli(["audit", p])
        self.assertEqual(rc, 1)
        self.assertIn("SG002", out)
        self.assertIn("%s:2" % p.replace(os.sep, os.sep), out)

    def test_json_output_is_parseable(self):
        p = self._write("bad.py", "import os\nos.system('ls')\n")
        rc, out, err = run_cli(["audit", "--json", p])
        data = json.loads(out)
        self.assertEqual(rc, 1)
        self.assertEqual(data["files_scanned"], 1)
        self.assertEqual(data["findings"][0]["rule"], "SG002")
        self.assertEqual(data["findings"][0]["line"], 2)

    def test_missing_path_argument_exits_two(self):
        rc, out, err = run_cli(["audit"])
        self.assertEqual(rc, 2)

    def test_nonexistent_path_exits_two(self):
        rc, out, err = run_cli(["audit", os.path.join(self.d, "nope.py")])
        self.assertEqual(rc, 2)

    def test_unknown_option_exits_two(self):
        rc, out, err = run_cli(["audit", "--wat", "x.py"])
        self.assertEqual(rc, 2)
