---
date: 2026-10-04
topic: PY1 -- CPython 3.14 on AmigaOS 3.x / 68020-68060 / ixemul (Track C)
tags: [cpython, python, amigaos, ixemul, m68k, port, ledger]
status: draft
---

# PY1 progress ledger

Source: `~/Code/vtcon/thoughts/shared/research/2026-10-04_python-on-amigaos.md` (Track C).
Upstream: CPython **v3.14.7** (823f032), shallow clone in `vendor/cpython` (gitignored);
our changes are commits on branch `amiga-3.14` there, exported to `patches/*.patch`
(the tracked copy). Rebase to a later 3.14.x: `tools/fetch-cpython.sh <tag>` (git am).
Commands: `RULES.md`.

Finish line for this session: C0 green and recorded; C1 linked m68k binary with measured
sizes; C2 patches in with their tests; C3 written as owner steps. C4/C5 only after that.

**Status: 19 of 24 done, 5 open** -- C3.2 (owner run), C4.1-C4.3 (code in and host-proven,
the Amiga run is the sentinel's job), C5.1 (Amiga regression subset, not started).

## Decisions (do not re-litigate)

- **D-1** CPython 3.14.7 = the host's Homebrew python3.14 (3.14.7), the `--with-build-python`.
- **D-2** Patches are commits on `amiga-3.14` over the tag, exported with `make patches`.
  `tools/fetch-cpython.sh` re-applies them to a fresh clone (verified: identical tree).
- **D-3** Compat sources, in order: SDK libixcompat; neovim-amiga's `amiga/compat` compiled
  here from its sources (no copy); the toolchain's newlib `libm.a` and the self-contained
  wide-string members of its `libc.a`; this repo's `amiga/compat` + `amiga/include`.
- **D-4** Threads: `--with-pthread-stubs` (WASI's model, now a configure option usable on any
  host). `threading` imports, `Thread.start()` raises RuntimeError, locks work in one thread.
  `_Py_thread_local` is a plain global under HAVE_PTHREAD_STUBS (no emutls).
- **D-5** Modules: all static (`MODULE_BUILDTYPE=static`); `amiga/Setup.local` lists what is
  left out and is the same file for the host proof and the Amiga.
- **D-6 Soft-float build (`-m68020-60`, no `-m68881`).** Measured: gcc 6.5 with `-m68881`
  returns doubles in `fp0`, while ixemul.library (also its FPU builds: `general/arith.c`
  ldexp moves fp0 to d0/d1) and libixcompat return them in `d0/d1`. An FPU build would read
  garbage from every double-returning library call (strtod, frexp, fmod, round...) unless
  a return-ABI shim wraps each one, and neovim-amiga's compat `<math.h>` does not compile
  with `-m68881` (its `atan2` declaration conflicts with ixemul's `math-68881.h` inline).
  The soft-float build has one ABI everywhere, runs on any 68020+ (FPU or not), and float
  arithmetic goes through ixemul.library's `__adddf3`/`__muldf3`, which use the FPU when
  the FPU variant of the library is installed. Python-level cost is small next to the
  interpreter's per-bytecode overhead (est., unmeasured). FPU build = owner decision O-1.
- **D-7 C99 math from the toolchain's newlib `libm.a`** (fdlibm): `--with-libm="-lc -lm
  -lcpyamiga"` -- ixemul's libc first, so newlib supplies only what ixemul lacks (acosh,
  asinh, atanh, erf, erfc, expm1, log1p, log2, cbrt, exp2, nextafter, fma, hypot...). Its
  errno reports go through `_impure_ptr->_errno` (offset 0): `amiga/compat/newlib-errno.c`
  points `_impure_ptr` at ixemul's `errno` (crt0 data); EDOM/ERANGE are 33/34 in both.
- **D-8 UTF-8 everywhere** (`_Py_FORCE_UTF8_LOCALE` on `__amigaos__`): ixemul has only the C
  locale, UP-Term speaks UTF-8. Latin-1 file names decode with surrogateescape (round-trip
  safe, not pretty).
- **D-9 Layout `/Python3`** (`--prefix=/Python3`): `Python3:bin/python3`,
  `Python3:lib/python314.zip`, empty `Python3:lib/python3.14/lib-dynload/` (getpath's
  exec_prefix landmark, else a warning). getpath finds the prefix by searching up from the
  executable's directory, or falls back to the compiled-in `/Python3` (ixemul's view of the
  assign `Python3:` -- unverified, C3 shows it).
