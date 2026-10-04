/* host test for amiga/compat/wcstol.c against the C library's wcstol
 * (same `long` width on both sides; the range cases cover 32 and 64 bit).
 * make test-wcstol */
#include <errno.h>
#include <stdio.h>
#include <wchar.h>
long amiga_wcstol(const wchar_t *, wchar_t **, int);
int main(void)
{
	static const wchar_t *in[] = { L"0", L"42", L"  -17x", L"+9", L"0x1F", L"0X", L"017",
		L"2147483647", L"2147483648", L"-2147483648", L"-2147483649",
		L"99999999999999999999", L"9223372036854775807", L"9223372036854775808", L"-9223372036854775809", L"", L"abc", L"z", L"-0x10", L"  \t\n7" };
	static const int bases[] = { 10, 0, 16, 36, 8, 2 };
	int fails = 0;
	for (size_t i = 0; i < sizeof in / sizeof *in; i++)
		for (size_t b = 0; b < sizeof bases / sizeof *bases; b++) {
			wchar_t *e1, *e2; long r1, r2; int er1, er2;
			errno = 0; r1 = amiga_wcstol(in[i], &e1, bases[b]); er1 = errno;
			errno = 0; r2 = wcstol(in[i], &e2, bases[b]); er2 = errno;
			/* "0X": C99 parses the "0" (end at 1); macOS's libc
			   reports no conversion. Check it against the standard. */
			if (in[i][0] == '0' && in[i][1] == 'X' && in[i][2] == 0 && (bases[b] == 0 || bases[b] == 16)) { r2 = 0; e2 = (wchar_t *)in[i] + 1; }
			if (r1 != r2 || e1 - in[i] != e2 - in[i] || (er1 == ERANGE) != (er2 == ERANGE)) {
				printf("FAIL %ls base %d: %ld/%td vs %ld/%td\n", in[i], bases[b], r1, e1 - in[i], r2, e2 - in[i]);
				fails++;
			}
		}
	printf(fails ? "wcstol_test: %d FAILED\n" : "wcstol_test: ok\n", fails);
	return fails != 0;
}
