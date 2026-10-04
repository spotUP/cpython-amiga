/* wcstol for ixemul 48.2 (none there; newlib's needs its locale). C99
 * semantics over the ASCII digits and white space, which is all a wide
 * number can hold in the "C" locale: optional sign, base 0/8/10/16 prefix
 * rules, ERANGE on overflow, *end at the first unused character (or at
 * the start if no digits). Searched first: ixemul libc, libixcompat,
 * neovim-amiga compat. Ledger request X3. */
#include <errno.h>
#include <limits.h>
#include <stddef.h>

long
wcstol(const wchar_t *s, wchar_t **end, int base)
{
	const wchar_t *p = s;
	unsigned long acc = 0, lim;
	int neg = 0, any = 0, over = 0;

	while (*p == ' ' || (*p >= '\t' && *p <= '\r'))
		p++;
	if (*p == '-' || *p == '+')
		neg = *p++ == '-';
	if ((base == 0 || base == 16) && p[0] == '0' && (p[1] == 'x' || p[1] == 'X')
	    && ((p[2] >= '0' && p[2] <= '9') || (p[2] >= 'a' && p[2] <= 'f') ||
	        (p[2] >= 'A' && p[2] <= 'F'))) {
		p += 2;
		base = 16;
	} else if (base == 0)
		base = *p == '0' ? 8 : 10;
	if (base < 2 || base > 36) {
		if (end)
			*end = (wchar_t *)s;
		errno = EINVAL;
		return 0;
	}
	lim = neg ? (unsigned long)LONG_MAX + 1 : (unsigned long)LONG_MAX;
	for (;; p++) {
		int d;
		if (*p >= '0' && *p <= '9') d = *p - '0';
		else if (*p >= 'a' && *p <= 'z') d = *p - 'a' + 10;
		else if (*p >= 'A' && *p <= 'Z') d = *p - 'A' + 10;
		else break;
		if (d >= base)
			break;
		any = 1;
		if (over || acc > (lim - d) / base)
			over = 1;
		else
			acc = acc * base + d;
	}
	if (end)
		*end = (wchar_t *)(any ? p : s);
	if (over) {
		errno = ERANGE;
		return neg ? LONG_MIN : LONG_MAX;
	}
	return neg ? (long)(0 - acc) : (long)acc;
}
