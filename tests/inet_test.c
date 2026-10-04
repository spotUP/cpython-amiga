/* host test: amiga/compat/inet.c against the C library (AF_INET).
 * make test-inet */
#include <arpa/inet.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
const char *amiga_inet_ntop(int, const void *, char *, socklen_t);
int amiga_inet_pton(int, const char *, void *);
int main(void)
{
	static const char *in[] = { "0.0.0.0", "127.0.0.1", "255.255.255.255", "1.2.3.4",
		"256.1.1.1", "1.2.3", "1.2.3.4.5", "01.2.3.4", "1..2.3", "", "a.b.c.d",
		"1.2.3.4 ", " 1.2.3.4", "192.168.000.1", "10.0.0.255", "1.2.3.", ".1.2.3",
		"0.00.0.0", "100.200.250.255" };
	int fails = 0;
	for (size_t i = 0; i < sizeof in / sizeof *in; i++) {
		unsigned char a[4] = {9,9,9,9}, b[4] = {9,9,9,9};
		int r1 = amiga_inet_pton(AF_INET, in[i], a), r2 = inet_pton(AF_INET, in[i], b);
		/* a part with a leading zero: BSD libcs (macOS) read it as
		   decimal, glibc and musl reject it; this one rejects it */
		if (strcmp(in[i], "01.2.3.4") == 0 || strcmp(in[i], "192.168.000.1") == 0 ||
		    strcmp(in[i], "0.00.0.0") == 0)
			r2 = 0;
		if (r1 != r2 || (r1 == 1 && memcmp(a, b, 4))) {
			printf("FAIL pton \"%s\": %d vs %d\n", in[i], r1, r2); fails++;
		}
		if (r1 == 1) {
			char s1[16], s2[16];
			if (!amiga_inet_ntop(AF_INET, a, s1, sizeof s1) || !inet_ntop(AF_INET, a, s2, sizeof s2)
			    || strcmp(s1, s2)) { printf("FAIL ntop \"%s\"\n", in[i]); fails++; }
		}
	}
	{ unsigned char a[4] = {255,255,255,255}; char s[15];
	  errno = 0;
	  if (amiga_inet_ntop(AF_INET, a, s, sizeof s) || errno != ENOSPC) { printf("FAIL ENOSPC\n"); fails++; } }
	{ unsigned char a[16]; errno = 0;
	  if (amiga_inet_pton(AF_INET6, "::1", a) != -1 || errno != EAFNOSUPPORT) { printf("FAIL AF_INET6\n"); fails++; } }
	printf(fails ? "inet_test: %d FAILED\n" : "inet_test: ok\n", fails);
	return fails != 0;
}
