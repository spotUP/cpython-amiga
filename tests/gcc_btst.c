/* G-1 cross-build test (make check-m68k): `flags & 1` on an int argument in
 * memory must test bit 0 of its LOW byte (offset 3, big-endian). bebbo's
 * gcc 6.5 (20260819) emitted `btst #-24,(16,a5)` for wo() at -O1: bit 24 --
 * the code that made PyFile_WriteObject() ignore Py_PRINT_RAW, so print()
 * wrote repr()s. Fixed by amiga/gcc/0001 (build/gcc/bin/cc1). */
extern int g(void *), h(void *);
extern void *k(void *);

int
wo(void *v, void *f, int flags)
{
    void *w = k(f);
    if (!w) {
        return -1;
    }
    if (flags & 1) {
        return g(v);
    }
    return h(v);
}
