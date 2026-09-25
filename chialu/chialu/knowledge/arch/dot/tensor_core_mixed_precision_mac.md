# tensor_core_mixed_precision_mac

A processing element that computes a short fixed-width dot product
plus an addend, D = A x B + C, as one operation: k narrow products
(binary16, bfloat16, TensorFloat-32, int8, or fp8) are formed exactly
at full precision in the first pipeline stage, the k products and C
are aligned to the largest-magnitude operand, summed in a wide
fixed-point accumulator that keeps two to three bits of carry headroom
and does not normalize between additions, truncated toward zero at
each addition, and normalized and rounded once into the binary32 or
binary16 result. Volta groups sixteen 4-element units into one 4x4x4
matrix multiply-accumulate per cycle; TPUs tile the units into a
128x128 systolic array.

Dot width sets density against exposure to the non-IEEE sum. Four
terms per unit on Volta and Turing became eight on A100 for the
low-precision modes, which doubled dense binary16 throughput per SM,
while the A100 binary64 mode drops to two terms, rounds to nearest
even, and normalizes after every addition. A wider dot aligns more
products to one exponent and pays fewer normalizations per output,
and the 128x128 array carries that to 32,768 operations per cycle
with the left operand streaming across a preloaded right operand.

Partial-sum rounding and alignment target define the accuracy
contract. Products are exact, but each output can absorb four rounding
errors; the V100 accumulator carries about 27 significand bits against
24 for binary32 with no alignment guard digits, so one cancellation
case shows relative error 1 and final-only normalization makes the
output non-monotonic in its inputs, while T4 and A100 add one bottom
bit. Error grows with matrix size and input magnitude, which limits
direct use in precision-sensitive HPC; the working contract is
application-level, model accuracy matching binary32 training when
partials accumulate in binary32 and loss scaling with binary32 master
weights is applied. Subnormals are supported in the tested modes.

The family is feed-forward with a four-stage pipe and a minimum
initiation interval of two cycles per warp instruction, and a
16x16x16 warp operation takes 54 to 64 cycles on Volta. It wins on
dense GEMM, about 6x binary32 and 3x binary16 CUDA-core GEMM on V100,
and the surrounding organization adds more: 32-thread granularity cuts
shared-memory loads, structured sparsity doubles throughput, and
unit-local accumulator registers reduce data movement. It loses where
per-operation IEEE semantics are required or the reduction is latency
bound.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/dot.py`: PEs of `dot_width_per_pe` products aligned to their largest exponent (or added pairwise in sequence), each partial sum rounded to d by the library rounder (`partial_sum_rounding` rne or truncate) and read back by the library unpacker before the accumulate with c; the module comment says the fused contract's single rounding is not met, and that the pairwise sequential form with one product per PE is the sequential contract; an integer mode keeps its partial sums exact). `python3 -m chialu.targets.rtl.families.dot --fab <format> --fc <format> --fd <format> --n <elements> --family <family> --pins k=v,...` emits it for a rewrite.

## design choices

### alignment_target

| member | what it selects |
| --- | --- |
| `largest_exponent` | each processing element aligns its products to the largest exponent among them. |
| `pairwise_sequential` | the products are aligned pairwise in sequence, which with one product per element is the sequential contract. |

## references

choquette_2018 -> J. Choquette, O. Giroux, D. Foley, "Volta: Performance and Programmability", IEEE Micro, vol. 38, no. 2, pp. 42-52, 2018.
fasi_2021 -> M. Fasi, N. J. Higham, M. Mikaitis, S. Pranesh, "Numerical Behavior of NVIDIA Tensor Cores", PeerJ Computer Science, 7:e330, 2021
micikevicius_2018 -> P. Micikevicius, S. Narang, J. Alben, G. Diamos, E. Elsen, et al., "Mixed Precision Training", ICLR, 2018
raihan_2019 -> M. A. Raihan, N. Goli, T. M. Aamodt, "Modeling Deep Learning Accelerator Enabled GPUs", IEEE ISPASS, pp. 79-92, 2019
markidis_2018 -> S. Markidis, S. W. D. Chien, E. Laure, I. B. Peng, J. S. Vetter, "NVIDIA Tensor Core Programmability, Performance & Precision", IEEE IPDPSW, pp. 522-531, 2018
choquette_2021 -> J. Choquette, W. Gandhi, O. Giroux, N. Stam, R. Krashinsky, "NVIDIA A100 Tensor Core GPU: Performance and Innovation", IEEE Micro, vol. 41, no. 2, pp. 29-35, 2021
choquette_2023 -> J. Choquette, "NVIDIA Hopper H100 GPU: Scaling Performance", IEEE Micro, vol. 43, no. 3, pp. 9-17, 2023.
norrie_2021 -> T. Norrie, N. Patil, D. H. Yoon, G. Kurian, S. Li, J. Laudon, C. Young, N. Jouppi, D. Patterson, "The Design Process for Google's Training Chips: TPUv2 and TPUv3", IEEE Micro, vol. 41, no. 2, pp. 56-63, 2021.
