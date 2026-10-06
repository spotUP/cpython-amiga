# CPython 3.14 for AmigaOS 3.x / 68020-68060 + FPU / ixemul (UP-Term PY1).
# Cross build with bebbo's gcc 6.5; ledger:
# thoughts/shared/plans/2026-10-04-py1-progress.md. Commands: RULES.md.
# The workspace directory that holds this repo and its siblings (the upterm
# meta-repo creates it); the sibling defaults below hang off it.
UPTERM_ROOT ?= $(abspath $(CURDIR)/..)
AMIGA    ?= $(HOME)/opt/amiga
AGCC     ?= $(AMIGA)/bin/m68k-amigaos-gcc
AAR      ?= $(AMIGA)/bin/m68k-amigaos-ar
# the Neovim port's compat layer, compiled here with this build's flags (no copy)
NVCOMPAT ?= $(UPTERM_ROOT)/neovim-amiga/amiga/compat
# code: 68020..68060, soft-float (decision D-6 in the ledger): ixemul.library
# returns doubles in d0/d1, while gcc 6.5 with -m68881 expects them in fp0,
# so an FPU build needs a return-ABI shim for every double-returning libc
# call (not built yet). Linked WITHOUT -m68020: with it the driver picks
# libnix's crt0 (neovim-amiga D-7).
ACPU     ?= -m68020-60
GCCLIB    = $(AMIGA)/lib/gcc/m68k-amigaos/6.5.0b
SRC       = vendor/cpython
TAG      ?= v3.14.7
BASE     ?= 823f032
HOSTPY   ?= /opt/homebrew/bin/python3.14
B         = build/m68k
H         = build/host
J        ?= -j4

.PHONY: all fetch patches cc1 test-gcc-btst host host-test test-stack test-amiga-path test-wcstol test-inet test-getentropy compat m68k check-m68k zip dist dist-host-check clean
all: m68k

# ---- upstream + our patch series ---------------------------------------------
fetch:
	tools/fetch-cpython.sh $(TAG)
