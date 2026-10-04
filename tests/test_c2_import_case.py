"""C2.4: imports on AmigaOS (case-insensitive, case-preserving file system)
match module names case-exactly, and PYTHONCASEOK relaxes that, as on
macOS. Runs on the host proof build (macOS's default file system is
case-insensitive too, so the directory-cache check is exercised for real).

Run: build/host/python.exe -m unittest -v tests/test_c2_import_case.py
"""
import importlib
import os
import sys
import tempfile
import unittest
from importlib import _bootstrap_external as be


class AmigaCaseInsensitive(unittest.TestCase):
    def test_amigaos_is_listed(self):
        self.assertIn("amigaos", be._CASE_INSENSITIVE_PLATFORMS)
        self.assertIn("amigaos", be._CASE_INSENSITIVE_PLATFORMS_BYTES_KEY)

    def relax_case_for(self, platform, environ):
        saved_platform, saved_env = sys.platform, be._os.environ
        try:
            sys.platform = platform
            be._os.environ = environ
            return be._make_relax_case()()
        finally:
            sys.platform, be._os.environ = saved_platform, saved_env

    def test_pythoncaseok_relaxes_on_amigaos(self):
        self.assertTrue(self.relax_case_for("amigaos", {b"PYTHONCASEOK": b"1"}))
        self.assertFalse(self.relax_case_for("amigaos", {}))

    def test_pythoncaseok_ignored_where_case_sensitive(self):
        self.assertFalse(self.relax_case_for("linux", {b"PYTHONCASEOK": b"1"}))

    def test_wrong_case_import_fails_on_case_insensitive_fs(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "CaseMod.py"), "w") as f:
                f.write("x = 1\n")
            if not os.path.exists(os.path.join(d, "casemod.py")):
                self.skipTest("file system is case-sensitive")
            sys.path.insert(0, d)
            importlib.invalidate_caches()
            try:
                self.assertEqual(importlib.import_module("CaseMod").x, 1)
                with self.assertRaises(ImportError):
                    importlib.import_module("casemod")
            finally:
                sys.path.remove(d)
                sys.modules.pop("CaseMod", None)


if __name__ == "__main__":
    unittest.main()
