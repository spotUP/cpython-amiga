/* C2.1 compile-time check, built with the m68k compiler against the m68k
 * build's headers (make check-m68k): the GC and PyStackRef keep flags in the
 * low two bits of object pointers, so PyObject and PyGC_Head must be at
 * least 4-byte aligned even though the m68k-amigaos ABI aligns int and
 * pointers to 2. Without the gh-127545 backport the asserts fail. */
#define Py_BUILD_CORE 1
#include "Python.h"
#include "pycore_interp_structs.h"

_Static_assert(_Alignof(long) == 2, "this is the 2-byte-aligned m68k ABI");
_Static_assert(_Alignof(PyObject) >= 4, "PyObject must be 4-aligned");
_Static_assert(_Alignof(PyVarObject) >= 4, "PyVarObject must be 4-aligned");
_Static_assert(_Alignof(PyGC_Head) >= 4, "PyGC_Head must be 4-aligned");
_Static_assert(sizeof(PyGC_Head) % 4 == 0, "PyGC_Head keeps objects 4-aligned");
_Static_assert(sizeof(PyObject) % 4 == 0, "PyObject size keeps arrays aligned");

int align_check_dummy;
