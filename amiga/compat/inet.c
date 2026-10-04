/* inet_ntop/inet_pton for ixemul 48.2 (it has inet_aton/inet_ntoa only).
 * IPv4 as POSIX specifies it (dotted decimal, exactly four parts, no
 * octal or hex, each part 0..255); AF_INET6 fails with EAFNOSUPPORT, as
 * ixemul's stack (bsdsocket.library) has no IPv6. CPython 3.14's socket
 * module needs both. Searched first: ixemul libc, libixcompat,
 * neovim-amiga compat, the toolchain's newlib. Ledger request X4. */
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <errno.h>
#include <stddef.h>

#ifndef EAFNOSUPPORT
#define EAFNOSUPPORT 47
#endif
#ifndef ENOSPC
#define ENOSPC 28
#endif

const char *
inet_ntop(int af, const void *src, char *dst, socklen_t size)
{
	const unsigned char *a = src;
	char buf[16], *p = buf;
	int i;
	size_t n;

	if (af != AF_INET) {
		errno = EAFNOSUPPORT;
		return NULL;
	}
	for (i = 0; i < 4; i++) {
		unsigned v = a[i];
		if (v >= 100) *p++ = (char)('0' + v / 100);
		if (v >= 10) *p++ = (char)('0' + v / 10 % 10);
		*p++ = (char)('0' + v % 10);
		*p++ = i < 3 ? '.' : '\0';
	}
	n = (size_t)(p - buf);
	if (n > (size_t)size) {
		errno = ENOSPC;
		return NULL;
	}
	for (i = 0; (size_t)i < n; i++)
		dst[i] = buf[i];
	return dst;
}

int
inet_pton(int af, const char *src, void *dst)
{
	unsigned char out[4];
	int part = 0, digits = 0;
	unsigned v = 0;

	if (af != AF_INET) {
		errno = EAFNOSUPPORT;
		return -1;
	}
	for (;; src++) {
		if (*src >= '0' && *src <= '9') {
			if (digits && v == 0)
				return 0;	/* leading zero */
			v = v * 10 + (unsigned)(*src - '0');
			if (v > 255 || ++digits > 3)
				return 0;
		} else if ((*src == '.' || *src == '\0') && digits) {
			out[part++] = (unsigned char)v;
			if (*src == '\0')
				break;
			if (part == 4)
				return 0;
			v = 0;
			digits = 0;
		} else
			return 0;
	}
	if (part != 4)
		return 0;
	for (part = 0; part < 4; part++)
		((unsigned char *)dst)[part] = out[part];
	return 1;
}
