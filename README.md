# cpython-amiga

CPython port for AmigaOS 3.x with ixemul, for the UP-Term kit. Part of the upterm source tree.

## Build

Commands and what each proves: `RULES.md`, section `## Commands`. In order, to
get the kit's `build/m68k/dist/Python3` (what vtcon's `make dist` copies,
`PYTHON_DIST=`):

    tools/fetch-cpython.sh            # vendor/cpython: git clone of the v3.14.x tag (network) plus patches/
    make cc1                          # this port's patched gcc cc1 (clones bebbo's gcc, branch amiga6, into build/gcc; network, long)
    make compat
    tools/configure-m68k.sh           # once
    make m68k zip dist

Needs bebbo's gcc 6.5 in `~/opt/amiga` and ixemul-vtcon's SDK headers and
`libixcompat.a` installed (see the `upterm` repo's README, "Set up the whole
thing"). `make host` and `make host-test` need no Amiga toolchain.
Order of the first lines not run end to end on a clean machine.
