"""W35 / C4.1: on AmigaOS, subprocess and os.execvp hand a bare command name
to ixemul's execve() first, which looks it up as AmigaDOS does (resident
list, then the shell's command path: C:, the `Path` list), and only then
try $PATH (os.defpath '/bin:/usr/bin' when PATH is unset).

The rig showed subprocess.run(["echo", ...]) failing with
FileNotFoundError(2): CPython only tried /bin/echo and /usr/bin/echo.

On the host, execve() of a bare name resolves against the current
directory, so a probe script in the cwd and NOT on $PATH shows which
lookup ran: found with sys.platform set to "amigaos", not found without.
The child processes are the host proof binary (patched Lib/).

Run: build/host/python.exe -m unittest -v tests/test_w35_exec_bare_name.py
"""
import os
import subprocess
import sys
import tempfile
import unittest

RUN = ("import subprocess, sys\n"
       "if {amiga}: sys.platform = 'amigaos'\n"
       "try:\n"
       "    r = subprocess.run([{name!r}], capture_output=True, text=True)\n"
       "    print('stdout=' + r.stdout.strip())\n"
       "except FileNotFoundError as e:\n"
       "    print('FileNotFoundError', e.errno)\n")
EXECVP = ("import os, sys\n"
          "if {amiga}: sys.platform = 'amigaos'\n"
          "try:\n"
          "    os.execvp({name!r}, [{name!r}])\n"
          "except FileNotFoundError as e:\n"
          "    print('FileNotFoundError', e.errno)\n")


class BareNameFirstOnAmigaOS(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        probe = os.path.join(self.dir.name, "w35probe")
        with open(probe, "w") as f:
            f.write("#!/bin/sh\necho probe-ok\n")
        os.chmod(probe, 0o755)

    def child(self, template, name, amiga):
        env = {"PATH": "/usr/bin:/bin"}  # the probe's directory is not on it
        out = subprocess.run([sys.executable, "-c", template.format(amiga=amiga, name=name)],
                             cwd=self.dir.name, env=env, capture_output=True, text=True)
        self.assertEqual(out.stderr, "")
        return out.stdout.strip()

    def test_subprocess_runs_a_bare_name_through_execve_on_amigaos(self):
        self.assertEqual(self.child(RUN, "w35probe", True), "stdout=probe-ok")

    def test_subprocess_bare_name_is_not_looked_up_in_cwd_elsewhere(self):
        self.assertEqual(self.child(RUN, "w35probe", False), "FileNotFoundError 2")

    def test_subprocess_still_searches_path_on_amigaos(self):
        self.assertEqual(self.child(RUN.replace("[{name!r}]", "[{name!r}, '-c', 'echo via-path']"),
                                    "sh", True), "stdout=via-path")

    def test_subprocess_unknown_name_still_fails_on_amigaos(self):
        self.assertEqual(self.child(RUN, "w35-no-such-command", True), "FileNotFoundError 2")

    def test_execvp_runs_a_bare_name_through_execve_on_amigaos(self):
        self.assertEqual(self.child(EXECVP, "w35probe", True), "probe-ok")

    def test_execvp_bare_name_is_not_looked_up_in_cwd_elsewhere(self):
        self.assertEqual(self.child(EXECVP, "w35probe", False), "FileNotFoundError 2")

    def test_execvp_unknown_name_still_fails_on_amigaos(self):
        self.assertEqual(self.child(EXECVP, "w35-no-such-command", True), "FileNotFoundError 2")


class DefaultExecPathOnAmigaOS(unittest.TestCase):
    """With PATH unset, the exec lookup walks os.defpath. On AmigaOS it is
    ixemul's _PATH_DEFPATH "/usr/bin:/bin:/c": C: holds the AmigaDOS
    commands (C:Which), and ixemul's execve() of a bare name walks only the
    shell's Path list, which need not contain C: (the rig's did not: the
    sentinel's `which which` was FileNotFoundError(2) after patch 0010)."""

    def exec_path(self, amiga):
        code = ("import sys, importlib\n"
                "if {amiga}: sys.platform = 'amigaos'\n"
                "import posixpath, os\n"
                "importlib.reload(posixpath); importlib.reload(os)\n"
                "print(os.defpath, os.get_exec_path({{}}))\n").format(amiga=amiga)
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        self.assertEqual(out.stderr, "")
        return out.stdout.strip()

    def test_amigaos_default_path_reaches_c(self):
        self.assertEqual(self.exec_path(True), "/usr/bin:/bin:/c ['/usr/bin', '/bin', '/c']")

    def test_posix_default_path_unchanged(self):
        self.assertEqual(self.exec_path(False), "/bin:/usr/bin ['/bin', '/usr/bin']")


if __name__ == "__main__":
    unittest.main()
