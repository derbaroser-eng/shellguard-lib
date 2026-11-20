"""Real attack suite for shellguard - stdlib only, zero dependencies.

Every test encodes a real failure mode observed in this system:
    bash: syntax error near unexpected token `('
    `echo INJECTED` executed
    $(echo INJECTED2) executed
A command builder that interpolates text into a shell string fails all of these.

Run:  python tests/test_shellguard.py
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import shellguard as sg  # noqa: E402


def out(argv, **kw):
    """Run and return stdout only, for quoting assertions."""
    return sg.run(argv, **kw).stdout



class TestQuoting(unittest.TestCase):
    def test_parentheses_do_not_break_parsing(self):
        """The exact bug: an unquoted '(' is a bash syntax error."""
        self.assertEqual(out(["echo", "(17*23)"]), "(17*23)\n")

    def test_backticks_are_data_not_commands(self):
        self.assertEqual(out(["echo", "`echo INJECTED`"]), "`echo INJECTED`\n")

    def test_dollar_parens_are_data_not_commands(self):
        self.assertEqual(out(["echo", "$(echo INJECTED2)"]), "$(echo INJECTED2)\n")

    def test_semicolon_does_not_chain_commands(self):
        self.assertEqual(out(["echo", "; rm -rf /"]), "; rm -rf /\n")

    def test_pipe_does_not_pipe(self):
        self.assertEqual(out(["echo", "| cat"]), "| cat\n")

    def test_ampersand_does_not_background(self):
        self.assertEqual(out(["echo", "&& touch /tmp/pwned"]), "&& touch /tmp/pwned\n")

    def test_newline_does_not_start_a_new_command(self):
        self.assertEqual(out(["echo", "\necho HACKED"]), "\necho HACKED\n")

    def test_single_quote_token_is_preserved(self):
        """MSYS2 strips an embedded apostrophe; the library must not."""
        self.assertEqual(sg.build("echo", ["it's"]), ["echo", "it's"])

    def test_double_quotes_are_data(self):
        self.assertEqual(out(["echo", 'say "hi"']), 'say "hi"\n')

    def test_glob_is_passed_through_untouched(self):
        """MSYS2 expands `*` in argv before exec; that is OS behaviour.

        The library contract is that it never expands anything itself.
        """
        self.assertEqual(sg.build("echo", ["*"]), ["echo", "*"])

    def test_tilde_is_passed_through_untouched(self):
        """MSYS2 rewrites `~` to the home path; the library must not."""
        self.assertEqual(sg.build("echo", ["~"]), ["echo", "~"])

    def test_env_expansion_is_not_evaluated(self):
        self.assertEqual(out(["echo", "$HOME"]), "$HOME\n")

    def test_redirection_does_not_write(self):
        self.assertEqual(out(["echo", "> /tmp/should_not_exist"]), "> /tmp/should_not_exist\n")

    def test_unicode_and_spaces_survive(self):
        self.assertEqual(out(["echo", "h\u00e9llo w\u00f6rld"]), "h\u00e9llo w\u00f6rld\n")

    def test_empty_argument_is_preserved(self):
        self.assertEqual(out(["echo", "", "x"]), " x\n")

    def test_binary_bytes_survive(self):
        self.assertEqual(out(["printf", "%s", "a\x01b"]), "a\x01b")


class TestContract(unittest.TestCase):
    def test_result_object_carries_real_exit_code(self):
        r = sg.run(["false"])
        self.assertEqual(r.returncode, 1)
        self.assertFalse(r.ok)

    def test_stdout_and_stderr_are_separate(self):
        r = sg.run(["sh", "-c", "echo out; echo err >&2"])
        self.assertEqual(r.stdout, "out\n")
        self.assertEqual(r.stderr, "err\n")

    def test_nonexistent_command_raises_never_a_shell(self):
        with self.assertRaises(FileNotFoundError):
            sg.run(["definitely-not-a-real-binary-xyz"])

    def test_shell_injection_via_command_name_is_impossible(self):
        with self.assertRaises(FileNotFoundError):
            sg.run(["echo hi; rm -rf /"])

    def test_timeout_is_enforced(self):
        with self.assertRaises(sg.Timeout):
            sg.run(["sleep", "5"], timeout=0.3)

    def test_working_directory_is_respected(self):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "marker.txt"), "w").write("M")
            r = sg.run(["ls"], cwd=d)
            self.assertIn("marker.txt", r.stdout)

    def test_environment_is_passthrough(self):
        r = sg.run(["sh", "-c", "echo $SHELLGUARD_PROBE"], env={"SHELLGUARD_PROBE": "env-ok"})
        self.assertEqual(r.stdout, "env-ok\n")


class TestHelpers(unittest.TestCase):
    def test_quote_helper_roundtrips(self):
        self.assertEqual(sg.quote("(a;b)"), "'(a;b)'")

    def test_build_returns_argv_not_a_shell_string(self):
        self.assertEqual(sg.build("echo", ["(1+2)"]), ["echo", "(1+2)"])

    def test_shell_mode_is_explicit_and_opt_in(self):
        with self.assertRaises(ValueError):
            sg.run(["echo (1+2)"], shell="required")


if __name__ == "__main__":
    unittest.main(verbosity=2)
