#!/bin/sh
# Recreate vendor/cpython: a shallow clone of the upstream tag, branch
# amiga-3.14 with patches/*.patch applied as commits (git am).
#   tools/fetch-cpython.sh [TAG]      default v3.14.7
# Rebasing to a later 3.14.x: tools/fetch-cpython.sh v3.14.N, fix what
# does not apply, `make patches` (BASE= the new tag's commit), commit.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
TAG=${1:-v3.14.7}
DIR=${CPYTHON_DIR:-$ROOT/vendor/cpython}
if [ -e "$DIR" ]; then
	echo "$DIR exists; move it away first (it may hold unexported commits)" >&2
	exit 1
fi
git clone -q --depth 1 --branch "$TAG" https://github.com/python/cpython.git "$DIR"
git -C "$DIR" checkout -q -b amiga-3.14
git -C "$DIR" am -q "$ROOT"/patches/*.patch
git -C "$DIR" log --oneline "$TAG"..HEAD 2>/dev/null || git -C "$DIR" log --oneline -12
