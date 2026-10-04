#!/usr/bin/env python3
"""Build python314.zip for the Amiga: the pure-Python stdlib as .pyc only,
compiled by the host CPython (same version, so the same bytecode magic;
marshal data is byte-order independent). Stored, not deflated: zipimport
needs zlib for deflated members and this build has no zlib.

  tools/mkzip.py SRC_LIB SYSCONFIGDATA OUT.zip [--optimize N] [--list]

Code objects carry the path they will have on the Amiga
(/Python3/lib/python314.zip/<name>.py) so tracebacks name it.
"""
import argparse
import importlib.util
import io
import os
import sys
import zipfile

# Left out: tests, GUI, things whose C module this build does not have
# (amiga/Setup.local, configure n/a list), and packaging helpers.
# The set is an owner decision (ledger, "Module set").
EXCLUDE_DIRS = {
    "test", "idlelib", "tkinter", "turtledemo", "ensurepip", "__phello__",
    "sqlite3", "curses", "ctypes", "multiprocessing", "pydoc_data",
    "lib2to3", "site-packages",
}
EXCLUDE_FILES = {
    "turtle.py", "_android_support.py", "_apple_support.py", "_ios_support.py",
    "_aix_support.py", "_osx_support.py",
}
ZIP_PREFIX = "/Python3/lib/python314.zip"


def wanted(rel):
    parts = rel.split("/")
    if any(p in EXCLUDE_DIRS or p == "__pycache__" for p in parts[:-1]):
        return False
    if "/".join(parts[:2]) in EXCLUDE_DIRS:
        return False
    return parts[-1] not in EXCLUDE_FILES and parts[-1].endswith(".py")


def pyc(source, display_name, optimize):
    code = compile(source, display_name, "exec", dont_inherit=True,
                   optimize=optimize)
    # unchecked hash-based pyc: nothing to compare against (no .py shipped)
    return importlib._bootstrap_external._code_to_hash_pyc(
        code, importlib.util.source_hash(source), checked=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lib")
    ap.add_argument("sysconfigdata")
    ap.add_argument("out")
    ap.add_argument("--optimize", type=int, default=0)
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if sys.version_info[:2] != (3, 14):
        sys.exit("needs the host CPython 3.14 (bytecode magic)")
    files = []
    for root, dirs, names in os.walk(a.lib):
        dirs.sort()
        for n in sorted(names):
            p = os.path.join(root, n)
            rel = os.path.relpath(p, a.lib).replace(os.sep, "/")
            if wanted(rel):
                files.append((rel, p))
    files.append((os.path.basename(a.sysconfigdata), a.sysconfigdata))
    total = 0
    with zipfile.ZipFile(a.out, "w", zipfile.ZIP_STORED) as z:
        for rel, p in files:
            with open(p, "rb") as f:
                src = f.read()
            data = pyc(src, f"{ZIP_PREFIX}/{rel}", a.optimize)
            info = zipfile.ZipInfo(rel[:-3] + ".pyc", (2026, 1, 1, 0, 0, 0))
            z.writestr(info, data)
            total += len(data)
            if a.list:
                print(rel)
    print(f"{a.out}: {len(files)} modules, {total} bytes of .pyc, "
          f"{os.path.getsize(a.out)} bytes zip")


if __name__ == "__main__":
    main()
