/* <unistd.h> additions over ixemul 48.2's and neovim-amiga's compat one:
 * getentropy() (amiga/compat/getentropy.c; NOT cryptographically strong,
 * see there). Ledger request X5. */
#ifndef CPYTHON_AMIGA_UNISTD_H
#define CPYTHON_AMIGA_UNISTD_H
#pragma GCC system_header
#include_next <unistd.h>
int	getentropy(void *, size_t);
#endif
