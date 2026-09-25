#ifndef RNG_H
#define RNG_H
#include <stdint.h>
/* splitmix64: deterministic across runs and machines, so a trace is reproducible. */
static inline uint64_t rng_next(uint64_t* s)
{
  uint64_t z = (*s += 0x9E3779B97F4A7C15ULL);
  z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
  z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
  return z ^ (z >> 31);
}
#endif
