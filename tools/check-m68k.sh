#!/bin/sh
# Static checks on the linked m68k binary (C1/C2), run on the host:
#   C2.1 PyObject/PyGC_Head 4-aligned under the 2-byte m68k ABI (compile-time)
#   C2.3 atomic builtins resolved by libamigacompat's Disable()/Enable() ones
#   C2.5 the $STACK: cookie is in the executable
#   C2.6 no emulated TLS: _Py_tss_tstate is a plain global
#   C2.2 the task-stack hook is linked
#   C1   only ixemul's libc (no member of the toolchain's newlib libc.a
#        except the vetted wide-string ones), every stub on a 48.2
#        vector, and the sizes
#   G-1  the build's cc1 is the patched one and emits the right bit tests
#   G-2  no conditional branch on condition codes a callee left
# Prints one [OK]/[FAIL] line per check; exit status = number of failures.
#   tools/check-m68k.sh [--gcc-only]
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
AMIGA=${AMIGA:-$HOME/opt/amiga}
B=$ROOT/build/m68k
EXE=$B/python.exe
MAP=$B/python.map
NM=$AMIGA/bin/m68k-amigaos-nm
fails=0
ok()   { echo "[OK]   $1"; }
bad()  { echo "[FAIL] $1"; fails=$((fails+1)); }
chk()  { if eval "$2"; then ok "$1"; else bad "$1"; fi; }

# G-1: the build's cc1 (amiga/gcc/0001) tests the right byte. Before the fix
# `flags & 1` on an int argument was `btst #-24,(16,a5)` (bit 24), and
# PyFile_WriteObject ignored Py_PRINT_RAW: print() wrote repr()s.
CCB="$AMIGA/bin/m68k-amigaos-gcc -mcrt=ixemul -B$ROOT/build/gcc/bin/"
chk "G-1 the driver runs build/gcc/bin/cc1" \
  "[ \"\$($CCB -print-prog-name=cc1)\" = '$ROOT/build/gcc/bin/cc1' ]"
chk "G-1 tests/gcc_btst.c: flags & 1 tests the low byte (btst #0,(19,a5))" \
  "$CCB -m68020-60 -O1 -S -o - '$ROOT/tests/gcc_btst.c' | grep -q 'btst #0,(19,a5)' && \
   ! $CCB -m68020-60 -O1 -S -o - '$ROOT/tests/gcc_btst.c' | grep -q 'btst #-'"
# G-2: no branch on flags a callee left (amiga/gcc/0003, bbb opt_strcpy
# dropped a tst after `move x,aN`): sum(range(200000)) returned NULL
G2O=$ROOT/build/m68k/gcc_cc0_movea.o
mkdir -p "$ROOT/build/m68k"
chk "G-2 tests/gcc_cc0_movea.c: no branch on a callee's flags" \
  "$CCB -m68020-60 -O2 -c -o '$G2O' '$ROOT/tests/gcc_cc0_movea.c' && \
   $AMIGA/bin/m68k-amigaos-objdump -d '$G2O' | python3 '$ROOT/tools/cc-after-call.py'"
[ "${1:-}" = "--gcc-only" ] && exit $fails

[ -f "$EXE" ] && [ -f "$MAP" ] || { echo "[FAIL] build first: make m68k (needs $EXE and $MAP)"; exit 1; }
chk "G-2 no CPython object branches on a callee's flags (tools/cc-after-call.py)" \
  "( for o in \$(find '$B/Modules' '$B/Objects' '$B/Parser' '$B/Programs' '$B/Python' -name '*.o' ! -name frozen.o); do \
     $AMIGA/bin/m68k-amigaos-objdump -d \$o | python3 '$ROOT/tools/cc-after-call.py' >&2 || exit 1; done )"
chk "G-1 PyFile_WriteObject tests flags' low byte (Py_PRINT_RAW)" \
  "$AMIGA/bin/m68k-amigaos-objdump -d '$B/Objects/fileobject.o' | \
   awk '/<_PyFile_WriteObject>:/,/rts/' | grep -q 'btst #0,a5@(19)'"

chk "C2.1 alignment asserts (tests/align_check.c)" \
  "$CCB -m68020-60 -std=c11 -fsyntax-only \
   -I$B/Include -I$B -I$ROOT/vendor/cpython/Include -I$ROOT/vendor/cpython/Include/internal \
   -I$ROOT/amiga/include -I${NVCOMPAT:-${UPTERM_ROOT:-$(dirname "$ROOT")}/neovim-amiga/amiga/compat}/include $ROOT/tests/align_check.c"
chk "C2.3 __atomic_* come from libamigacompat.a(amiga-os.o)" \
  "grep -q 'libamigacompat.a(amiga-os.o)' '$MAP' && ! grep -q 'libatomic.a' '$MAP'"
chk "C2.5 \$STACK: cookie in the executable" "strings -a '$EXE' | grep -qx '\\\$STACK: 1048576'"
chk "C2.6 no emulated TLS (__emutls_*)" "! grep -q '__emutls' '$MAP'"
chk "C2.2 _PyAmiga_TaskStack linked" "grep -q '_PyAmiga_TaskStack' '$MAP'"
chk "C1 libc is ixemul's" "grep -q 'ixemul/lib/libc.a' '$MAP'"
chk "C1 every ixemul stub hits a 48.2 vector of the same name (tools/vector-audit.py)" \
  "python3 '$ROOT/tools/vector-audit.py' >&2"
chk "C1 newlib libc.a: wide-string members only" \
  "! grep -oE 'm68k-amigaos/lib/libc\\.a\\([^)]*\\)' '$MAP' | grep -v 'lib_a-w' | grep -q ."

set -- $("$AMIGA/bin/m68k-amigaos-size" "$EXE" | awk 'NR==2 {print $1, $2, $3}')
file=$(wc -c < "$EXE" | tr -d ' ')
cp "$EXE" "$B/python.stripped" && "$AMIGA/bin/m68k-amigaos-strip" "$B/python.stripped"
strip=$(wc -c < "$B/python.stripped" | tr -d ' ')
printf 'text %s data %s bss %s (loaded: %s bytes); file %s, stripped %s\n' \
  "$1" "$2" "$3" "$(( $1 + $2 + $3 ))" "$file" "$strip" | tee "$B/sizes.txt"
exit $fails
