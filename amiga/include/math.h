/* <math.h> additions: C99 functions neither ixemul 48.2's <math.h> nor
 * neovim-amiga's compat <math.h> declares. They are linked from the
 * toolchain's newlib libm.a (fdlibm; --with-libm in tools/configure-m68k.sh,
 * errno hook in amiga/compat/newlib-errno.c). Ledger request X2. */
#ifndef CPYTHON_AMIGA_MATH_H
#define CPYTHON_AMIGA_MATH_H
#pragma GCC system_header
#include_next <math.h>

double	log2(double);
double	exp2(double);
double	nextafter(double, double);
double	fma(double, double, double);
double	tgamma(double);
double	scalbn(double, int);
int	ilogb(double);
double	nearbyint(double);
long	lround(double);
long long llround(double);
double	remquo(double, double, int *);
#endif
