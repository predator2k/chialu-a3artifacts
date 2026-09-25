/* Blocked single-precision GEMM.  Patterns:
     - A[i*K+k] : unit stride within a tile, large jump between tiles
     - B[k*N+j] : long stride (row length), the classic stride-prefetcher case
     - C[i*N+j] : reuse, resident in L1 for the whole tile
   Distinct enough that the best single prefetcher for one is wrong for
   the others. */
#include <stdio.h>
#include <stdlib.h>
#include "champsim_markers.h"

#define M 512
#define K 512
#define N 512
#define TI 32
#define TJ 32
#define TK 32

int main(void)
{
  float* A = malloc(sizeof(float) * M * K);
  float* B = malloc(sizeof(float) * K * N);
  float* C = calloc((size_t)M * N, sizeof(float));
  for (int i = 0; i < M * K; ++i)
    A[i] = 1.0f;
  for (int i = 0; i < K * N; ++i)
    B[i] = 1.0f;
  __champsim_start_trace();
  for (int i0 = 0; i0 < M; i0 += TI)
    for (int j0 = 0; j0 < N; j0 += TJ)
      for (int k0 = 0; k0 < K; k0 += TK)
        for (int i = i0; i < i0 + TI; ++i)
          for (int k = k0; k < k0 + TK; ++k) {
            float a = A[i * K + k];
            for (int j = j0; j < j0 + TJ; ++j)
              C[i * N + j] += a * B[k * N + j];
          }
  __champsim_stop_trace();
  printf("gemm C0 %f\n", C[0]);
  return 0;
}
