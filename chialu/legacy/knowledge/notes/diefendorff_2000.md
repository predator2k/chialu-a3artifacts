---
handle: diefendorff_2000
citation: K. Diefendorff, P. K. Dubey, R. Hochsprung, H. Scales, "AltiVec Extension to PowerPC Accelerates Media Processing", IEEE Micro, vol. 20, no. 2, pp. 85-95, 2000
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU, VEC_DOT_ACC]
formats: [int8, uint8, int16, uint16, int32, uint32, fp32]
authority: landmark
pages_read: 11 / 11
---

## summary
The document describes AltiVec, a 128-bit SIMD extension with dedicated vector registers, packed integer/fp32 arithmetic, saturation, multiply-sum, fused multiply-add, arbitrary byte permutation, and double-vector shifting. Cycle-accurate MPC 7400 simulations report average speedups of 6.5 for integer kernels and 5.1 for floating-point kernels over the same processor without AltiVec. # p.86

## families
### replicated_lanes  (role: proposes)
mechanism: AltiVec uses a dedicated 32-register vector file and fixed 128-bit vectors containing four, eight, or 16 elements. Corresponding elements execute in parallel. A first-class `vperm` instruction uses a full 32 × 16 bytewise crossbar to select each destination byte from two source vectors. # pp.86,88
choices:
  register_file: dedicated_simd   # p.86
  rearrangement: full_permute_network   # p.88
new_choices:
  permute_network: 32 × 16 bytewise crossbar — implementation of arbitrary two-source byte permutation   # p.88
  issue_pairing: one ALU-class plus one permute-class instruction per cycle — superscalar execution pairing   # pp.88,93
slots: none
parameters: 128-bit vectors; 32 vector registers; 16 × 8-bit, 8 × 16-bit, or 4 × 32-bit/fp32 lanes; 162 instructions; throughput at least one instruction per cycle and typically two per cycle   # pp.86-88
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average integer-kernel speedup | 6.5 | ratio | UNKNOWN / MPC 7400 (year: 2000) | same PowerPC processor without AltiVec | more than 40 media kernels; cycle-accurate simulation | p.86 |
| average floating-point-kernel speedup | 5.1 | ratio | UNKNOWN / MPC 7400 (year: 2000) | same PowerPC processor without AltiVec | more than 40 media kernels; cycle-accurate simulation | p.86 |
| motion estimation | 90.7/macroblock; 16 | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | 176 × 144, 8-bit | p.94 |
| quantization | 96.8; 12.5 | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | 8 × 8 DCT output block, 16-bit → 8-bit | p.94 |
| 8 × 8 inverse discrete cosine transform | 101.7/block; 12.3 | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | 8 × 8 image block, 16-bit | p.94 |
| inverse fast Fourier transform | 1,700; 3.5 | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | 128 complex taps, FP | p.94 |
| windowing | 834/kernel; 4.9 | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | 256 elements, FP → 16-bit | p.94 |
| matrix-matrix multiplication | 36.5; 6.2 | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | two 4 × 4 → one 4 × 4, FP | p.94 |
| matrix-vector multiplication | 5.6/vector; Not available (n/a) | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | 4 × 4 arrays times 4-element vectors, FP | p.94 |
| transform/perspective/projection | 28,800; 2.5 | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | 800 vertices, 400 normals, FP | p.94 |
| buffer accumulation | 5.3/pixel; 17.5 | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | [RGBA] (8-bit), FP scale factors | p.94 |
| Bezier curve drawing | 2.48/point; 6.3 | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | four 16-bit → 64 16-bit points | p.94 |
| 3 × 3 median filter | 1.23/pixel; n/a | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | 128 × 128 pixels | p.94 |
| separable convolution | 1.94/pixel; n/a | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | 512 × 512 pixels | p.94 |
| bilinear interpolation | 26.7/pixel; 6.4 | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | 128 × 128 pixels | p.94 |
| color-space conversion | 2.25/pixel; n/a | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | 4,800 pixels | p.94 |
| L-filter | 5.23/pixel; n/a | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | 128 × 128 pixels | p.94 |
| 13-tap real finite impulse response | 4.25/output; 9.4 | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | scalar PPC FP | AltiVec 16-bit | p.94 |
| linear prediction, Levinson-Durbin | 388; 3.2 | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | 12 LP coefficients, FP | p.94 |
| linear prediction, Schur recursion | 238; 7.1 | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | 12 LP coefficients, FP | p.94 |
| bit-packing in 64-QAM demodulation | 35; 10.5 | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | 32 16-bit → 384 bits | p.94 |
| CRC-32 | 1.312/byte; n/a | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | 128-bit → 32-bit | p.94 |
| autocorrelation | 676; 30.7 | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | 256 8-bit samples → 16 32-bit coefficients | p.94 |
| GSM module 4.2.11 | 1,034; 12.5 | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | signed 16-bit, 60,600 samples | p.94 |
| 2 × 2 forward Haar transform | 0.375/pixel; n/a | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | eight 2 × 2-pixel blocks → 16-bit frequency bands | p.94 |
| sorting using Batcher sort | 76; 10.0 | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | 16 8-bit elements | p.94 |
| (2,1,3) convolution encoder | 19; n/a | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | two sets of 125 bits → 256 bits | p.94 |
| gamma correction, ITU-R 709 | 0.625/pixel; n/a | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | 8 bit → 8 bit | p.94 |
| arbitrary permutation | 20; n/a | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | 128-bit | p.94 |
| associative search | 13; 5.8 | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | two 32-entry tables, 16-bit keys/tags → 16-bit tag | p.94 |
| Gaussian elimination | 9,824; 1.42 | cycles; speedup ratio | UNKNOWN / MPC 7400 (year: 2000) | optimized scalar code on same processor | FP, 16 variables | p.94 |
errors_and_checks: none
conditions: SIMD parallelism is 16 for 8-bit, eight for 16-bit, and four for 32-bit/fp32 data. # p.86 The design omits 32-bit integer multiply as a silicon-area concession. # p.89
evidence: architectural characteristics and performance summary on pp.86-88; `vperm` and Figure 1 on p.88; MPC 7400 characteristics and Table 3 on pp.93-94

