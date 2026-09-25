---
handle: norrie_2021
citation: T. Norrie, N. Patil, D. H. Yoon, G. Kurian, S. Li, J. Laudon, C. Young, N. Jouppi, D. Patterson, "The Design Process for Google's Training Chips: TPUv2 and TPUv3", IEEE Micro, vol. 41, no. 2, pp. 56-63, 2021.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU, VEC_DOT_ACC]
formats: [bf16, fp16, fp32]
authority: survey
pages_read: 56-63 / 8
---

## summary
The article describes TPUv2’s programmable scalar/vector datapath and its bfloat16-by-fp32 systolic matrix unit, then explains the TPUv3 extensions. TPUv2 uses 128 vector lanes with eight sublanes each and a 128 x 128 matrix multiply unit. TPUv3 doubles the matrix units and raises their clock frequency while retaining 16 nm technology.

## families
### replicated_lanes  (role: instantiates)
mechanism: The vector computation unit contains 128 lanes, and each lane contains eight sublanes. Each sublane has a dual-issue 32-bit ALU connected to a 32-deep register file. Push slots send vectors to the matrix units, and a result FIFO receives returned vectors for later movement into vector memory. Separate units perform matrix transposes, row reductions, and column permutations. (pp.59-60)
choices:
  register_file: dedicated_simd   # p.59
new_choices:
  none
slots:
  none
parameters: 128 lanes; 8 sublanes per lane; dual-issue 32-bit ALU per sublane; 32-deep register file; eight sets of 128-wide vectors per clock cycle   # p.59
results:
| metric | value | unit | technology / device | baseline | condition | page |
| vector throughput | eight sets of 128-wide vectors | per clock cycle | 16 nm TPUv2; 2017 | UNKNOWN | full vector computation unit | pp.56,59,61 |
errors_and_checks: UNKNOWN
conditions: Sublanes increase the vector-to-matrix compute ratio, which is useful for batch normalization. The result FIFO relaxes scheduling constraints for long-latency matrix operations and shortens register lifetimes.   # p.59
evidence: Figure 3(b) and “Vector Computation Unit,” p.59; matrix-transformation-unit description, p.60

### tensor_core_mixed_precision_mac  (role: instantiates)
mechanism: The matrix multiply unit is a 128 x 128 systolic array of multipliers and adders. A left-hand-side matrix streams across a preloaded right-hand-side matrix, and the streaming result matrix enters the vector unit’s result FIFO. The right-hand-side matrix can be transposed during loading. TPUv3 doubles the number of matrix multiply units. (pp.59,61)
choices:
  none
new_choices:
  array_style: systolic_array — the spatial organization of multiplier/adder processing elements   # p.59
  operand_flow: lhs_stream_rhs_preloaded — the left matrix streams across a stationary preloaded right matrix   # p.59
  rhs_load_transpose: optional — the right matrix may be transposed while loading   # p.59
slots:
  none
parameters: 128 x 128 systolic array; 32,768 operations per cycle per TPUv2 matrix multiply unit; TPUv3 has twice the TPUv2 matrix-unit count; 700 MHz TPUv2 clock; 940 MHz TPUv3 clock   # pp.59,61
results:
| metric | value | unit | technology / device | baseline | condition | page |
| matrix-unit throughput | 32,768 | operations per cycle | 16 nm TPUv2; 2017 | UNKNOWN | one 128 x 128 systolic matrix multiply unit | pp.56,59,61 |
| maximum FLOPS/second | 2× | relative | 16 nm TPUv3; UNKNOWN | TPUv2 | matrix multiply units doubled | p.61 |
| clock frequency | 940 | MHz | 16 nm TPUv3; UNKNOWN | TPUv2, 700 MHz | pipeline tuning | p.61 |
| peak computation gain | 2.7× | relative | 16 nm TPUv3; UNKNOWN | TPUv2 | doubled matrix units plus clock increase | p.62 |
| geometric-mean application performance gain | 1.8× | relative | 16 nm TPUv3; UNKNOWN | TPUv2 | MLPerf 0.6 benchmarks and Google production applications; chip-level result | p.62 |
errors_and_checks: UNKNOWN
conditions: The systolic structure provides high computational density and supplies most FLOPS/s without being the largest chip-area contributor. TPUv3’s memory bandwidth/ICI bandwidth/clock improvements are each 1.3× while peak computation rises 2.7×, so application performance rises 1.8× rather than matching the peak-compute gain.   # pp.59,62
evidence: “Matrix Computation Units,” p.59; Figure 4, p.60; “TPUv3,” p.61; “Performance Synopsis,” p.62

### bf16_fma_datapath  (role: instantiates)
mechanism: The matrix units perform multiplications with bfloat16 operands and accumulate in full 32-bit floating point. Bfloat16 retains the float32 exponent range with fewer mantissa bits. The article does not specify the multiplier structure, partial-sum rounding behavior, subnormal handling, or accumulation recurrence. (p.59)
choices:
  none
new_choices:
  op_shape: matrix_dot_accumulate [outside domain] — bfloat16 matrix products accumulate into fp32 results inside a systolic array   # p.59
slots:
  none
parameters: 16-bit bfloat16 multiplication operands; 32-bit floating-point accumulation   # p.59
results:
| metric | value | unit | technology / device | baseline | condition | page |
| energy advantage | ≈1.5× | relative | 7 nm estimate; UNKNOWN | IEEE 16-bit float | estimated bfloat16 add/multiply energy | p.59 |
| add energy | 0.11 | pJ | 7 nm estimate; UNKNOWN | IEEE 16-bit float, 0.16 pJ | bfloat16 addition | p.59 |
| multiply energy | 0.21 | pJ | 7 nm estimate; UNKNOWN | IEEE 16-bit float, 0.31 pJ | bfloat16 multiplication | p.59 |
errors_and_checks: UNKNOWN
conditions: Bfloat16 works for almost all ML training workloads described by the authors and avoids the loss scaling needed for fp16. The reported energy values are estimates for 7 nm rather than measurements from the 16 nm TPUv2/v3 chips.   # p.59
evidence: Bfloat16 numerics and energy comparison in “Matrix Computation Units,” p.59

## new_families
none

## space_gaps
* `tensor_core_mixed_precision_mac` lacks choices for systolic-array dimensions, operand flow, optional load-time transpose, and matrix-unit replication.   # pp.59,61
* `replicated_lanes` lacks choices for lane count, sublane count, issue width, and per-sublane register-file depth.   # p.59
* `bf16_fma_datapath.op_shape` lacks a matrix-dot-accumulate value for systolic training accelerators.   # p.59

## open_questions
* The document does not specify the matrix unit’s multiplier/reduction families, fp32 accumulator organization, intermediate rounding, or subnormal behavior.
* The document does not identify the operations or number formats supported by the dual-issue 32-bit scalar/vector ALUs.
* The document does not define how the 128 x 128 array dimensions map to `tensor_core_mixed_precision_mac.dot_width_per_pe`.
