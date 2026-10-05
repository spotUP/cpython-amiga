# C3 step 2 (after the one-liner): what this port changed, seen running on
# the Amiga. Each line prints OK or FAIL; send the whole output back.
#   Python3:bin/python3 Python3:c3-sentinel.py
import sys, os, time
t0 = time.monotonic()

def check(name, cond, detail=""):
    print(("OK   " if cond else "FAIL ") + name + (": " + str(detail) if detail else ""))

check("platform is amigaos", sys.platform == "amigaos", sys.platform)
# W35: print() wrote repr()s ('x''\n') -- gcc's btst miscompile of
# `flags & Py_PRINT_RAW` (amiga/gcc/0001). Checked from inside as well.
import io
buf = io.StringIO()
print("x", 1, file=buf)
check("print writes str, not repr (gcc btst fix)", buf.getvalue() == "x 1\n", repr(buf.getvalue()))
# W35: sys.executable was '/Ram Disk//Python3:bin/python3', and
# `python3 Python3:c3-sentinel.py` could not open the script
check("sys.executable in Unix form, exists",
      sys.executable.startswith("/") and ":" not in sys.executable
      and "//" not in sys.executable and os.path.isfile(sys.executable), sys.executable)
check("script path in Unix form (Vol:path argv)",
      __file__.startswith("/") and ":" not in __file__ and os.path.isfile(__file__), __file__)
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

# G-2: int sums leaving the C fast path (sum() returned NULL: the bbb
# flags-after-call miscompile, amiga/gcc/0003), and other big-int paths
import functools
check("sum(range(200000)) == 19999900000 (gcc bbb fix)", sum(range(200000)) == 19999900000)
t = 0
for i in range(70000):
    t = t + i
check("int add past 2**31 in a loop", t == 2449965000, t)
check("int mul/add overflow into PyLong",
      65536 * 65536 == 4294967296 and (2**31 - 1) + 1 == 2147483648 and 2**64 == 18446744073709551616)
import math
check("math.factorial(25), math.prod(range(1, 26))",
      math.factorial(25) == 15511210043330985984000000 == math.prod(range(1, 26)))
check("int.bit_length", (2**64).bit_length() == 65 and (-2**31).bit_length() == 32)
check("functools.partial repr", repr(functools.partial(int, 1)).startswith("functools.partial("))
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
# a bare AmigaDOS command (C:Which; Echo is a shell built-in, no file) found
# through ixemul's execve(): resident list, then the shell's command path.
# (PATH only for the host run, `env -i`: there `which` searches it.)
try:
    r = subprocess.run(["which", "which"], capture_output=True, text=True, timeout=60,
                       env={**os.environ, "PATH": os.environ.get("PATH") or os.defpath})
    check("subprocess over vfork (C4.1), bare name on the command path",
          r.returncode == 0 and r.stdout.strip().lower().endswith("which"),
          (r.returncode, r.stdout, r.stderr))
except Exception as e:
    check("subprocess over vfork (C4.1), bare name on the command path", False,
          (repr(e), "PATH=%r" % os.environ.get("PATH"), os.get_exec_path()))
# C4.2/C4.3: select over a pipe (ixemul select), sockets need a TCP/IP
# stack (Roadshow/AmiTCP) running: without one they print INFO, not FAIL
import select, socket
r, w = os.pipe()
os.write(w, b"p")
check("select on a pipe", select.select([r], [], [], 5)[0] == [r] and os.read(r, 1) == b"p")
os.close(r); os.close(w)
try:
    info = socket.getaddrinfo("127.0.0.1", 80, socket.AF_INET, socket.SOCK_STREAM)
    check("getaddrinfo, numeric (neovim-amiga compat netdb)", info[0][4] == ("127.0.0.1", 80), info[0])
except OSError as e:
    print("INFO getaddrinfo:", e)
try:
    a, b = socket.socketpair()
    a.send(b"s")
    check("socketpair + select", select.select([b], [], [], 5)[0] == [b] and b.recv(1) == b"s")
    a.close(); b.close()
except OSError as e:
    print("INFO socketpair:", e)
print("sys.path:", sys.path)
print("prefix:", sys.prefix, "executable:", sys.executable)
print("sentinel took %.1f s" % (time.monotonic() - t0))
