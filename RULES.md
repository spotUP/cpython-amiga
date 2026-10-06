# cpython-amiga project rules

CPython 3.14 for AmigaOS 3.x / 68020-68060 / ixemul 48.2 (UP-Term plan PY1, Track C of
`~/Code/vtcon/thoughts/shared/research/2026-10-04_python-on-amigaos.md`). The global rules
(`~/.claude/CLAUDE.md`) apply; this file adds the project's. The ledger is
`thoughts/shared/plans/2026-10-04-py1-progress.md` (decisions, checklist, findings, owner steps).

1. **Upstream stays a tag plus a patch series.** `vendor/cpython` (gitignored) is a shallow
   clone of the tag; every change is a commit on its branch `amiga-3.14`, exported to
   `patches/*.patch` with `make patches` and committed here. Never edit `patches/` by hand.
2. **Guard AmigaOS code with `__amigaos__`**, never `AMIGA`/`amiga` (predefined as 1).
   Code that must be testable on the host gets its own switch (`--with-pthread-stubs`,
   `Py_SUBPROCESS_VFORK_ONLY`) and runs in the host proof build.
3. **What ixemul lacks** comes from, in this order: the SDK's libixcompat; neovim-amiga's
   `amiga/compat` (compiled here from its sources, never copied); the toolchain's newlib
   (`libm.a`, the self-contained wide-string members of `libc.a`); this repo's
   `amiga/compat` + `amiga/include`. Each addition is a request (X-items) in the ledger:
   it belongs in the ixemul-vtcon SDK.
4. **Nothing here starts an emulator or touches the rig.** Amiga runs are owner steps.
5. **One module set** (`amiga/Setup.local`) for the host proof and the Amiga.

## Commands

| Task | Command |
|------|---------|
| Recreate vendor/cpython (tag + patches) | `tools/fetch-cpython.sh [v3.14.N]` |
| Export the patch series after committing in vendor/cpython | `make patches` |
| Host proof build (macOS, the reduced configuration) | `make host` |
| Host tests: stack limits, wcstol, inet, then the stdlib set (resumable, `build/host/tests.tsv`) | `make host-test` |
| One stdlib test / this repo's tests / only failures | `tools/host-tests.sh test_re` / `tools/host-tests.sh tests/test_c0_config.py` / `tools/host-tests.sh --failed` |
| This port's cc1 (bebbo's gcc + `amiga/gcc/*.patch`, request G-1), used through `-B` | `make cc1` |
| The G-1 checks alone (driver runs that cc1, bit tests right) | `make test-gcc-btst` |
| Host test of the AmigaDOS path helpers | `make test-amiga-path` |
| Compat libraries for m68k | `make compat` |
| Configure for m68k (once; re-run after config.site changes) | `tools/configure-m68k.sh` |
| Build python for m68k (`build/m68k/python.exe`, map `python.map`) | `make m68k` |
| Static checks on the m68k binary + sizes (`build/m68k/sizes.txt`) | `make check-m68k` |
| Stdlib zip (host-compiled .pyc; `ZIPOPT=2` drops docstrings/asserts) | `make zip` |
| What goes onto the Amiga (`build/m68k/dist/Python3`) | `make dist` |
| The C3 layout and command on the host binary | `make dist-host-check` |
| On the Amiga (owner) | ledger, section "C3 owner steps" |
| Clean | `make clean` |

## Cross-repo changes

A change that crosses two or more UP-Term repos is one commit per repo, all with the
same subject line, plus one `repos.lock` update in the `upterm` meta-repo (re-pin with
`bin/upterm-bootstrap --update`) carrying that subject line too. Release step:
`upterm-bootstrap --update`, then `make dist` in vtcon; run `bin/upterm-doctor` first.
