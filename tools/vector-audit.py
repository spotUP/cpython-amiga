#!/usr/bin/env python3
"""Every ixemul libc.a stub the m68k python links must call a vector that
ixemul-vtcon 48.2's library has, under the same name. The SDK's libc.a
(Aminet 48.x) is newer than the library UP-Term installs; a stub past
48.2's table would jump into nothing (libixcompat exists for exactly those).

Counts come from the structures: the link map's libc.a members, the jmp
offsets in those members' code (objdump), and ixemul-vtcon's
include/sys/syscall.def. Exit status 1 on any mismatch.
"""
import re, subprocess, sys, os, collections
AM = os.path.expanduser("~/opt/amiga/bin/")
LIBC = os.path.expanduser("~/opt/amiga/m68k-amigaos/ixemul/lib/libc.a")
DEF = os.path.expanduser("~/Code/ixemul-vtcon/include/sys/syscall.def")
MAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "build", "m68k", "python.map")
defs = {}
for m in re.finditer(r"SYSTEM_CALL\s*\((\w+)\s*,\s*(\d+)\)", open(DEF).read()):
    defs[m.group(1)] = int(m.group(2))
members = sorted(set(re.findall(r"ixemul/lib/libc\.a\(([^)]+)\)", open(MAP).read())))
dis = subprocess.run([AM + "m68k-amigaos-objdump", "-d", LIBC], capture_output=True, text=True).stdout
# per member: function label and jmp offset
cur = None; stubs = {}; member = None; nonstub = collections.defaultdict(list)
for line in dis.splitlines():
    m = re.match(r"^(\S+\.o):\s+file format", line)
    if m: member = m.group(1); continue
    m = re.match(r"^[0-9a-f]+ <(_\w+)>:", line)
    if m: cur = m.group(1)[1:]; continue
    m = re.search(r"jmp a0@\((-\d+)\)", line)
    if m and member in members and cur:
        stubs[cur] = int(m.group(1))
bad = []; ok = 0
for name, off in sorted(stubs.items()):
    vec = -off // 6 - 4   # LVOs start after Open/Close/Expunge/Reserved
    if name not in defs:
        bad.append((name, vec, "NOT IN 48.2 syscall.def"))
    elif defs[name] != vec:
        bad.append((name, vec, "48.2 has it at %d" % defs[name]))
    else:
        ok += 1
print("libc.a members linked:", len(members), " library stubs:", len(stubs), " matching 48.2:", ok)
for b in bad: print("MISMATCH", b)
sys.exit(1 if bad or not stubs else 0)
