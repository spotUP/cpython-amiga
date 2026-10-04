/* host test for amiga/compat/getentropy.c (the logic, not the entropy):
 * fills the buffer, successive calls differ, >256 bytes fails with EIO.
 * make test-getentropy */
#include <errno.h>
#include <stdio.h>
#include <string.h>
int amiga_getentropy(void *, size_t);
int main(void)
{
	unsigned char a[256], b[256], z[256];
	int fails = 0, i, ones = 0;
	memset(a, 0, sizeof a); memset(z, 0, sizeof z);
	if (amiga_getentropy(a, sizeof a) != 0) { puts("FAIL 256"); fails++; }
	if (amiga_getentropy(b, sizeof b) != 0) { puts("FAIL 256 again"); fails++; }
	if (!memcmp(a, z, sizeof a)) { puts("FAIL all zero"); fails++; }
	if (!memcmp(a, b, sizeof a)) { puts("FAIL repeated"); fails++; }
	for (i = 0; i < 256; i++) ones += __builtin_popcount(a[i]);
	if (ones < 900 || ones > 1150) { printf("FAIL bit balance %d of 2048\n", ones); fails++; }
	{ unsigned char c[5] = {0}; if (amiga_getentropy(c, 3) != 0 || c[3] || c[4]) { puts("FAIL short"); fails++; } }
	errno = 0;
	if (amiga_getentropy(a, 257) != -1 || errno != EIO) { puts("FAIL >256"); fails++; }
	printf(fails ? "getentropy_test: %d FAILED\n" : "getentropy_test: ok\n", fails);
	return fails != 0;
}
