"""C0 host proof: the reduced AmigaOS configuration, checked on the host
build (build/host/python.exe) -- and, where it says so, on the m68k binary.

Run: build/host/python.exe -m unittest -v tests/test_c0_config.py
"""
import os
import pathlib
import subprocess
import sys
import sysconfig
import threading
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SETUP_LOCAL = ROOT / "amiga" / "Setup.local"


def disabled_modules():
    names, on = [], False
    for line in SETUP_LOCAL.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line == "*disabled*":
            on = True
        elif line.startswith("*"):
            on = False
        elif line and on:
            names.append(line.split()[0])
    return names


class ThreadStubs(unittest.TestCase):
    def test_config_has_stubs(self):
        self.assertEqual(sysconfig.get_config_var("HAVE_PTHREAD_STUBS"), 1)
        self.assertEqual(sys.thread_info.name, "pthread-stubs")

    def test_thread_start_raises(self):
        t = threading.Thread(target=lambda: None)
        with self.assertRaises(RuntimeError):
            t.start()

    def test_locks_still_work_in_one_thread(self):
        lock = threading.Lock()
        with lock:
            self.assertTrue(lock.locked())
        self.assertFalse(lock.locked())
        rlock = threading.RLock()
        with rlock, rlock:
            pass

    def test_thread_local_is_plain_global(self):
        # _Py_thread_local is empty under HAVE_PTHREAD_STUBS: the thread
        # state pointer must be an ordinary data symbol, not a TLS one.
        exe = sys.executable
        if sys.platform != "darwin":
            self.skipTest("Mach-O section check")
        out = subprocess.run(["nm", "-m", exe], capture_output=True,
                             text=True, check=True).stdout
        line = [l for l in out.splitlines() if l.endswith(" __Py_tss_tstate")]
        self.assertEqual(len(line), 1, line)
        self.assertNotIn("thread_", line[0])   # not __thread_vars/_bss/_data


class StaticModules(unittest.TestCase):
    def test_no_mimalloc(self):
        self.assertEqual(sysconfig.get_config_var("WITH_MIMALLOC"), 0)

    def test_no_shared_extension_modules(self):
        built = list(pathlib.Path(sys.executable).parent.glob("build/lib.*/*.so"))
        self.assertEqual(built, [])

    def test_wanted_modules_are_builtin(self):
        for name in ("posix", "_io", "_sre", "_json", "_struct", "math",
                     "time", "select", "_socket", "binascii", "_random",
                     "_posixsubprocess", "termios", "fcntl", "array",
                     "_datetime", "_pickle", "unicodedata", "_sha2"):
            self.assertIn(name, sys.builtin_module_names, name)

    def test_disabled_modules_absent(self):
        for name in disabled_modules():
            self.assertNotIn(name, sys.builtin_module_names, name)
            with self.assertRaises(ImportError, msg=name):
                __import__(name)


class StackLimit(unittest.TestCase):
    def test_deep_c_recursion_raises_not_crashes(self):
        # 3.14 measures the C stack (hardware_stack_limits); with the stubs
        # on macOS that is the generic estimate, on AmigaOS tc_SPLower/Upper.
        code = ("import sys; sys.setrecursionlimit(10**6)\n"
                "x = []\n"
                "for _ in range(10**6): x = [x]\n"
                "try:\n    repr(x)\nexcept RecursionError:\n    print('RecursionError')\n")
        r = subprocess.run([sys.executable, "-c", code], capture_output=True,
                           text=True)
        self.assertEqual(r.returncode, 0, r.stderr[-500:])
        self.assertEqual(r.stdout.strip(), "RecursionError")


if __name__ == "__main__":
    unittest.main()
