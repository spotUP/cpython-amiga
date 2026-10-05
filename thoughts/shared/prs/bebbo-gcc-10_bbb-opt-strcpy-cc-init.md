`opt_strcpy` merges `move.l x,d0; move.l d0,Y; tst.l d0` into `move.l x,Y` when `NOTICE_UPDATE_CC` says the move sets the flags for the tested value. It ran `NOTICE_UPDATE_CC` on a stale `cc_status`: a move to an address register leaves `cc_status` untouched, so a `value2 == dst` left over from an earlier insn passed the check, the merge produced `move.l x,aN` -- which sets no flags -- and the `tst` was dropped. The branch after it then tested whatever flags the previous call left.

The fix resets `cc_status` (`CC_STATUS_INIT`) before `NOTICE_UPDATE_CC`, as the pass's other callers do.

**Reproducer** (`-m68020-60 -O2`), the shape of a loop that drops a reference and then tests the next result:

```c
typedef struct O { long rc; } O;
extern O *next(O *); extern O *add(O *, O *); extern void dealloc(O *);
static inline void decref(O *o)
{ if (o->rc <= 0x3fffffff) { if (--o->rc == 0) dealloc(o); } }
O *loop(O *it, O *result)
{
    for (;;) {
        O *item = next(it); if (item == 0) break;
        O *temp = add(result, item); decref(result); decref(item);
        result = temp; if (result == 0) break;
    }
    return result;
}
```

Before (after the call to `dealloc`):
```
addql #4,sp
moveal a5@(-4),a2     | sets no flags
bnes ...              | tests the flags dealloc() left
```
After:
```
movel a5@(-4),d0      | sets the flags for result
addql #4,sp
moveal d0,a2
bnes ...
```

Found by CPython 3.14 on AmigaOS: builtin `sum()`'s generic loop returned NULL without an exception (`sum(range(200000))`). With the fix, CPython's checks pass on an A1200/68060 (FS-UAE). Compiling all 228 CPython objects with the old and new cc1, exactly 3 functions change (`sum`, `math.prod`, `functools.partial` repr), the 3 sites a scan for this shape finds.

Tested on `amiga6` (8c1fd39db), whose `opt_strcpy` is the same code as on `amiga6.5`; this branch is `amiga6.5` + the one change.
