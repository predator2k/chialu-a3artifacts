---
handle: markidis_2018
citation: S. Markidis, S. W. D. Chien, E. Laure, I. B. Peng, J. S. Vetter, "NVIDIA Tensor Core Programmability, Performance & Precision", IEEE IPDPSW, pp. 522-531, 2018
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp16, fp32]
authority: incremental
pages_read: 12 / 12
---

## summary
The paper characterizes NVIDIA Volta Tensor Cores as 4×4 matrix-multiply-and-accumulate units with FP16 inputs and FP32 accumulation, and measures GEMM performance and precision on a Tesla V100 (p.1–3). The paper also proposes residual-based precision refinement using two or four Tensor Core GEMMs (p.6–7).

## families
### tensor_core_mixed_precision_mac  (role: analyzes)
mechanism: Each Tensor Core performs one 4×4 matrix-multiply-and-accumulate per GPU clock cycle. The matrix operands use FP16, multiplication uses mixed-precision behavior described inconsistently as half-precision multiplication or a single-precision product, and accumulation uses FP32. One Tensor Core performs 64 FMA operations per cycle; an FMA uses one rounding rather than separate multiply/add roundings (p.1–3).
choices:
  dot_width_per_pe: 4   # p.1–3
new_choices:
  matrix_tile_shape: 4x4 — hardware matrix-multiply-and-accumulate tile dimensions   # p.1–3
  operand_accumulator_formats: fp16_inputs_fp32_accumulator — arithmetic formats used by the matrix operation   # p.1–3
  output_format: fp16_or_fp32 — supported result formats   # p.2
slots:
  none
parameters: 4×4 hardware MMA; 64 FMA operations/cycle/Tensor Core; 640 Tensor Cores; 40,960 FMA operations/cycle; 80 SMs; 1.38 GHz measured boost clock; 112.7 Tflops/s test-system theoretical peak; WMMA exposes 16×16 MMA to one 32-thread warp   # p.2–4, p.6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| peak GEMM performance | 83 | Tflops/s | UNKNOWN / NVIDIA Tesla V100; 2018 | 112.7 Tflops/s theoretical peak | cuBLAS, N = 8,192, 1.38 GHz | p.7 |
| theoretical-peak utilization | 74 | % | UNKNOWN / NVIDIA Tesla V100; 2018 | 112.7 Tflops/s theoretical peak | cuBLAS mixed-precision GEMM | p.7 |
| GEMM speedup | 6× | × | UNKNOWN / NVIDIA Tesla V100; 2018 | full single-precision cuBLAS GEMM on CUDA cores | large matrix GEMM | p.7 |
| GEMM speedup | 3× | × | UNKNOWN / NVIDIA Tesla V100; 2018 | full half-precision cuBLAS GEMM on CUDA cores | large matrix GEMM | p.7 |
| batched GEMM peak | 4 | Tflops/s | UNKNOWN / NVIDIA Tesla V100; 2018 | cuBLAS batched sgemm on CUDA cores | 262,144 independent 16×16 matrix multiplications | p.7–8 |
| batched GEMM speedup | 2.5×–12× | × | UNKNOWN / NVIDIA Tesla V100; 2018 | cuBLAS batched sgemm on CUDA cores | speedup varies with batch size | p.8, p.10 |
| shared-memory implementation speedup | 5× | × | UNKNOWN / NVIDIA Tesla V100; 2018 | sgemm on CUDA cores | N = 8,192; result not plotted | p.7 |
errors_and_checks: The evaluation defines e = Chalf − Csingle and uses ||e||Max = max(|ei,j|) as the maximum per-entry error bound. Inputs are random FP32 values converted to FP16; no fault-detection mechanism is reported (p.7).
conditions: The naive WMMA implementation provides no improvement over sgemm and is slower than hgemm, while shared-memory use reduces memory traffic and raises performance (p.7). Error increases with matrix size and input magnitude, which limits direct use in precision-sensitive HPC applications (p.5, p.8–10). Batched cuBLAS sgemm exhausts available V100 memory above 131,072 tested matrices (p.8).
evidence: §III; Fig. 3; §IV; Listing 1; §VI; §VII.A; Figs. 6–7.

## new_families
### residual_refined_gemm  (domain: dot-product / FMA / MAC, closest: tensor_core_mixed_precision_mac, why_not: the mechanism composes multiple GEMM invocations and residual matrices rather than changing the Tensor Core MAC datapath)
mechanism: Precision refinement represents each FP32 operand matrix as its FP16 rounding plus an FP16 residual. Refining A computes RA Bhalf + Ahalf Bhalf using two Tensor Core GEMMs. Refining both operands computes RA RB + Ahalf RB + RA Bhalf + Ahalf Bhalf using four Tensor Core GEMMs. The method trades additional computation and storage for lower input-conversion error (p.6–7).
choices:
  refined_operands: {A_only, A_and_B}
  gemm_count: {2, 4}
  residual_storage: {RA, RA_and_RB}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum error | 0.24 | ||e||Max | UNKNOWN / NVIDIA Tesla V100; 2018 | 8.32 without refinement | A/B values random between ±16, N = 4,096, both operands refined | p.9 |
| error decrease | 35× | × | UNKNOWN / NVIDIA Tesla V100; 2018 | no refinement | A/B values random between ±16, N = 4,096, both operands refined | p.9 |
| error decrease | 30 | % | UNKNOWN / NVIDIA Tesla V100; 2018 | no refinement | N = 8,192, A-only refinement | p.9 |
| computational cost | 2.25× | × | UNKNOWN / NVIDIA Tesla V100; 2018 | one unrefined Tensor Core GEMM | N = 8,192, A-only refinement | p.9 |
| error decrease | 10× | × | UNKNOWN / NVIDIA Tesla V100; 2018 | no refinement | N = 8,192, both operands refined | p.9 |
| computational cost | 5× | × | UNKNOWN / NVIDIA Tesla V100; 2018 | one unrefined Tensor Core GEMM | N = 8,192, both operands refined | p.9 |
| execution-time reduction | 25 | % | UNKNOWN / NVIDIA Tesla V100; 2018 | full single-precision GEMM without Tensor Cores | N = 8,192, both operands refined | p.9 |
evidence: §V, Eqs. 1–3; §VI; Fig. 5; §VII.B; Figs. 8–9.

## space_gaps
* tensor_core_mixed_precision_mac lacks choices for matrix tile shape and explicit operand/accumulator/output formats (p.1–3).
* The dot-product vocabulary lacks residual decomposition across multiple low-precision GEMMs as an accuracy-recovery mechanism (p.6–7).

## open_questions
* The text describes multiplication as half precision, while Fig. 3 labels the product as single precision; the internal product precision is therefore ambiguous (p.1–3).
* The paper does not specify partial-sum rounding, alignment policy, subnormal behavior, multiplier structure, or reduction structure.
* The paper does not report the Tesla V100 fabrication node.
