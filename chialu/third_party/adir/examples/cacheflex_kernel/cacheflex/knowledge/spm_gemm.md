# The CacheFlex SPM GEMM

The L2 is converted into a software-managed scratchpad (SPM). A K-tile
of B (KC rows by NT columns, fp16) is copied into the SPM once per (K
tile, M block, N tile) with `pack_B_tile_to_spm` (the SPMCP
instructions); the microkernel `spm_gemm_fused_8x3VL` then reads B from
the SPM with `spm.ld1qd` loads while streaming a packed block of A (MC
rows, 8 per sub-block) and writing or accumulating C directly.

## What the loop nest decides

* `kc`: rows of B per SPM tile. Larger KC means fewer SPMCP copies and
  fewer C read-modify-write passes (C is accumulated once per K tile),
  bounded by the SPM capacity: 1024 at VL 4, 512 at VL 8, 341 at VL 16
  (the binary refuses more).
* `mc`: rows of A packed per M block. Larger MC amortizes each SPMCP
  copy over more rows; the packed A block (MC x KC fp16) must stay in
  the L1 and L2 that remain.
* The loop order. The seed is the paper's driver verbatim -- K outer, M
  blocks, then N tiles with one SPMCP per tile -- so each B tile is
  copied ceil(M/MC) times per K tile. An N-outer order copies each B tile once but re-packs A per N
  tile; a prepacked A trades packing time for footprint.
* The pack of A (`pack_A_fp16_8row`) interleaves 8 rows; its cost is
  MC x KC per block and is inside the ROI.

## The shapes and what distinguishes them

At VL 16 the microkernel's N tile is NT = 384 halfwords, so a workload's
N decides whether the last N tile is partial, and its K against KC
decides whether C is written once or accumulated over several K tiles.

| workload | M | K | N | N tiles | tail | K tiles at KC 341 |
| --- | --- | --- | --- | --- | --- | --- |
| W7 | 784 | 256 | 1024 | 3 | 256 | 1 |
| W4 | 512 | 768 | 768 | 2 | none | 3 |
| W6 | 2048 | 64 | 2048 | 6 | 128 | 1 |
| W3 | 256 | 2048 | 2048 | 6 | 128 | 6 |

A change that holds only for one of these columns is a change for that
column: the nest receives M, K and N and may take a different path for
each. A change that assumes one K tile is wrong wherever K exceeds KC,
because the fused kernel accumulates into C from the second K tile on,
and a column computed twice is then added twice.

## What is fixed

The microkernel, the SPMCP copy and the A pack are the artifact's;
the mutable region is the loop nest alone. The harness fills A and B
deterministically, compares against a naive reference and prints the
checksum. Two things check a candidate, and they check different
things. The reference compare under QEMU runs twice, on a reduced
shape and on the workload shape at the KC and MC the block declares;
it is what catches a nest that skips, double-counts or mis-tails a
tile. The checksum then ties the gem5 cell to that QEMU run within a
relative 1e-6 -- not bit for bit, because the mock builds the cache
microkernel and the cell the SPM one, and the two accumulate in a
different order -- so it catches an SPM path that diverges from the
checked one, not a wrong nest. The cell's cycles are the ROI at
2.5 GHz on the paper's out-of-order core (5-wide, 128 ROB, 64 KB L1,
512 KB L2 as SPM, 4 MB L3).
