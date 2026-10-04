/* <stddef.h> for ixemul 48.2: its offsetof is the pre-C89 null-pointer
 * cast, which gcc 6 does not accept as an integer constant expression
 * (array sizes, _Static_assert, configure's alignment probes). Use gcc's
 * builtin. Belongs in the ixemul-vtcon SDK (ledger request X1). */
#ifndef CPYTHON_AMIGA_STDDEF_H
#define CPYTHON_AMIGA_STDDEF_H
#pragma GCC system_header
#include_next <stddef.h>
#undef offsetof
#define offsetof(type, member) __builtin_offsetof(type, member)
#endif