- **D-10 subprocess = vfork only** (`VFORK_ONLY` in `_posixsubprocess`): no fork() fallback;
  preexec_fn / user / group / extra_groups fail with ENOSYS. The host proof compiles the
  same code (`-DPy_SUBPROCESS_VFORK_ONLY` in `amiga/Setup.local`).
- **D-11 stdlib zip**: `.pyc` only, unchecked-hash pycs compiled by the host 3.14.7, stored
  (no zlib on m68k). Code objects name `/Python3/lib/python314.zip/<file>.py`.

## Checklist (24 items; 19 done, 5 open)

Commits: outer repo (this one) and `vendor/cpython` branch `amiga-3.14` (= `patches/000N`).

### C0 Host proof (Mac, reduced config) -- 6 of 6
- [x] C0.1 repo, shallow clone v3.14.7, ledger -- 71284b3
- [x] C0.2 configure.ac: m68k-amigaos host case, `--with-pthread-stubs`, AmigaOS n/a list,
      static modules -- patch 0001 (db85d79)
- [x] C0.3 pthread_stubs.h names prefixed `_Py_stub_` outside WASI (no clash with macOS
      `<sys/types.h>` or neovim compat's `pthread_self`); no native thread id with stubs;
      `test.support.threading_helper.can_start_thread` false for a stubs build -- patch 0002
- [x] C0.4 `_Py_thread_local` plain global under stubs -- patch 0002; test
      `tests/test_c0_config.py` (`__Py_tss_tstate` in `__DATA,__common`, stock 3.14 has it in
      `__thread_vars`)
- [x] C0.5 host build (`make host`): stubs, 66 static built-ins, no mimalloc, no doc
      strings, no test modules, `Thread.start` raises -- 762a2c6
- [x] C0.6 tests recorded resumably in `build/host/tests.tsv` (`tools/host-tests.sh`):
      **12 of 12 pass** (json 225, re 165, posixpath 94, genericpath 25, struct 44, math 89,
      select 6 pass; io 667, time 64, subprocess 353 pass* = every failure listed in
      `tests/c0-expected.tsv`: tests that start threads without `@requires_working_threading`,
      CJK codecs left out, `platform.mac_ver` needs pyexpat, preexec_fn/user/group under
      vfork-only; plus `tests/test_c0_config.py` 9, `tests/test_c2_import_case.py` 4) -- 762a2c6

### C1 Cross configure / link -- 6 of 6
- [x] C1.1 C1a: geekychris/python-amigaos4 (3.12.7, OS4/newlib) read -- notes below
- [x] C1.2 `amiga/config.site` (cross answers, each with its reason) -- cd9d9f9
- [x] C1.3 compat libraries: `libamigacompat.a` from neovim-amiga's sources, `libcpyamiga.a`
      (newlib errno hook, wcstol, inet_ntop/pton, getentropy), `libnewlibwcs.a` (23 newlib
      members, `nm -u` clean) -- cd9d9f9, 28b0992
- [x] C1.4 m68k configure passes (`tools/configure-m68k.sh`) -- cd9d9f9
- [x] C1.5 **python links**: `build/m68k/python.exe`; `make check-m68k` all OK, including
      `tools/vector-audit.py`: all 258 ixemul library calls hit a 48.2 vector of the same
      name (counted from the link map, objdump of the stubs and ixemul-vtcon's
      `include/sys/syscall.def`) -- cd9d9f9, 9964f06
- [x] C1.6 `python314.zip` built (`make zip`) -- cd9d9f9

### C2 Patches -- 6 of 6
- [x] C2.1 gh-127545 alignment backport (python/cpython#135209, applied unchanged) -- patch
      0004 (df13a54); test `tests/align_check.c` (m68k compile-time asserts; fails against
      the pre-backport headers: verified)
- [x] C2.2 stack bounds from `FindTask(NULL)->tc_SPLower/tc_SPUpper` (`Python/amigaos.c`,
      NDK headers only) with a pure limit chooser (`pycore_amigaos.h`) -- patch 0003; test
      `make test-stack` (host C test), `tests/test_c0_config.py` deep-recursion
      RecursionError (host), sentinel line on the Amiga
- [x] C2.3 atomics: the `__atomic_*` libcalls resolve to neovim-amiga compat's
      Disable()/Enable() versions (link map: `libamigacompat.a(amiga-os.o)`, no libatomic);
      the hot path (ceval.o) has 2 atomic calls, ceval_gil.o 31 -- check in `make check-m68k`
- [x] C2.4 case-insensitive imports: `amigaos` in `_CASE_INSENSITIVE_PLATFORMS` (PYTHONCASEOK
      as on darwin) -- patch 0009; test `tests/test_c2_import_case.py` (2 of 4 fail without
      the patch: verified)
- [x] C2.5 `$STACK: 1048576` cookie (in `Python/amigaos.c`) -- patch 0003; check in
      `make check-m68k`
- [x] C2.6 `_Py_thread_local` plain (= C0.4); m68k: no `__emutls` in the link map

### C3 Reachability sentinel (owner, on an Amiga) -- 1 of 2
- [x] C3.1 owner steps written (section below); the same layout and command run on the host
      binary: `make dist-host-check` -- f24f565
- [ ] C3.2 owner run result recorded (OWNER)

### C4/C5 -- 0 of 4 done (code for C4 is in; the Amiga run decides)
- [~] C4.1 subprocess on vfork: patch 0008; host proof runs test_subprocess through the
      vfork-only code (pass*). Amiga: sentinel line "subprocess over vfork".
- [~] C4.2 socket with getaddrinfo: neovim-amiga compat `netdb.o` linked; inet_ntop/pton
      added (`make test-inet`). Amiga: sentinel lines (need a TCP/IP stack running).
- [~] C4.3 select: linked; host test_select pass. Amiga: sentinel "select on a pipe".
- [ ] C5.1 resumable regression subset on the Amiga (host side exists: `tools/host-tests.sh`)
- Not started: C4a (LoadSeg extension plugins, amiga/arexx modules with AmigaPython's API).

## Measured sizes (m68k, -O2, soft-float, 2026-10-04)

| What | Bytes |
|---|---|
| text / data / bss | 4,570,668 / 327,248 / 160,140 |
| **loaded into RAM** (text+data+bss) | **5,058,056 (4.8 MiB)** |
| `python.exe` file / stripped (`bin/python3`) | 5,355,748 / 5,242,596 |
| `python314.zip`, 504 modules, `.pyc` -O0, stored | 10,137,914 |
| the same with `ZIPOPT=2` (no docstrings, no asserts) | 8,698,922 |
| largest objects | unicodedata 722 K, frozen modules 437 K, HACL hashes ~400 K (HMAC 213 K, SHA2 81 K, BLAKE2 52 K, SHA3 46 K), Python-ast 204 K, unicodeobject 192 K, pylifecycle 187 K, pystate 179 K, parser 158 K, unicodectype 133 K |

The research estimate (3-5 MB binary) holds: 4.8 MiB loaded. RAM for the C3 command =
4.8 MiB + heap (est. 1.5-2.5 MB) + 1 MB stack: plan for 8-9 MB free fast RAM. The text
segment is one ~4.4 MiB hunk: LoadSeg needs it contiguous (fragmented RAM can fail
before total free RAM runs out; unverified).

## Module set (owner decision O-2)

In (static): the bootstrap set (posix, _io, _sre, _codecs, _collections, itertools, time,
_signal, _thread, pwd, ...), array, _asyncio, _bisect, _contextvars, _csv, _heapq, _json,
_pickle, _queue, _random, _struct, _zoneinfo, math, cmath, _statistics, binascii, _md5,
_sha1, _sha2, _sha3, _blake2, _hmac, unicodedata, fcntl, grp, resource, select, _socket,
termios, _posixsubprocess, _datetime, _opcode.
Out: no library on m68k (zlib, bz2, lzma, zstd, ssl, hashlib, sqlite3, dbm, readline,
curses, tkinter, uuid, ctypes); no threads/fork/shm (multiprocessing, posixshmem,
interpreters*, remote_debugging); size (_decimal -> _pydecimal, _lsprof, mmap, syslog,
pyexpat, _elementtree, CJK codecs). Zip leaves out test, idlelib, tkinter, turtledemo,
ensurepip, sqlite3, curses, ctypes, multiprocessing, pydoc_data.
Trade-offs to decide: unicodedata (722 K; `_pyrepl` and `unicodedata.normalize` need it),
the HACL hashes (~400 K; without them `import hashlib` logs errors), pyexpat (xml, plistlib).

## Not implemented (and what it blocks)

| What | Where | Blocks |
|---|---|---|
| Threads (stubs) | D-4 | `Thread.start`, `concurrent.futures.ThreadPoolExecutor` |
| fork(); preexec_fn, user/group in subprocess | D-10 | `os.fork`, multiprocessing, those subprocess options (ENOSYS) |
| os.urandom is NOT cryptographically strong | `amiga/compat/getentropy.c` | `secrets`, key generation (hash seeds, temp names, `random` seeding are fine) |
| fcntl.lockf (no record locks in ixemul) | patch 0007 | lockf (flock works) |
| os.ttyname (3.14 sizes it with `_SC_TTY_NAME_MAX`) | config.site | os.ttyname (isatty works) |
| locale.nl_langinfo (ixemul has 8 of ~55 items) | config.site | nl_langinfo; `locale.getencoding()` answers utf-8 |
| os.RTLD_*, dlopen (no dynamic loading) | config.site | C extension modules not built in (C4a: LoadSeg plugins) |
| IPv6 (`--disable-ipv6`), inet_pton/ntop AF_INET6 -> EAFNOSUPPORT | amiga/compat/inet.c | IPv6 sockets |
| `Vol:path` strings in os.path (posixpath sees `:` as a name char) | -- | `os.path.join("Work:", "x")`; use `/Work/x` (O-5) |
| FPU build | D-6 | inline 68881 math (O-1) |

## C1a: what geekychris/python-amigaos4 (3.12.7, OS4 PPC, newlib) does, read 2026-10-04

Cloned to the session scratchpad; patches read, nothing built.
- Native AmigaDOS paths (newlib): patches posixpath.isabs/join, importlib `_path_join` /
  `_path_isabs`, fileutils `_Py_isabs`/joinpath and getpath.py (`DELIM=';'`, a prefix search
  over `python3:`, `System:python3`, `DH1:`) so `Vol:` counts as absolute and `Vol:`+`x` is
  `Vol:x`. ixemul's Unix view (`/Vol/x`) makes that unnecessary here; the same idea is the
  answer to O-5 if Amiga-style paths must work in os.path.
- `configure` host case `*-*-amigaos*` -> `ac_sys_system=AmigaOS` (we use the same name).
- Static modules via `Setup.local` (`*static*` + `*disabled*`), as here; they disable
  `_posixsubprocess` (no subprocess); we keep it on vfork.
- Several patches are bring-up probes writing `RAM:*.log` (pymain stages, path config,
  stat/open/mkdir, codec lookups) -- a diagnostic technique for C3 if startup fails silently;
  not carried. AmiSSL loaded lazily from PyInit (`amissl_lazy.c`): a model for a future `_ssl`.
- MorphOS SDK 3.14.4 patches: not looked for this session.

## Requests (not done here)

For **ixemul-vtcon** (belong in the SDK; each is a workaround here until then):
- **X1** `<stddef.h>` offsetof as `__builtin_offsetof` (the null-pointer cast is not an
  integer constant expression for gcc 6; configure's alignment probes fail) -- `amiga/include/stddef.h`
- **X2** C99 `<math.h>`/libm (log2, exp2, nextafter, fma, tgamma, acosh..., declarations
  and functions) -- newlib libm + `amiga/include/math.h`
- **X3** `<wchar.h>` wide string functions and `wcstol` -- newlib members + `amiga/compat/wcstol.c`
- **X4** `inet_ntop`/`inet_pton` -- `amiga/compat/inet.c`
- **X5** `/dev/urandom` or `getentropy` (= neovim-amiga R5); a real entropy source would
  make os.urandom strong -- `amiga/compat/getentropy.c`
- **X6** POSIX record locks (F_SETLK) for lockf; **X7** `_SC_TTY_NAME_MAX`; **X8** a full
  `<langinfo.h>`; **X9** `MAP_ANONYMOUS` alias (pymalloc would use mmap arenas; today malloc,
  4-byte aligned: `library/malloc.c` header is 20 bytes -- enough for CPython's 4)

For **neovim-amiga** compat (outside this repo; needs the owner's go-ahead):
- **N1** only if O-1 = FPU build: guard the `atan2` declaration in
  `amiga/compat/include/math.h` (and its definition in `math.c`) with `#ifndef __HAVE_68881__`
  (math-68881.h defines `atan2` as `static inline const double`).

## Owner decisions

- **O-1** FPU build? Needs: a return-ABI shim for ixemul's double-returning calls, N1, and a
  second dist. Recommended: stay soft-float until C3 runs; then measure pystone on both.
- **O-2** Module set (above): unicodedata, HACL hashes, pyexpat in or out.
- **O-3** Threads stay stubbed (real threads = making ixemul thread-aware; research option 4).
- **O-4** os.urandom weak (X5) acceptable, or make `os.urandom` raise instead (then CPython
  still starts on the hash-seed path only if that is split from os.urandom -- a patch).
- **O-5** Amiga-style `Vol:path` in os.path (OS4 port's approach) or document `/Vol/path`.
- **O-6** stdlib zip at -O0 (10.1 MB) or -O2 (8.7 MB, no docstrings/asserts).

## C3 owner steps (on an Amiga; this repo's agent never runs them)

Hardware: 68020 or better (030/060 fine; **no FPU needed**: soft-float build), **>= 9 MB
free fast RAM** (16 MB board), AmigaOS 3.x, UP-Term kit installed (ixemul-vtcon's
ixemul.library in LIBS:, vsh). A TCP/IP stack only for the optional socket lines.

1. On the Mac: `cd ~/Code/cpython-amiga && make dist` -> `build/m68k/dist/Python3/` (15 MB):
   - `Python3/bin/python3` (5.2 MB, the interpreter; carries `$STACK: 1048576`)
   - `Python3/lib/python314.zip` (10.1 MB, the stdlib)
   - `Python3/lib/python3.14/lib-dynload/` (empty directory -- copy it too)
   - `Python3/c3-sentinel.py`
2. Copy the whole `Python3` drawer to the Amiga, e.g. to `Work:Python3` (any volume that
   takes 30-character names; FFS is fine). Then, in an AmigaDOS shell:
   `Assign Python3: Work:Python3` (add it to `S:User-Startup` to keep it).
3. In UP-Term, in vsh, `cd Work:` (any directory with a few files), then:
   - `Avail FLUSH` -> note the **Total available** (and Fast) number = *before*.
   - `Date` -> note the time.
   - `Python3:bin/python3 -c "import os, re, json; print(json.dumps(os.listdir('.')))"`
   - `Date` -> note the time (end - start = the time).
   - `Avail FLUSH` -> note Total available = *after* (should equal *before*).
   PASS: one line of JSON listing the directory's entries, e.g. `["Python3", "foo", ...]`,
   prompt back, no requester. Optional peak RAM: run
   `Python3:bin/python3 -c "import os, re, json; input('Avail now, then Return')"` and run
   `Avail` in a second UP-Term window while it waits.
4. Then the sentinel: `Python3:bin/python3 Python3:c3-sentinel.py` -- every line should say
   `OK` (INFO lines are fine without a TCP/IP stack). Send back all of its output, the
   before/after/peak Avail numbers and the time.
5. If step 3 fails, send back the exact output and try, in order:
   - `Python3:bin/python3 -c "import sys; print(sys.prefix, sys.path)"` -- the prefix
     should be `/Python3`; if the stdlib is not found, `SetEnv PYTHONHOME /Python3`
     (ixemul reads ENV:), retry, and `UnSetEnv PYTHONHOME` afterwards.
   - `Python3:bin/python3 -S -c "print(1)"` (no site), then `-X importtime` on the one-liner.
   - "Fatal Python error" lines name the failing stage; a Guru/crash number with the
     address helps: `build/m68k/python.map` maps it to a function.
   - "not enough memory" with enough total free RAM: the 4.4 MiB code hunk needs one
     contiguous block -- retry right after a reboot.
   Known not-a-bug: `os.fork` is missing; `Thread.start()` raises RuntimeError.

## Gotchas

- macOS is case-insensitive: `python` would collide with `Python/`; the build target is
  `python.exe` (`make m68k` builds that name; dist renames it `bin/python3`).
- The compiler defines `AMIGA`/`amiga`/`amigaos`: guard with `__amigaos__`.
- `-m68020` at link picks libnix's crt0 (multilib `libm020`); `-m68020-60` keeps multilib `.`
  and ixemul's crt0 -- the CPU flag can stay in CFLAGS (configure links with it).
- `-m68881` changes the double return register to fp0 (D-6): never mix FPU objects with
  ixemul/libixcompat/newlib-libm calls that return doubles.
- The toolchain's `sys-include` (newlib) satisfies configure's header probes for
  `libintl.h`, `sys/statvfs.h`, `sys/lock.h`, `pthread.h`: answered `no` in config.site.
- ixemul's libc.a stubs: LVO = -6 * (syscall.def number + 4) (Open/Close/Expunge/Reserved).
- The host test machine ran with load average ~100 during test_subprocess (hot Mac): -j4 only.

## C3 run on the rig (main session, 2026-10-04 23:35-23:44)

Rig: FS-UAE default config (68020, 8 MB fast + 64 MB Z3, KS 3.1/OS 3.x, ixemul-vtcon 48.2 in LIBS:),
the dist copied to VTC:Python3, `Assign Python3: VTC:Python3`, `Stack 1100000`, run from AmigaShell
through the rig agent (not vsh).

- C3 sentinel line: `python3 -c "import os, re, json; print(json.dumps(os.listdir('.')))"` in RAM:
  PRINTED THE LISTING (["ENV", "Clipboards", "T"]), 36 s start to exit, Avail FLUSH before/after
  equal within 792 bytes (fast 69829328 -> 69828536).
- c3-sentinel.py (by /Python3/c3-sentinel.py; `Python3:c3-sentinel.py` gives rc 2 = O-5, Vol:path
  not handled): 14 OK, 1 FAIL, 183.4 s:
  OK platform, UTF-8, thread stubs, Thread.start raises, RecursionError, json, re, floats, C99 libm,
  math domain error, struct, listdir/stat, case-exact import, import JSON fails.
  FAIL subprocess over vfork (C4.1): FileNotFoundError(2).
- BUG stdout: every print arrives as reprs with the newline apart: `'OK   json round trip''\n'`.
  Looks like sys.stdout is the early-init stdprinter / a repr-writing fallback, not the io stack
  (check create_stdio / io init failing silently on ixemul isatty/fstat). Both runs show it.
- BUG sys.executable = '/Ram Disk//Python3:bin/python3' (argv0 Amiga form joined to the cwd);
  prefix /Python3 was found anyway.
- Speed: 36 s for the one-liner, 183 s for the sentinel on the rig's 68020 (not cycle-exact; the
  stock A1200 cannot run this: 2 MB chip only).
