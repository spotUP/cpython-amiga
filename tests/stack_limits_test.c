/* C2.2 host test: the AmigaOS stack-limit choice (pycore_amigaos.h),
 * the pure part of hardware_stack_limits()'s __amigaos__ branch.
 * Build+run: make test-stack */
#include <stdio.h>
#include "pycore_amigaos.h"

static int fails;
#define CHECK(c) do { if (!(c)) { printf("FAIL line %d: %s\n", __LINE__, #c); fails++; } } while (0)

int main(void)
{
    uintptr_t base, top;

    /* sp inside the task's stack: exactly the task's bounds */
    CHECK(_PyAmiga_StackLimits(0x200800, 0x100000, 0x200000 + 0x100000, 32768, &base, &top) == 1);
    CHECK(base == 0x100000 && top == 0x300000);

    /* sp at the lowest valid byte still counts as inside */
    CHECK(_PyAmiga_StackLimits(0x100000, 0x100000, 0x300000, 32768, &base, &top) == 1);

    /* sp == upper is outside (upper is one past the end) */
    CHECK(_PyAmiga_StackLimits(0x300000, 0x100000, 0x300000, 32768, &base, &top) == 0);

    /* stack swapped behind exec's back: fall back to sp's page - 32 KB */
    CHECK(_PyAmiga_StackLimits(0x7f0123, 0x100000, 0x300000, 32768, &base, &top) == 0);
    CHECK(top == 0x7f1000 && base == 0x7f1000 - 32768);

    /* nonsense bounds (lower >= upper) also take the fallback */
    CHECK(_PyAmiga_StackLimits(0x150000, 0x300000, 0x100000, 32768, &base, &top) == 0);

    printf(fails ? "stack_limits_test: %d FAILED\n" : "stack_limits_test: ok\n", fails);
    return fails != 0;
}
