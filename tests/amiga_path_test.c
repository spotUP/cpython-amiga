/* W35 host test: AmigaDOS-absolute paths to ixemul's Unix view, the pure
 * part of _Py_abspath()'s __amigaos__ branch (pycore_amigaos.h). The rig
 * showed sys.executable = '/Ram Disk//Python3:bin/python3' (argv[0]
 * "Python3:bin/python3" joined to the current directory) and
 * `python3 Python3:c3-sentinel.py` failing with "can't open file".
 * Build+run: make test-amiga-path */
#include <stdio.h>
#include <wchar.h>
#include "pycore_amigaos.h"

static int fails;
#define CHECK(c) do { if (!(c)) { printf("FAIL line %d: %s\n", __LINE__, #c); fails++; } } while (0)

/* the Unix form of an AmigaDOS-absolute path, rest appended */
static const wchar_t *
unix_of(const wchar_t *base, const wchar_t *rest)
{
    static wchar_t out[256];
    size_t n = _PyAmiga_DevicePrefix(base);
    if (n < 2 || _PyAmiga_UnixPath(base, n, rest, out, 256) < 0) {
        return L"(error)";
    }
    return out;
}

int main(void)
{
    /* AmigaDOS-absolute: the first component holds the ':' */
    CHECK(_PyAmiga_DevicePrefix(L"Python3:bin/python3") == 8);
    CHECK(_PyAmiga_DevicePrefix(L"Ram Disk:") == 9);
    CHECK(_PyAmiga_DevicePrefix(L"PROGDIR:python3") == 8);
    CHECK(_PyAmiga_DevicePrefix(L":c/dir") == 1);
    /* Unix and relative paths are not, a ':' after a '/' is a name char */
    CHECK(_PyAmiga_DevicePrefix(L"/Python3/bin/python3") == 0);
    CHECK(_PyAmiga_DevicePrefix(L"bin/python3") == 0);
    CHECK(_PyAmiga_DevicePrefix(L"dir/a:b") == 0);
    CHECK(_PyAmiga_DevicePrefix(L"") == 0);

    /* the rig's argv[0] and script argument */
    CHECK(wcscmp(unix_of(L"Python3:bin/python3", L""), L"/Python3/bin/python3") == 0);
    CHECK(wcscmp(unix_of(L"Python3:c3-sentinel.py", L""), L"/Python3/c3-sentinel.py") == 0);
    /* a bare volume, with and without a name to append; spaces kept */
    CHECK(wcscmp(unix_of(L"Ram Disk:", L""), L"/Ram Disk") == 0);
    CHECK(wcscmp(unix_of(L"Ram Disk:", L"T/x"), L"/Ram Disk/T/x") == 0);
    /* a resolved PROGDIR: ("VTC:Python3/bin" from NameFromLock) + rest */
    CHECK(wcscmp(unix_of(L"VTC:Python3/bin", L"python3"), L"/VTC/Python3/bin/python3") == 0);
    CHECK(wcscmp(unix_of(L"VTC:Python3/bin/", L"python3"), L"/VTC/Python3/bin/python3") == 0);

    /* too small an output buffer fails instead of overflowing */
    wchar_t small[8];
    CHECK(_PyAmiga_UnixPath(L"Python3:bin", 8, L"", small, 8) == -1);
    CHECK(_PyAmiga_UnixPath(L"Work:", 5, L"", small, 8) == 5 && wcscmp(small, L"/Work") == 0);

    if (fails) {
        printf("[FAIL] %d check(s)\n", fails);
        return 1;
    }
    printf("[OK] amiga path checks\n");
    return 0;
}
