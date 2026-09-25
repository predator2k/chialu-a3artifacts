# Task

The loop nest around the CacheFlex SPM GEMM microkernel for the paper
workloads the run names, at one SVE vector length. The microkernel, the scratchpad copy
and the A packing are the artifact's and fixed; the search rewrites the
loop nest (`gemm_v3`) and declares its K tile `kc` and M tile `mc`. The
seed is the artifact's own nest, lifted out of the ROI of
`kernels/gemm/cacheflex/src/v3_fused.cpp`, at the KC and MC its
reference run for this workload and vector length pinned. A
candidate compiles through the artifact's SPM encoder, runs under QEMU
against a naive reference on a reduced shape and at the workload shape
for a checksum, then runs one cell on the artifact's gem5 fork, whose
checksum must reproduce the mock's. The goal is the cells' cycles
against the seed's, one shape at a time and their geometric mean.

The nest is called with M, K and N, so it may branch on the shape it is
given: a tail that one workload has and another does not, a K that fits
one tile against a K that does not. Specialising per shape is allowed
and is what a tuned kernel library does; every shape the run names is
measured, and a candidate is admitted only where all of them are
correct.
