# cpython-amiga

CPython port for AmigaOS 3.x with ixemul, for the UP-Term kit. Part of the upterm source tree.

## Build

Commands and what each proves: `RULES.md`, section `## Commands`. In order, to
get the kit's `build/m68k/dist/Python3` (what vtcon's `make dist` copies,
`PYTHON_DIST=`):

    tools/fetch-cpython.sh            # vendor/cpython: git clone of the v3.14.x tag (network) plus patches/
    make compat
    tools/configure-m68k.sh           # once
    make m68k zip dist

Needs bebbo's gcc 6.5 in `~/opt/amiga` and ixemul-vtcon's SDK headers and
`libixcompat.a` installed (see the `upterm` repo's README, "Set up the whole
thing"). `make host` and `make host-test` need no Amiga toolchain.
Order of the first lines not run end to end on a clean machine.

## Paths on the Amiga

`sys.executable` and `sys.prefix` can name the same drawer in two forms. With
`Python3:` assigned to `VTCX:Python3` (`VTC:` being an assign of the volume
`VTCX:`), `Python3:bin/python3` gives `sys.executable` = `/Python3/bin/python3`
(the path as typed) and `sys.prefix` = `/VTCX/Python3` (getpath works from the
real program directory, the assign resolved). This is intended: CPython on
Linux and macOS keeps a symlinked `sys.executable` as typed and finds the
prefix from the resolved path. Do not "fix" one to match the other.
