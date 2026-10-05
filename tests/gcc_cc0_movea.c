/* G-2 cross-build test (make check-m68k): after a call, a branch must not
 * test flags the callee left. bebbo's gcc 6.5 (20260819) bbb pass
 * opt_strcpy turned `move.l (-4,a5),d0; move.l d0,a2; tst.l d0` into
 * `move.l (-4,a5),a2` -- movea sets no flags -- so `if (result == 0)`
 * below branched on the CCR of dealloc(). The shape of builtin sum()'s
 * generic loop: sum(range(200000)) returned NULL without an exception.
 * Fixed by amiga/gcc/0003 (build/gcc/bin/cc1). */
typedef struct O { long rc; } O;
extern O *next(O *);
extern O *add(O *, O *);
extern void dealloc(O *);

static inline void
decref(O *o)
{
    if (o->rc <= 0x3fffffff) {
        if (--o->rc == 0) {
            dealloc(o);
        }
    }
}

O *
loop(O *it, O *result)
{
    for (;;) {
        O *item = next(it);
        if (item == 0) {
            break;
        }
        O *temp = add(result, item);
        decref(result);
        decref(item);
        result = temp;
        if (result == 0) {
            break;
        }
    }
    decref(it);
    return result;
}
