/* Sparse matrix-vector product, CSR.  Patterns:
     - ptr[i]   : unit stride
     - idx[k]   : streaming
     - val[k]   : streaming, a second stream in a different array
     - x[idx[k]]: indirect gather, unpredictable from its own history
   The two streams want an aggressive degree; the gather wants none, and
   pollutes the streams' prefetcher if it is allowed to train it. */
#include <stdio.h>
#include <stdlib.h>
#include "rng.h"
#include "champsim_markers.h"

#define NR (1 << 20)
#define NNZ_PER_ROW 24
#define NNZ ((size_t)NR * NNZ_PER_ROW)

int main(void)
{
  uint64_t s = 0xBEEF5EEDULL;
  int* ptr = malloc(sizeof(int) * (NR + 1));
  int* idx = malloc(sizeof(int) * NNZ);
  double* val = malloc(sizeof(double) * NNZ);
  double* x = malloc(sizeof(double) * NR);
  double* y = malloc(sizeof(double) * NR);
  for (int i = 0; i <= NR; ++i)
    ptr[i] = i * NNZ_PER_ROW;
  for (size_t k = 0; k < NNZ; ++k) {
    idx[k] = (int)(rng_next(&s) % NR);
    val[k] = 1.0;
  }
  for (int i = 0; i < NR; ++i) {
    x[i] = 1.0;
    y[i] = 0.0;
  }
  __champsim_start_trace();
  for (int rep = 0; rep < 3; ++rep) {
    for (int i = 0; i < NR; ++i) {
      double acc = 0.0;
      int b = ptr[i], e = ptr[i + 1];
      for (int k = b; k < e; ++k)
        acc += val[k] * x[idx[k]];
      y[i] = acc;
    }
  }
  __champsim_stop_trace();
  printf("spmv y0 %f\n", y[0]);
  return 0;
}
