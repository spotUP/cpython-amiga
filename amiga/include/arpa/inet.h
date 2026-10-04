/* <arpa/inet.h> for ixemul 48.2: adds inet_ntop/inet_pton (IPv4 only),
 * implemented in amiga/compat/inet.c. Ledger request X4. */
#ifndef CPYTHON_AMIGA_ARPA_INET_H
#define CPYTHON_AMIGA_ARPA_INET_H
#pragma GCC system_header
#include_next <arpa/inet.h>
#include <sys/socket.h>
const char *inet_ntop(int, const void *, char *, socklen_t);
int	inet_pton(int, const char *, void *);
#endif
