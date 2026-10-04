/* The toolchain's libm.a (newlib's fdlibm) supplies the C99 math ixemul
 * 48.2 lacks (acosh asinh atanh erf erfc expm1 log1p log2 cbrt exp2
 * nextafter fma lgamma tgamma ...). Its wrappers report EDOM/ERANGE through
 * newlib's reentrancy struct: `_impure_ptr->_errno`, the struct's first
 * member. Point it at ixemul's errno (an int in crt0's data) so those
 * reports land where CPython reads them. newlib's EDOM/ERANGE are 33/34,
 * as in ixemul (BSD). Ledger: D-7; request X2 (C99 libm in ixemul). */
#include <errno.h>

void *_impure_ptr = &errno;
