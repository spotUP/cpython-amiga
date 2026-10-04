# C3 step 2 (after the one-liner): what this port changed, seen running on
# the Amiga. Each line prints OK or FAIL; send the whole output back.
#   Python3:bin/python3 Python3:c3-sentinel.py
import sys, os, time
t0 = time.monotonic()

def check(name, cond, detail=""):
    print(("OK   " if cond else "FAIL ") + name + (": " + str(detail) if detail else ""))

check("platform is amigaos", sys.platform == "amigaos", sys.platform)
check("UTF-8 locale and file system encoding",
      sys.getfilesystemencoding() == "utf-8" and sys.flags.utf8_mode == 1,
      (sys.getfilesystemencoding(), sys.flags.utf8_mode))
check("threads are the stubs", sys.thread_info.name == "pthread-stubs", sys.thread_info)
import threading
try:
    threading.Thread(target=lambda: None).start()
    check("Thread.start raises", False, "a thread started")
except RuntimeError as e:
    check("Thread.start raises", True, e)

# C stack limits from tc_SPLower/tc_SPUpper: deep C recursion must raise
# RecursionError, not crash the machine
sys.setrecursionlimit(100000)
x = []
for _ in range(100000):
    x = [x]
try:
    repr(x)
    check("deep C recursion raises RecursionError", False, "no error")
except RecursionError:
    check("deep C recursion raises RecursionError", True)
del x

import json, re, math, struct
check("json round trip", json.loads(json.dumps({"a": [1, 2.5, "x"]})) == {"a": [1, 2.5, "x"]})
check("re", re.sub(r"(\w+)@(\w+)", r"\2 at \1", "spot@amiga") == "amiga at spot")
check("floats (soft-float build)", repr(0.1 + 0.2) == "0.30000000000000004" and math.isclose(math.sqrt(2) ** 2, 2.0),
      repr(0.1 + 0.2))
check("C99 libm (newlib): acosh, log2, expm1",
      math.isclose(math.acosh(2), 1.3169578969248166) and math.log2(1024) == 10.0
      and math.isclose(math.expm1(1e-10), 1e-10), (math.acosh(2), math.log2(1024)))
try:
    math.acosh(0)
    check("math domain error", False, "no error")
except ValueError:
    check("math domain error", True)
check("struct big-endian native", struct.pack("=I", 1) == b"\0\0\0\1")
check("listdir/stat", isinstance(os.listdir("."), list) and os.stat(".").st_mode != 0)
check("case-exact import (json, not JSON)", "JSON" not in sys.modules)
try:
    __import__("JSON")
    check("import JSON fails", False, "imported")
except ImportError:
    check("import JSON fails", True)
import subprocess
try:
    r = subprocess.run(["echo", "vfork ok"], capture_output=True, text=True, timeout=60)
    check("subprocess over vfork (C4.1)", r.stdout.strip() == "vfork ok", (r.returncode, r.stdout, r.stderr))
except Exception as e:
    check("subprocess over vfork (C4.1)", False, repr(e))
print("sys.path:", sys.path)
print("prefix:", sys.prefix, "executable:", sys.executable)
print("sentinel took %.1f s" % (time.monotonic() - t0))
