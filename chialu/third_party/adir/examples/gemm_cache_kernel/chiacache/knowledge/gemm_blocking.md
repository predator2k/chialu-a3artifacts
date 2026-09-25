# Blocking a GEMM for a cache hierarchy

C = A x B with A M x K, B K x N, row-major. The naive i-j-k loop reads
a column of B per output element: K strided loads per (i, j), so B is
re-read M times from wherever it lives.

## What the simulation charges

The cost model is one cycle per instruction, 5 per first-level data
miss (L1: `l1.size_kb`, 8-way, 64-byte lines) and 60 per last-level
miss (L2: `l2.size_kb`, `l2.ways`, 64-byte lines). Instruction count
matters as much as misses: a kernel that halves the misses and doubles
the loop overhead gains nothing.

## Moves that pay

* Loop order i-k-j: the inner loop walks a row of B and a row of C
  contiguously; A is read once per (i, k).
* Blocking: choose mb x kb of A and kb x nb of B so mb*kb + kb*nb +
  mb*nb floats stay in the cache the block is meant for (L1 for the
  inner blocks, L2 for the outer). Declare the working set in the
  BUFFER line and the block sizes in the TILE lines.
* Packing: copy a kb x nb panel of B into a contiguous buffer once,
  then stream every row block of A through it; the pack costs kb*nb
  loads and stores per panel and removes the stride in the inner loop.
* Register blocking: compute a 4 x 4 (or 2 x 8) block of C in scalar
  accumulators so each loaded element of A and B feeds several
  multiply-adds; this cuts instructions, which the model charges one
  each.
* Shape classes: a tall kernel (M >> N) keeps the whole B resident and
  streams A; a wide one keeps A's row block and streams B panels; the
  small one fits entirely in L2 and is instruction-bound.

## What does not

* Inline assembly, intrinsics and OpenMP are not admitted (plain_c).
* Tiles whose working set exceeds the declared BUFFER bytes fail the
  declaration check; buffers above `l2.size_kb` fail it too.
* A change to the harness or the reference is outside the mutable
  regions and rejected.
