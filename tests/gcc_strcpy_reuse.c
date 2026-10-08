/* G-3 cross-build test (make test-gcc-btst / check-m68k): a register's load
 * must stay while an earlier store still reads it. bebbo's gcc 6.5 bbb pass
 * opt_strcpy joins `move x,dN; move dN,Y; tst dN` into `move x,Y`; after a
 * first `move dN,A` that was no match it took the next `move dN,B` as the
 * match and deleted the load: `move dN,A; move x,B`, A getting whatever dN
 * held (findutils 4.11's find: every directory's mode was 0177767, so
 * -type d matched nothing). Fixed by amiga/gcc/0004 (build/gcc/bin/cc1). */
short a, b;
extern void use(short *);

int
f(const short *p, short k)
{
	short m = *p;

	a = m;
	b = m;
	if (m == 0)
		return k;
	use(&a);
	return 2;
}
