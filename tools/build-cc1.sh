#!/bin/sh
# Build this port's cc1: bebbo's gcc 6.5 (amiga6, the commit the installed
# toolchain was built from) plus amiga/gcc/*.patch, into build/gcc/bin/cc1.
# The m68k build finds it with -B (tools/configure-m68k.sh, Makefile ACFLAGS);
# the installed toolchain in $AMIGA stays untouched.
#   tools/build-cc1.sh            clone (if missing), patch, configure, build
# Why: amiga/gcc/0001 -- the installed cc1 miscompiles `x & 1` on an int in
# memory (btst #-24 on the first byte = bit 24). Request G-1 in the ledger:
# the patch belongs in bebbo's gcc and then in the installed toolchain.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
AMIGA=${AMIGA:-$HOME/opt/amiga}
GCC_URL=${GCC_URL:-https://franke.ms/git/bebbo/gcc}
# = `m68k-amigaos-gcc --version`: 6.5.0b 20260819091705 ("bump version")
GCC_COMMIT=${GCC_COMMIT:-8c1fd39db}
G=$ROOT/build/gcc
SRC=$G/src
OBJ=$G/obj
J=${J:--j4}

if [ ! -d "$SRC/.git" ]; then
	mkdir -p "$G"
	git clone -q --no-checkout --depth 40 -b amiga6 "$GCC_URL" "$SRC"
	# C only: leave out the test suites and the other languages' runtimes
	git -C "$SRC" sparse-checkout init --no-cone
	printf '%s\n' '/*' '!/gcc/testsuite/' '!/gcc/ada/' '!/gcc/go/' '!/gcc/fortran/' \
		'!/gcc/java/' '!/libjava/' '!/libgo/' '!/libstdc++-v3/' '!/libgfortran/' \
		'!/libsanitizer/' '!/gnattools/' '!/libada/' '!/boehm-gc/' '!/libffi/' \
		'!/zlib/' '!/libobjc/' '!/libgomp/' '!/libcilkrts/' '!/libvtv/' \
		'!/liboffloadmic/' '!/libmpx/' '!/libquadmath/' '!/libitm/' '!/libatomic/' \
		> "$SRC/.git/info/sparse-checkout"
	git -C "$SRC" checkout -q -b amiga-cpython "$GCC_COMMIT"
	git -C "$SRC" -c user.name=cpython-amiga -c user.email=noreply@anthropic.com \
		am -q "$ROOT"/amiga/gcc/*.patch
fi
git -C "$SRC" log --oneline -"$(( $(ls "$ROOT"/amiga/gcc/*.patch | wc -l) + 1 ))"

# configured and compiled as the installed one ($AMIGA/bin/m68k-amigaos-gcc -v;
# amiga-gcc's build log: CFLAGS only -I<brew>/include), C only; the target
# binutils on PATH so gcc/configure probes the same assembler
if [ ! -f "$OBJ/Makefile" ]; then
	mkdir -p "$OBJ"
	BREW=$(brew --prefix)
	(cd "$OBJ" && PATH="$AMIGA/bin:$PATH" CFLAGS="-I$BREW/include" CXXFLAGS="-I$BREW/include" \
		"$SRC/configure" --prefix="$AMIGA" --target=m68k-amigaos \
		--enable-languages=c --enable-version-specific-runtime-libs \
		--disable-libssp --disable-nls --disable-shared --enable-threads=no \
		--with-gmp="$BREW" --with-mpfr="$BREW" --with-mpc="$BREW" \
		--with-system-zlib > configure.log 2>&1) || { tail -30 "$OBJ/configure.log"; exit 1; }
fi
PATH="$AMIGA/bin:$PATH" make -C "$OBJ" $J all-gcc > "$OBJ/make.log" 2>&1 || { tail -30 "$OBJ/make.log"; exit 1; }
mkdir -p "$G/bin"
cp "$OBJ/gcc/cc1" "$G/bin/cc1"
echo "[OK] $G/bin/cc1"
