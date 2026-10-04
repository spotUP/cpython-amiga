/* getentropy() for ixemul 48.2, which has no /dev/urandom, getrandom or
 * getentropy (neovim-amiga request R5). CPython cannot start without
 * random bytes (hash randomization), and os.urandom uses the same source.
 *
 * NOT CRYPTOGRAPHICALLY STRONG. AmigaOS 3.x has no entropy pool; this
 * gathers what varies between runs and moments -- timer.device's E-clock
 * (CLOCK_MONOTONIC, 1.4 us) sampled around data-dependent busy loops so
 * interrupt and DMA timing jitter is folded in, the video beam position,
 * the wall clock, the process id and heap/stack addresses -- and mixes
 * it with the splitmix64 finalizer. Good enough for hash seeds, temp
 * names and seeding `random`; not for keys (`secrets`, ssl). Ledger X5.
 * Searched first: ixemul, libixcompat, neovim-amiga compat, newlib. */
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/time.h>

#ifndef EIO
#define EIO 5
#endif

static unsigned long long pool;
static unsigned long long counter;

static unsigned long long
mix(unsigned long long z)
{
	z += 0x9e3779b97f4a7c15ULL;
	z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
	z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
	return z ^ (z >> 31);
}

static unsigned long long
sample(void)
{
	struct timespec ts;
	unsigned long long v = 0;

	if (clock_gettime(CLOCK_MONOTONIC, &ts) == 0)
		v = (unsigned long long)ts.tv_sec * 1000000000ULL + (unsigned long)ts.tv_nsec;
#ifdef __amigaos__
	/* VHPOSR: the custom chips' beam position, on every classic Amiga */
	v ^= (unsigned long long)*(volatile unsigned short *)0xdff006 << 48;
#endif
	return v;
}

static void
stir(int rounds)
{
	volatile unsigned long spin;
	int i;

	for (i = 0; i < rounds; i++) {
		unsigned long n = (unsigned long)(pool & 0x3ff) + 64;
		for (spin = 0; spin < n; spin++)
			;
		pool = mix(pool ^ sample());
	}
}

int
getentropy(void *buf, size_t len)
{
	unsigned char *out = buf;

	if (len > 256) {
		errno = EIO;
		return -1;
	}
	if (counter == 0) {
		struct timeval tv;
		void *heap = malloc(16);
		gettimeofday(&tv, NULL);
		pool = mix((unsigned long long)tv.tv_sec << 20 ^ (unsigned long)tv.tv_usec);
		pool = mix(pool ^ (unsigned long)getpid() ^ (unsigned long)&tv);
		pool = mix(pool ^ (unsigned long)heap);
		free(heap);
		stir(32);
	}
	while (len > 0) {
		unsigned long long w;
		size_t n = len < 8 ? len : 8;
		stir(4);
		w = mix(pool ^ ++counter);
		memcpy(out, &w, n);
		out += n;
		len -= n;
	}
	return 0;
}
