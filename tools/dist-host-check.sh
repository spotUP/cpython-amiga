#!/bin/sh
# The C3 layout and command, on this Mac: the host proof binary as
# Python3/bin/python3 next to the m68k build's python314.zip, run with an
# empty environment. Proves the zip, getpath's prefix search from the
# executable, and the sentinel script -- not the m68k code.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
D=$ROOT/build/host/dist/Python3
rm -rf "$ROOT/build/host/dist"
mkdir -p "$D/bin" "$D/lib/python3.14/lib-dynload"
cp "$ROOT/build/host/python.exe" "$D/bin/python3"
cp "$ROOT/build/m68k/python314.zip" "$D/lib/python314.zip"
cd "$ROOT/build/host/dist"
out=$(env -i "$D/bin/python3" -c "import os, re, json; print(json.dumps(os.listdir('.')))")
echo "C3 command: $out"
[ "$out" = '["Python3"]' ] || { echo "[FAIL] C3 command output"; exit 1; }
env -i "$D/bin/python3" -c "import json, sys; assert json.__file__.startswith('$D/lib/python314.zip/'), json.__file__; print('[OK] json from', json.__file__)"
# the sentinel script: on the host the platform line and the byte order
# differ by design; every other line must be OK
env -i "$D/bin/python3" "$ROOT/amiga/c3-sentinel.py" | tee "$ROOT/build/host/dist/sentinel.txt"
if grep '^FAIL' "$ROOT/build/host/dist/sentinel.txt" | grep -v 'platform is amigaos\|UTF-8 locale\|big-endian'; then
	echo "[FAIL] sentinel on the host"; exit 1
fi
echo "[OK] dist layout on the host"
