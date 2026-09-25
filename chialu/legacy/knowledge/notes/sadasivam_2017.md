---
handle: sadasivam_2017
citation: S. K. Sadasivam, B. W. Thompto, R. Kalla, W. J. Starke, "IBM Power9 Processor Architecture", IEEE Micro, vol. 37, no. 2, pp. 40-51, 2017.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU, VEC_DOT_ACC]
formats: [int64, int128, fp32, fp64, fp128, decimal_fp]
authority: landmark
pages_read: 40-51 / 12
---

## summary
The document describes the 14-nm Power9 processor and its modular execution-slice architecture for shared fixed-point/floating-point/scalar/SIMD execution (pp.40, 43-46). Two 64-bit slices form a 128-bit super-slice, which supports two scalar operations or one vector operation and contains fully pipelined double-precision multiply-add resources (pp.43-46). A separate QP/DFU block supplies quad-precision and decimal floating-point execution (pp.44-45).

## families
### replicated_lanes  (role: extends)
mechanism: A symmetric 64-bit computational slice shares execution resources across fixed-point, floating-point, scalar, and SIMD operations. Two slices combine into a 128-bit super-slice; two super-slices form an SMT4 core, while four form an SMT8 core. One super-slice handles either two scalar operations or one vector operation (pp.43-46).
choices:
new_choices:
  slice_composition: two 64-bit slices per 128-bit super-slice — specifies how narrow execution slices combine for wider operations   # pp.43-44
  datatype_sharing: fixed-point/floating-point/scalar/SIMD — specifies the data types served by the symmetric computational resources   # p.43
slots: none
parameters: slice width 64-bit; super-slice width 128-bit; two super-slices per SMT4 core; four super-slices per SMT8 core; up to four scalar 64-bit or two vector 128-bit operations per cycle per SMT4 core   # pp.43-46
results:
| metric | value | unit | technology / device | baseline | condition | page |
| scalar issue capability | four | scalar 64-bit operations per cycle | 14-nm FinFET / IBM Power9 (2017) | none | SMT4 core; operations include computational/load/store operations | p.45 |
| vector issue capability | two | vector 128-bit operations per cycle | 14-nm FinFET / IBM Power9 (2017) | none | SMT4 core | p.45 |
| simple fixed-point throughput | four | ALU operations per cycle | 14-nm FinFET / IBM Power9 (2017) | none | Power9 SMT4 VSU pipes | p.45 |
| 128-bit permute throughput | two | operations per cycle | 14-nm FinFET / IBM Power9 (2017) | none | Power9 SMT4 VSU pipes | p.45 |
| 128-bit quadword fixed-point throughput | two | operations per cycle | 14-nm FinFET / IBM Power9 (2017) | none | Power9 SMT4 VSU pipes | p.45 |
errors_and_checks: none
conditions: Two slices are occupied by each 128-bit operation, while each 64-bit slice can independently handle scalar operations of different instruction types (pp.43, 45). The SMT8 core doubles the SMT4 execution resources and can power-gate half of those resources when only one thread is active (pp.45-46).
evidence: Execution Slice Microarchitecture, pp.43-44; Figures 4-6, pp.44-45; Core Computational Capabilities, pp.44-46.

### multi_precision_simd_fma  (role: instantiates)
mechanism: Each of the four SMT4 slices contains a double-precision floating-point unit optimized for fully pipelined multiply-add. The Vector Scalar Extension uses a 128-bit super-slice for two-way double-precision or four-way single-precision execution per cycle (pp.45-46).
choices:
  lane_split: 2x64, 4x32 [outside domain]   # pp.45-46
new_choices: none
slots:
  align: UNKNOWN   # pp.45-46
  lza: UNKNOWN   # pp.45-46
  cpa: UNKNOWN   # pp.45-46
  round: UNKNOWN   # pp.45-46
  multiplier: UNKNOWN   # pp.45-46
parameters: four double-precision floating-point units per SMT4 core; one unit per 64-bit slice; 128-bit super-slice; fully pipelined; two-way fp64 or four-way fp32 operations per cycle per super-slice   # pp.45-46
results:
| metric | value | unit | technology / device | baseline | condition | page |
| floating-point/fixed-point multiply throughput | four | operations per cycle | 14-nm FinFET / IBM Power9 (2017) | none | Power9 SMT4 VSU pipes; includes complex 64-bit fixed-point operations | p.45 |
| fp64 SIMD throughput | two-way | operations per cycle | 14-nm FinFET / IBM Power9 (2017) | none | one 128-bit super-slice | pp.45-46 |
| fp32 SIMD throughput | four-way | operations per cycle | 14-nm FinFET / IBM Power9 (2017) | none | one 128-bit super-slice | pp.45-46 |
| floating-point arithmetic performance improvement | well above one and half | times | 14-nm FinFET / IBM Power9 (2017) | Power8 | scale-out configuration; similar bandwidth constraints; constant frequency | p.49 |
| floating-point fetch-to-retirement latency reduction | eight | cycles | 14-nm FinFET / IBM Power9 (2017) | Power8 | core pipeline comparison | p.42 |
errors_and_checks: none
conditions: The document identifies double-precision multiply-add as the optimized function, but it does not state the rounding contract or whether fp32/fp128 execution uses the same fused datapath (pp.45-46).
evidence: Figure 5 and VSU capability list, pp.44-45; floating-point-unit description, pp.45-46; Figure 10 and Performance, p.49.

### commercial_decimal_fpu  (role: instantiates)
mechanism: The SMT4 core contains a QP/DFU execution block. The VSU pipes support one decimal floating-point operation, while Power ISA 3.0 adds native IEEE-compliant 128-bit quadword floating-point arithmetic (pp.44-45, 48).
choices:
  implementation: hardware_dfu   # pp.44-45
new_choices: none
slots:
  significand_adder: UNKNOWN   # pp.44-45
  multiplier: UNKNOWN   # pp.44-45
  divider: UNKNOWN   # pp.44-46
parameters: one decimal floating-point operation; native 128-bit quadword floating-point arithmetic; QP/DFU block   # pp.44-45, 48
results:
| metric | value | unit | technology / device | baseline | condition | page |
| decimal floating-point throughput | one | operation | 14-nm FinFET / IBM Power9 (2017) | none | listed SMT4 VSU-pipe capability; cycle qualification is not stated | p.45 |
errors_and_checks: none
conditions: The document does not identify the decimal format, datapath width, arithmetic algorithms, latency, or whether binary and decimal arithmetic share internal datapath components (pp.44-45).
evidence: Figure 5, p.44; VSU capability list, p.45; Power ISA Support for Emerging Markets, p.48.

## new_families
none

## space_gaps
* `replicated_lanes` lacks a slice-composition choice for pairing two 64-bit slices into a 128-bit super-slice (pp.43-44).
* `replicated_lanes` lacks a choice for sharing one symmetric execution engine across fixed-point/floating-point/scalar/SIMD data types (p.43).
* `multi_precision_simd_fma.lane_split` lacks the reported 2x64 and 4x32 lane organizations of a 128-bit super-slice (pp.45-46).

## open_questions
* The document does not disclose the adder, multiplier, reduction, normalization, or rounding microarchitecture inside the floating-point multiply-add units.
* The document states that each floating-point unit performs divide and square root, but it does not identify the recurrence, radix, latency, throughput, or rounding method (p.46).
* The document does not identify the decimal floating-point format, DFU datapath width, or internal decimal adder/multiplier/divider families (pp.44-45).