### funnel  (role: instantiates)
mechanism: AltiVec double-vector shift instructions form shifted windows from two source vectors. `vsldi` constructs successive byte-offset vectors from an aligned register pair and is identified as a funnel shift in the median-filter example. # pp.88,91
choices:
  input_forming: two_register_pair   # p.91
new_choices: none
slots: none
parameters: 128-bit sources and destination; byte offsets shown from 1 through 4   # p.91
results:
| metric | value | unit | technology / device | baseline | condition | page |
| median filter | 1.2 | cycles/output pixel | UNKNOWN / typical AltiVec implementation (year: 2000) | scalar processors, unquantified | more sophisticated 5 × 5 algorithm | p.91 |
errors_and_checks: none
conditions: Long linear unaligned-load sequences approach two instructions per vector because load and permute usually issue simultaneously. # p.90
evidence: double-vector shift description on p.88; Figure 2 and median-filter discussion on p.91

### integer_mac  (role: instantiates)
mechanism: `multiply-sum` multiplies corresponding byte or halfword elements, groups the products into four 32-bit partial sums, adds four values from a third vector, and saturates each partial sum. `sum-across` reduces the four partial sums to one 32-bit scalar result. # p.89
choices:
  array_style: simd_packed_dot   # p.89
  accumulator_width_bits: 32   # p.89
  saturating_accumulate: true   # p.89
new_choices: none
slots:
  mul: UNKNOWN   # p.89
  reduction: UNKNOWN   # p.89
parameters: byte and halfword element forms; four 32-bit partial sums; full-precision products; 16-pixel-per-cycle motion-search throughput   # p.89
results: none reported independently from the application results above.
errors_and_checks: Products are full precision, and individual partial sums saturate on overflow/underflow. # p.89
conditions: Byte multiply-add is absent; byte-oriented algorithms use multiply-sum or expand data to 16 bits. # p.89
evidence: Figure 1b and vector dot-product/multiply-accumulate sections on pp.88-89

### classic_fma  (role: instantiates)
mechanism: AltiVec provides fp32 vector multiply-add with three source operands and one destination. Intermediate calculations are described as infinitely precise, with one rounding after the add operation. # pp.89-90
choices: none
new_choices: none
slots:
  align: UNKNOWN
  lza: UNKNOWN
  cpa: UNKNOWN
  round: UNKNOWN
  multiplier: UNKNOWN
