# Task

Four GEMM kernels in C, one per shape class (small, large, tall, wide),
for a core with a 32 KB first-level data cache and a 2 MB 16-way L2.
Every hardware variable is fixed; the search is over the kernel text
alone. The declaration block states the plan: a BUFFER line with the
bytes the plan keeps resident, and one TILE line per kernel with its
block sizes. The goal is the geometric mean of the simulated cycles
over the training shapes, measured under cachegrind with the stated
cost model; a held-out shape set is reported for the front.

This run file is the cachegrind cousin of the CacheFlex task
(`examples/cacheflex_kernel`), which converts the L2 into a
software-managed scratchpad under an ISA extension and measures on
gem5. Here the L2 stays a cache and the kernels are plain C.
