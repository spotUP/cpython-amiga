"""W35: _Py_abspath() joins a relative path to a current directory that
already ends with '/' without doubling it. ixemul's getcwd() returns
"/Ram Disk/" in a volume's root, and the rig showed sys.executable =
'/Ram Disk//Python3:bin/python3'; on the host the root directory "/" shows
the same join ("//Users/...").

The AmigaDOS-absolute part ("Python3:bin/python3" -> "/Python3/bin/python3")
is Amiga-only: its pure helpers are tests/amiga_path_test.c
(make test-amiga-path), the rest is the rig's sentinel.

Run: build/host/python.exe -m unittest -v tests/test_w35_abspath.py
"""
import os
import subprocess
import sys
import tempfile
import unittest


class AbspathInRoot(unittest.TestCase):
    def run_in_root(self, args):
        exe = os.path.relpath(os.path.realpath(sys.executable), "/")
        out = subprocess.run([exe] + args, cwd="/", capture_output=True, text=True)
        self.assertEqual(out.stderr, "")
        return out.stdout.strip()

    def test_executable_has_no_double_slash_from_root(self):
        exe = self.run_in_root(["-c", "import sys; print(sys.executable)"])
        self.assertEqual(exe, os.path.realpath(sys.executable))

    def test_script_file_has_no_double_slash_from_root(self):
        with tempfile.TemporaryDirectory() as d:
            d = os.path.realpath(d)
            script = os.path.join(d, "w35.py")
            with open(script, "w") as f:
                f.write("print(__file__)\n")
            self.assertEqual(self.run_in_root([os.path.relpath(script, "/")]), script)


if __name__ == "__main__":
    unittest.main()
