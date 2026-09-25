/* A pointer chase running alongside a unit-stride stream.  The chase is
   unpredictable and every prefetch issued for it is wasted bandwidth and
   a wasted cache line; the stream is perfectly predictable.  This is the
   case the hint's filter field exists for: keep the chase's demand
   requests away from the stream's prefetcher so it is not polluted. */
#include <stdio.h>
#include <stdlib.h>
#include "rng.h"
#include "champsim_markers.h"

#define N (1 << 22)           /* 4 M nodes, 32 MB of next-pointers */
#define STREAM_N (1 << 23)

int main(void)
{
  uint64_t s = 0x1234ABCDULL;
  long* next = malloc(sizeof(long) * N);
  double* stream = malloc(sizeof(double) * STREAM_N);
  int* perm = malloc(sizeof(int) * N);
  for (int i = 0; i < N; ++i)
    perm[i] = i;
  for (int i = N - 1; i > 0; --i) {             /* Fisher-Yates */
    int j = (int)(rng_next(&s) % (unsigned)(i + 1));
    int t = perm[i];
    perm[i] = perm[j];
    perm[j] = t;
  }
  for (int i = 0; i < N - 1; ++i)
    next[perm[i]] = perm[i + 1];
  next[perm[N - 1]] = perm[0];
  for (size_t i = 0; i < STREAM_N; ++i)
    stream[i] = 1.0;

  long p = perm[0];
  double acc = 0.0;
  __champsim_start_trace();
  for (int rep = 0; rep < 2; ++rep) {
    size_t si = 0;
    for (int i = 0; i < N; ++i) {
      p = next[p];                              /* chase: dependent, random */
      acc += stream[si];                        /* stream: unit stride */
      si = (si + 1) % STREAM_N;
    }
  }
  __champsim_stop_trace();
  printf("chase_mix p %ld acc %f\n", p, acc);
  return 0;
}