parameters: four fp32 lanes per 128-bit vector; fully pipelined; latency UNKNOWN   # pp.86,89-90
results: none reported independently.
errors_and_checks: The fused multiply-add performs a single rounding after addition. # p.90
conditions: SIMD floating-point throughput is similar to SIMD integer throughput when pipeline latency can be covered. # p.90
evidence: multiply-accumulate and division/square-root discussions on pp.89-90

### newton_raphson  (role: instantiates)
mechanism: Division and square root use Newton-Raphson refinement of reciprocal or reciprocal-square-root estimates with fused multiply-add operations instead of dedicated division hardware. The single-rounding FMA supports rapid convergence to an IEEE-754-accurate reciprocal. # p.90
choices: none
new_choices: none
slots:
  seed: UNKNOWN   # p.90
  iter_mult: UNKNOWN   # p.90
  final_round: UNKNOWN   # p.90
parameters: iterations UNKNOWN; guard bits UNKNOWN; fp32 vectors   # pp.86,90
results: none reported independently.
errors_and_checks: The refined reciprocal is described as IEEE-754-accurate; no numerical error bound is given. # p.90
conditions: The sequence has no hidden state between cycles, so instructions can be rescheduled and division can be fully pipelined. # p.90
evidence: reciprocal/reciprocal-square-root instruction summary on p.87; division and square-root discussion on p.90

### shift_round_convert  (role: instantiates)
mechanism: One vector instruction converts and scales four signed or unsigned 32-bit fixed-point words to four fp32 values, or performs the reverse conversion. A separate instruction rounds fp32 values to integral values. # p.89
choices:
  rounding_modes: four_ieee_modes [outside domain]   # p.89
new_choices: none
slots:
  shift_unit: UNKNOWN
  round: UNKNOWN
  lz: UNKNOWN
parameters: 4 × int32/uint32 or 4 × fp32 per instruction; scale included in conversion   # p.89
results: none reported independently.
errors_and_checks: none stated
conditions: All four IEEE-754 rounding modes are supported for rounding floating-point values to integral values. # p.89
evidence: conversion discussion on pp.89-90

### saturating_clamp  (role: instantiates)
mechanism: Packed add/subtract, multiply-add, multiply-sum, sum-across, partial-sum, and pack operations include saturating variants. Multiply-sum clamps each partial sum to the maximum on overflow and minimum on underflow. # pp.87,89
choices: none
new_choices: none
slots: none
parameters: packed 8-bit/16-bit/32-bit integer operations; signed/unsigned availability depends on instruction class   # p.87
results: none reported independently.
errors_and_checks: Saturation replaces overflowed/underflowed results with the destination format’s maximum/minimum value. # p.89
conditions: The paper specifies architectural saturation behavior but does not disclose detection or clamp circuitry. # pp.87,89
evidence: Table 2 on p.87; vector dot-product and multiply-add descriptions on p.89

## new_families
### vector_select_merge  (domain: shift: sub-word SIMD, closest: vector_lane_masking, why_not: `vsel` writes a selected result under a general-register predicate rather than controlling whether lanes commit)
mechanism: Vector comparisons create a predicate vector in any vector register. `vsel` selects corresponding bits from two source vectors under that predicate, which supports branch avoidance, conditional movement, predicated-execution simulation, and merging subfields that do not follow element boundaries. # p.90
choices: predicate_storage: {general_vector_register}; select_granularity: {bit, element}
results: none reported independently.
evidence: conditionals section on p.90

## space_gaps
* `replicated_lanes` lacks choices for the 32 × 16 bytewise crossbar and ALU/permute issue pairing fixed by this implementation. # pp.88,93
* `shift_round_convert.rounding_modes` lacks the four-mode IEEE-754-1985 value stated by the document. # p.89

## open_questions
* The paper does not disclose the adder, multiplier, reduction-tree, saturation-detection, or rounding circuit topologies. # pp.87-93
* The stated 1-cycle simple-operation and 3-to-4-cycle compound-operation latencies do not identify every instruction individually. # p.93
* The reciprocal/reciprocal-square-root estimate implementation, Newton-Raphson iteration count, guard precision, and final-rounding proof are unspecified. # pp.87,90
