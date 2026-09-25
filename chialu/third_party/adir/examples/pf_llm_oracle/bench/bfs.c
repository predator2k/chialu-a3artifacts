/* CSR breadth-first search.  Three load patterns in one inner loop:
     - row[v], row[v+1]   : short stride over the offset array
     - col[e]             : streaming over a slice of the edge array
     - dist[u]            : scattered, dependent on the value col[e] just returned
   A single global prefetcher choice cannot serve all three, which is the
   headroom a per-PC hint is supposed to exploit. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "rng.h"
#include "champsim_markers.h"

#define NV (1 << 21)          /* 2 M vertices */
#define DEG 16                /* average degree */
#define NE ((size_t)NV * DEG)

static int* row;
static int* col;
static int* dist;
static int* frontier;
static int* next_f;

static void build(void)
{
  uint64_t s = 0xC0FFEE123ULL;
  row = malloc(sizeof(int) * (NV + 1));
  col = malloc(sizeof(int) * NE);
  dist = malloc(sizeof(int) * NV);
  frontier = malloc(sizeof(int) * NV);
  next_f = malloc(sizeof(int) * NV);
  for (int v = 0; v <= NV; ++v)
    row[v] = v * DEG;
  for (size_t e = 0; e < NE; ++e)
    col[e] = (int)(rng_next(&s) % NV);
}

int main(void)
{
  build();
  for (int v = 0; v < NV; ++v)
    dist[v] = -1;
  int nf = 0;
  uint64_t s = 42;
  for (int i = 0; i < 4096; ++i) {              /* a wide starting frontier */
    int v = (int)(rng_next(&s) % NV);
    dist[v] = 0;
    frontier[nf++] = v;
  }
  long long visited = 0;
  __champsim_start_trace();
  for (int level = 1; level <= 3 && nf > 0; ++level) {
    int nn = 0;
    for (int i = 0; i < nf; ++i) {
      int v = frontier[i];
      int b = row[v], e = row[v + 1];
      for (int j = b; j < e; ++j) {
        int u = col[j];
        if (dist[u] < 0) {
          dist[u] = level;
          next_f[nn++] = u;
          ++visited;
        }
      }
    }
    memcpy(frontier, next_f, sizeof(int) * nn);
    nf = nn;
  }
  __champsim_stop_trace();
  printf("bfs visited %lld\n", visited);
  return 0;
}
