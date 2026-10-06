#!/bin/sh
# Configure CPython for m68k-amigaos (ixemul) in build/m68k.
# Needs: the host python3.14 (same version as the tree) as the build Python,
# build/m68k/libamigacompat.a (make compat), the ixemul SDK's libixcompat.a,
# build/gcc/bin/cc1 (make cc1: the installed cc1 miscompiles bit tests,
# amiga/gcc/0001), which the driver finds first through -B.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
AMIGA=${AMIGA:-$HOME/opt/amiga}
UPTERM_ROOT=${UPTERM_ROOT:-$(dirname "$ROOT")}
NVCOMPAT=${NVCOMPAT:-$UPTERM_ROOT/neovim-amiga/amiga/compat}
HOSTPY=${HOSTPY:-/opt/homebrew/bin/python3.14}
ACPU=${ACPU:--m68020-60}
B=$ROOT/build/m68k
[ -x "$ROOT/build/gcc/bin/cc1" ] || { echo "build/gcc/bin/cc1 missing: make cc1" >&2; exit 1; }
mkdir -p "$B"
cd "$B"
CONFIG_SITE=$ROOT/amiga/config.site \
CC="$AMIGA/bin/m68k-amigaos-gcc -mcrt=ixemul -B$ROOT/build/gcc/bin/" \
AR=$AMIGA/bin/m68k-amigaos-ar \
RANLIB=$AMIGA/bin/m68k-amigaos-ranlib \
READELF=: \
CFLAGS="$ACPU" \
OPT="-DNDEBUG -O2" \
CPPFLAGS="-I$ROOT/amiga/include -I$NVCOMPAT/include" \
LDFLAGS="-L$B -Wl,-Map,$B/python.map" \
LIBS="-lcpyamiga -lamigacompat -lixcompat -lnewlibwcs" \
"$ROOT/vendor/cpython/configure" \
	--build="$("$ROOT/vendor/cpython/config.guess")" \
	--host=m68k-amigaos \
	--with-build-python="$HOSTPY" \
	--prefix=/Python3 \
	--with-pthread-stubs \
	--without-mimalloc \
	--without-doc-strings \
	--disable-test-modules \
	--disable-ipv6 \
	--without-ensurepip \
	--with-pkg-config=no \
	--with-libm="-lc -lm -lcpyamiga" \
	> configure.log 2>&1 || { tail -30 configure.log; exit 1; }
tail -3 configure.log
