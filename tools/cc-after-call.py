#!/usr/bin/env python3
"""G-2 check: no conditional branch may test condition codes left by a
called function. bebbo's gcc 6.5 bbb pass (opt_strcpy) merged
`move.l x,d0; move.l d0,aN; tst.l d0` into `move.l x,aN` -- movea sets no
flags, so the branch after it read whatever the callee left in the CCR
(sum(range(200000)) returned NULL: `result = temp; if (!result) break;`
after a Py_DECREF that called _Py_Dealloc).

Reads `objdump -d` output on stdin; prints each hit as function+offset and
exits 1 if there is any. A hit: jsr/bsr, then optionally the argument pop
(addq/adda/lea to sp), then movea (which sets no flags), then beq/bne --
the shape the bbb merge leaves. Tighter than "any non-flag-setting
instruction" on purpose: amigaos puts read-only data in the code hunk, and
objdump decodes strings as instructions.
"""
import re
import sys

POP = re.compile(r"^(addql #\d+,sp|addaw #\d+,sp|lea sp@\(\d+\),sp)$")
MOVEA = re.compile(r"^movea[lw] \S+,a[0-6]$")
BCC = re.compile(r"^b(ne|eq)[sw]? ")
func, after_call, state, hits = "?", None, 0, []
for line in sys.stdin:
    m = re.match(r"^([0-9a-f]+) <(.*)>:", line)
    if m:
        func, after_call = m.group(2), None
        continue
    parts = line.rstrip("\n").split("\t")
    if len(parts) < 3:
        continue
    addr, insn = parts[0].strip().rstrip(":"), parts[2].strip()
    op = insn.split(None, 1)[0] if insn else ""
    if op == "jsr":  # gcc calls with jsr; bsr here is string data decoded
        after_call, state = addr, 0
    elif after_call and state == 0 and POP.match(insn):
        state = 1
    elif after_call and state < 2 and MOVEA.match(insn):
        state = 2
    elif after_call and state == 2 and BCC.match(insn + " "):
        hits.append("%s: %s (call at %s)" % (func, insn, after_call))
        after_call = None
    else:
        after_call = None
for h in hits:
    print(h)
sys.exit(1 if hits else 0)