patches:
	rm -f patches/*.patch
	git -C $(SRC) format-patch -q -o $(CURDIR)/patches $(BASE)..amiga-3.14
	ls patches

# ---- C0: host proof (macOS, the reduced configuration) -----------------------
$(H)/Makefile: $(SRC)/configure amiga/config.site-host
	mkdir -p $(H)
	cd $(H) && CONFIG_SITE=$(CURDIR)/amiga/config.site-host MODULE_BUILDTYPE=static \
	  $(CURDIR)/$(SRC)/configure --with-pthread-stubs --without-mimalloc \
	  --without-doc-strings --disable-test-modules --without-ensurepip > configure.log
host: $(H)/Makefile
	cp amiga/Setup.local $(H)/Modules/Setup.local
	$(MAKE) -C $(H) $(J) > $(H)/make.log 2>&1 || (tail -30 $(H)/make.log; false)
test-inet: tests/inet_test.c amiga/compat/inet.c
	mkdir -p $(H)
	cc -Wall -Dinet_ntop=amiga_inet_ntop -Dinet_pton=amiga_inet_pton -c -o $(H)/inet_amiga.o amiga/compat/inet.c
	cc -Wall -o $(H)/inet_test tests/inet_test.c $(H)/inet_amiga.o
	$(H)/inet_test
test-getentropy: tests/getentropy_test.c amiga/compat/getentropy.c
	mkdir -p $(H)
	cc -Wall -Dgetentropy=amiga_getentropy -c -o $(H)/getentropy_amiga.o amiga/compat/getentropy.c
	cc -Wall -o $(H)/getentropy_test tests/getentropy_test.c $(H)/getentropy_amiga.o
	$(H)/getentropy_test
host-test: host test-stack test-amiga-path test-wcstol test-inet test-getentropy
	tools/host-tests.sh
test-stack: $(H)/stack_limits_test
	$(H)/stack_limits_test
test-amiga-path: tests/amiga_path_test.c $(SRC)/Include/internal/pycore_amigaos.h
	mkdir -p $(H)
	cc -Wall -I$(SRC)/Include/internal -o $(H)/amiga_path_test tests/amiga_path_test.c
	$(H)/amiga_path_test
test-wcstol: tests/wcstol_test.c amiga/compat/wcstol.c
	mkdir -p $(H)
	cc -Wall -Dwcstol=amiga_wcstol -c -o $(H)/wcstol_amiga.o amiga/compat/wcstol.c
	cc -Wall -o $(H)/wcstol_test tests/wcstol_test.c $(H)/wcstol_amiga.o
	$(H)/wcstol_test
$(H)/stack_limits_test: tests/stack_limits_test.c $(SRC)/Include/internal/pycore_amigaos.h
	mkdir -p $(H)
	cc -Wall -I$(SRC)/Include/internal -o $@ tests/stack_limits_test.c

# ---- G-1: this port's cc1 (bebbo's gcc + amiga/gcc/*.patch) ------------------
# The installed cc1 tests the wrong byte for `x & 1` on an int in memory
# (amiga/gcc/0001). Every m68k object is compiled with -B$(GCCB)/, which
# makes the installed driver run this cc1. The installed toolchain is not
# touched (request G-1 in the ledger).
GCCB = $(CURDIR)/build/gcc/bin
CC1  = $(GCCB)/cc1
cc1: $(CC1)
$(CC1): tools/build-cc1.sh $(wildcard amiga/gcc/*.patch)
	tools/build-cc1.sh
test-gcc-btst: $(CC1)
	tools/check-m68k.sh --gcc-only

# ---- compat: neovim-amiga's amiga/compat, built with this CPU/FPU ------------
COMPAT_SRCS = netdb.c posix.c eprintf.c math.c
COMPAT_OBJS = $(addprefix $(B)/compat/,$(COMPAT_SRCS:.c=.o)) $(B)/compat/amiga-os.o
ACFLAGS     = -mcrt=ixemul -B$(GCCB)/ $(ACPU) -O2 -fno-strict-aliasing -Wall -Wno-unused
$(B)/compat/%.o: $(NVCOMPAT)/%.c $(CC1)
	@mkdir -p $(dir $@)
	$(AGCC) $(ACFLAGS) -I$(NVCOMPAT)/include -c -o $@ $<
# NDK headers only; the atomic builtins are defined there, not called
$(B)/compat/amiga-os.o: $(NVCOMPAT)/amiga-os.c $(CC1)
	@mkdir -p $(dir $@)
	$(AGCC) $(ACFLAGS) -fno-builtin -c -o $@ $<
$(B)/libamigacompat.a: $(COMPAT_OBJS)
	rm -f $@
	$(AAR) rcs $@ $(COMPAT_OBJS)
# this port's own additions (amiga/compat): newlib libm's errno hook,
# wcstol, inet_ntop/pton, getentropy
$(B)/cpyamiga/%.o: amiga/compat/%.c $(CC1)
	@mkdir -p $(dir $@)
	$(AGCC) $(ACFLAGS) -I$(NVCOMPAT)/include -c -o $@ $<
$(B)/libcpyamiga.a: $(B)/cpyamiga/newlib-errno.o $(B)/cpyamiga/wcstol.o $(B)/cpyamiga/inet.o \
                  $(B)/cpyamiga/getentropy.o
	rm -f $@
	$(AAR) rcs $@ $^
# wide string functions ixemul lacks: the self-contained members of the
# toolchain's newlib libc.a (no locale/malloc/errno; checked with nm -u)
NEWLIBC   = $(AMIGA)/m68k-amigaos/lib/libc.a
WCS_FUNCS = wcscat wcschr wcscmp wcscoll wcscpy wcscspn wcslcpy wcslen wcsncat \
            wcsncmp wcsncpy wcsnlen wcspbrk wcsrchr wcsspn wcsstr wcstok wcsxfrm \
            wmemchr wmemcmp wmemcpy wmemmove wmemset
$(B)/libnewlibwcs.a: $(NEWLIBC)
	rm -rf $(B)/newlibwcs && mkdir -p $(B)/newlibwcs
	cd $(B)/newlibwcs && $(AAR) x $(NEWLIBC) $(addprefix lib_a-,$(addsuffix .o,$(WCS_FUNCS)))
	rm -f $@
	$(AAR) rcs $@ $(B)/newlibwcs/*.o
compat: $(B)/libamigacompat.a $(B)/libcpyamiga.a $(B)/libnewlibwcs.a

# ---- C1: cross build ---------------------------------------------------------
$(B)/Makefile: $(SRC)/configure amiga/config.site tools/configure-m68k.sh $(CC1) \
               $(B)/libamigacompat.a $(B)/libcpyamiga.a $(B)/libnewlibwcs.a
	tools/configure-m68k.sh
	@# a new cc1 or new configure answers: CPython's Makefile does not track
	@# either, and an unchanged pyconfig.h keeps its date -- recompile all
	find $(B)/Modules $(B)/Objects $(B)/Parser $(B)/Programs $(B)/Python -name '*.o' -delete
	rm -f $(B)/libpython3.14.a $(B)/python.exe
m68k: $(B)/Makefile
	cp amiga/Setup.local $(B)/Modules/Setup.local
	$(MAKE) -C $(B) $(J) python.exe > $(B)/make.log 2>&1 || (tail -30 $(B)/make.log; false)

check-m68k:
	tools/check-m68k.sh

# ---- C1.6 / C3: what goes onto the Amiga --------------------------------------
# Python3/bin/python3, Python3/lib/python314.zip (stdlib .pyc, host-compiled),
# Python3/lib/python3.14/lib-dynload/ (empty: getpath's exec_prefix landmark)
SYSCONFIGDATA = $(B)/build/lib.amigaos-m68k-3.14/_sysconfigdata__amigaos_.py
ZIPOPT ?= 0
$(SYSCONFIGDATA): $(B)/python.exe
	$(MAKE) -C $(B) pybuilddir.txt > $(B)/sysconfig.log 2>&1
zip: $(SYSCONFIGDATA)
	$(HOSTPY) tools/mkzip.py $(SRC)/Lib $(SYSCONFIGDATA) $(B)/python314.zip --optimize $(ZIPOPT)
D = $(B)/dist/Python3
dist: zip check-m68k
	rm -rf $(B)/dist && mkdir -p $(D)/bin $(D)/lib/python3.14/lib-dynload
	cp $(B)/python.stripped $(D)/bin/python3
	cp $(B)/python314.zip $(D)/lib/python314.zip
	cp amiga/c3-sentinel.py $(D)/c3-sentinel.py
	du -sk $(D) $(D)/bin/python3 $(D)/lib/python314.zip
# the same layout around the HOST proof binary: the C3 command on this Mac
dist-host-check: host zip
	tools/dist-host-check.sh

clean:
	rm -rf build
