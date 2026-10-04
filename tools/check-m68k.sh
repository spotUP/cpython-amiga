#!/bin/sh
# Static checks on the linked m68k binary (C1/C2), run on the host:
#   C2.1 PyObject/PyGC_Head 4-aligned under the 2-byte m68k ABI (compile-time)
#   C2.3 atomic builtins resolved by libamigacompat's Disable()/Enable() ones
#   C2.5 the $STACK: cookie is in the executable
#   C2.6 no emulated TLS: _Py_tss_tstate is a plain global
#   C2.2 the task-stack hook is linked
#   C1   only ixemul's libc (no member of the toolchain's newlib libc.a
#        except the vetted wide-string ones), and the sizes
# Prints one [OK]/[FAIL] line per check; exit status = number of failures.
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

[ -f "$EXE" ] && [ -f "$MAP" ] || { echo "[FAIL] build first: make m68k (needs $EXE and $MAP)"; exit 1; }

chk "C2.1 alignment asserts (tests/align_check.c)" \
  "$AMIGA/bin/m68k-amigaos-gcc -mcrt=ixemul -m68020-60 -std=c11 -fsyntax-only \
   -I$B/Include -I$B -I$ROOT/vendor/cpython/Include -I$ROOT/vendor/cpython/Include/internal \
   -I$ROOT/amiga/include -I$HOME/Code/neovim-amiga/amiga/compat/include $ROOT/tests/align_check.c"
chk "C2.3 __atomic_* come from libamigacompat.a(amiga-os.o)" \
  "grep -q 'libamigacompat.a(amiga-os.o)' '$MAP' && ! grep -q 'libatomic.a' '$MAP'"
chk "C2.5 \$STACK: cookie in the executable" "strings -a '$EXE' | grep -qx '\\\$STACK: 1048576'"
chk "C2.6 no emulated TLS (__emutls_*)" "! grep -q '__emutls' '$MAP'"
chk "C2.2 _PyAmiga_TaskStack linked" "grep -q '_PyAmiga_TaskStack' '$MAP'"
chk "C1 libc is ixemul's" "grep -q 'ixemul/lib/libc.a' '$MAP'"
chk "C1 newlib libc.a: wide-string members only" \
  "! grep -oE 'm68k-amigaos/lib/libc\\.a\\([^)]*\\)' '$MAP' | grep -v 'lib_a-w' | grep -q ."

set -- $("$AMIGA/bin/m68k-amigaos-size" "$EXE" | awk 'NR==2 {print $1, $2, $3}')
file=$(wc -c < "$EXE" | tr -d ' ')
cp "$EXE" "$B/python.stripped" && "$AMIGA/bin/m68k-amigaos-strip" "$B/python.stripped"
strip=$(wc -c < "$B/python.stripped" | tr -d ' ')
printf 'text %s data %s bss %s (loaded: %s bytes); file %s, stripped %s\n' \
  "$1" "$2" "$3" "$(( $1 + $2 + $3 ))" "$file" "$strip" | tee "$B/sizes.txt"
exit $fails
