"""Contract tests for the shellguard CLI (`sg`)."""
import contextlib
import io
import os
import subprocess
import sys
import unittest

from shellguard import cli


def run_cli(args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = cli.main(list(args))
    return rc, out.getvalue(), err.getvalue()


class TestRun(unittest.TestCase):
    def test_run_keeps_parentheses_as_data(self):
        rc, out, err = run_cli(["run", "--", "echo", "(17*23)"])
        self.assertEqual(rc, 0)
        self.assertEqual(out, "(17*23)\n")

    def test_run_returns_command_exit_code(self):
        rc, out, err = run_cli(["run", "--", "false"])
        self.assertEqual(rc, 1)

    def test_run_stderr_is_separated_from_stdout(self):
        rc, out, err = run_cli([
            "run", "--", sys.executable, "-c",
            "import sys; sys.stdout.write('O'); sys.stderr.write('E')",
        ])
        self.assertEqual(rc, 0)
        self.assertEqual(out, "O")
        self.assertEqual(err, "E")

    def test_run_missing_program_is_usage_error(self):
        rc, out, err = run_cli(["run"])
        self.assertEqual(rc, 2)
        self.assertIn("missing program", err)

    def test_run_unknown_option_is_usage_error(self):
        rc, out, err = run_cli(["run", "--bogus", "--", "echo", "x"])
        self.assertEqual(rc, 2)

    def test_run_bad_timeout_is_usage_error(self):
        rc, out, err = run_cli(["run", "--timeout", "abc", "--", "echo", "x"])
        self.assertEqual(rc, 2)

    def test_run_missing_cwd_reports_failure(self):
        rc, out, err = run_cli([
            "run", "--cwd", os.path.join("no", "such", "dir"), "--", "echo", "x",
        ])
        self.assertEqual(rc, 1)


class TestQuote(unittest.TestCase):
    def test_quote_wraps_a_single_token(self):
        rc, out, err = run_cli(["quote", "a b"])
        self.assertEqual(rc, 0)
        self.assertEqual(out, "'a b'\n")

    def test_quote_joins_multiple_tokens(self):
        rc, out, err = run_cli(["quote", "a b", "c"])
        self.assertEqual(rc, 0)
        self.assertEqual(out, "'a b' 'c'\n")

    def test_quote_escapes_an_embedded_quote(self):
        import shlex
        token = "a" + chr(39) + "b"
        rc, out, err = run_cli(["quote", token])
        self.assertEqual(rc, 0)
        self.assertTrue(out.startswith(chr(39))
                        and out.endswith(chr(39) + chr(10)))
        self.assertIn(chr(92), out)
        self.assertEqual(shlex.split(out), [token])

    def test_quote_missing_text_is_usage_error(self):
        rc, out, err = run_cli(["quote"])
        self.assertEqual(rc, 2)


class TestLicense(unittest.TestCase):
    def test_issue_then_verify_roundtrip(self):
        rc, out, err = run_cli([
            "license", "issue", "--customer", "acme@example.com",
            "--tier", "commercial", "--secret", "s3cret",
        ])
        self.assertEqual(rc, 0)
        key = out.strip()
        self.assertTrue(key.startswith("SG1-"))
        rc2, out2, err2 = run_cli([
            "license", "verify", "--key", key, "--secret", "s3cret",
        ])
        self.assertEqual(rc2, 0)
        self.assertIn("acme@example.com", out2)

    def test_verify_forged_key_fails(self):
        rc, out, err = run_cli([
            "license", "verify", "--key", "SG1-bogus", "--secret", "s3cret",
        ])
        self.assertEqual(rc, 1)

    def test_issue_missing_option_is_usage_error(self):
        rc, out, err = run_cli(["license", "issue", "--customer", "acme"])
        self.assertEqual(rc, 2)

    def test_license_unknown_subcommand_is_usage_error(self):
        rc, out, err = run_cli(["license", "frobnicate"])
        self.assertEqual(rc, 2)


class TestTopLevel(unittest.TestCase):
    def test_no_args_prints_usage(self):
        rc, out, err = run_cli([])
        self.assertEqual(rc, 0)
        self.assertIn("usage", out.lower())

    def test_unknown_command_is_usage_error(self):
        rc, out, err = run_cli(["frobnicate"])
        self.assertEqual(rc, 2)

    def test_version(self):
        rc, out, err = run_cli(["--version"])
        self.assertEqual(rc, 0)
        self.assertIn("shellguard", out)


class TestEntrypoint(unittest.TestCase):
    def test_module_entrypoint_runs_with_local_src(self):
        env = dict(os.environ)
        src = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
        env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
        p = subprocess.run(
            [sys.executable, "-m", "shellguard.cli", "quote", "a b"],
            capture_output=True, text=True, env=env,
        )
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "'a b'\n")
