/* <wchar.h> for ixemul 48.2, which declares only wint_t/WEOF and has no
 * wide string functions. These come from the toolchain's newlib libc.a,
 * as the self-contained members only (libnewlibwcs.a, top-level Makefile:
 * no locale, no malloc, no errno). wchar_t is gcc's (4 bytes, a code
 * point). Belongs in the ixemul-vtcon SDK (ledger request X3). */
#ifndef CPYTHON_AMIGA_WCHAR_H
#define CPYTHON_AMIGA_WCHAR_H
#pragma GCC system_header
#include_next <wchar.h>

size_t	 wcslen(const wchar_t *);
size_t	 wcsnlen(const wchar_t *, size_t);
long	 wcstol(const wchar_t *, wchar_t **, int);	/* amiga/compat/wcstol.c */
int	 wcscmp(const wchar_t *, const wchar_t *);
int	 wcsncmp(const wchar_t *, const wchar_t *, size_t);
int	 wcscoll(const wchar_t *, const wchar_t *);
size_t	 wcsxfrm(wchar_t *, const wchar_t *, size_t);
size_t	 wcslcpy(wchar_t *, const wchar_t *, size_t);
wchar_t	*wcscpy(wchar_t *, const wchar_t *);
wchar_t	*wcsncpy(wchar_t *, const wchar_t *, size_t);
wchar_t	*wcscat(wchar_t *, const wchar_t *);
wchar_t	*wcsncat(wchar_t *, const wchar_t *, size_t);
wchar_t	*wcschr(const wchar_t *, wchar_t);
wchar_t	*wcsrchr(const wchar_t *, wchar_t);
wchar_t	*wcsstr(const wchar_t *, const wchar_t *);
wchar_t	*wcspbrk(const wchar_t *, const wchar_t *);
size_t	 wcsspn(const wchar_t *, const wchar_t *);
size_t	 wcscspn(const wchar_t *, const wchar_t *);
wchar_t	*wcstok(wchar_t *, const wchar_t *, wchar_t **);
wchar_t	*wmemchr(const wchar_t *, wchar_t, size_t);
int	 wmemcmp(const wchar_t *, const wchar_t *, size_t);
wchar_t	*wmemcpy(wchar_t *, const wchar_t *, size_t);
wchar_t	*wmemmove(wchar_t *, const wchar_t *, size_t);
wchar_t	*wmemset(wchar_t *, wchar_t, size_t);
#endif
