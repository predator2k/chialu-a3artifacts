---
handle: codrescu_2014
citation: L. Codrescu, W. Anderson, S. Venkumanhanti, M. Zeng, E. Plondke, C. Koob, et al., "Hexagon DSP: An Architecture Optimized for Mobile Multimedia and Communications", IEEE Micro, vol. 34, no. 2, pp. 34-43, 2014.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [int8, int16, int32, int64, frac16, frac32, complex16, fp32]
authority: landmark
pages_read: 34-43 / 10
---

## summary
The document describes the shipped Hexagon V5 DSP, whose two 64-bit SIMD execution units support integer/fractional arithmetic, complex multiplication, and single-precision floating-point FMA (p.36). The document reports execution-unit capabilities and whole-processor results but does not disclose the arithmetic circuits inside the multipliers, adders, saturators, or FMA (pp.36-42).

## families
### classic_fma  (role: instantiates)
mechanism: Each 64-bit SIMD execution unit supports one single-precision IEEE-compatible floating-point fused multiply-add operation. The article identifies the operation as an FMA but does not describe its alignment, multiplication, carry-propagation, normalization, or rounding structure (p.36).
choices:
new_choices:
  none
slots:
  none
parameters: fp32; one FMA operation supported by each of two identical 64-bit SIMD execution units; pipeline depth, latency, and initiation interval UNKNOWN (p.36)
results:
none
errors_and_checks: Single-precision floating point is described as IEEE-compatible; no rounding-error bound, exception behavior, fault model, or checking coverage is reported (p.36).
conditions: The FMA shares each multifunction SIMD execution unit with multiply, shift, ALU, and bit-manipulation instructions; permitted simultaneous issue combinations are not stated (p.36).
evidence: Data-processing-instruction description and Figure 3 (p.36).

## new_families
### multiwidth_multifunction_simd_execution_unit  (domain: shift: sub-word SIMD, closest: replicated_lanes, why_not: replicated_lanes does not express a multifunction unit whose multiply concurrency changes with operand width)
mechanism: Hexagon V5 contains two identical 64-bit SIMD execution units. Each unit supports multiply, shift, ALU, and bit-manipulation instructions over packed integer/fractional data. Each unit can support four 16 × 16 multiplies, two 32 × 16 multiplies, or one 32 × 32 multiply, complex multiply, or fp32 FMA. Thirty-two 32-bit general registers, also accessible as aligned 64-bit pairs, hold scalar/vector/accumulator data (p.36).
choices:
  datapath_width_bits: {64}
  execution_unit_count: {2}
  operation_set: {multiply_shift_alu_bitmanip}
  multiply_shape: {4x16x16, 2x32x16, 1x32x32, complex16, fp32_fma}
  register_file_integration: {shared_scalar_vector_accumulator}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum clock frequency | 800 | MHz | 28 nm Hexagon V5 aDSP / 2012 | none | Snapdragon 800 implementation; whole DSP rather than isolated execution unit | p.40 |
| total system power | -32 | percent | UNKNOWN / UNKNOWN | ARM/Neon CPU execution | Feature-detection algorithm offloaded through RPC; battery measurement includes system power and RPC overhead | p.41 |
evidence: Figures 2-4 and accompanying execution-unit description (pp.35-37); Snapdragon 800 implementation data (p.40); Figure 10 and accompanying text (p.41).

## space_gaps
* The vocabulary lacks a multiply-shape/concurrency choice for a multifunction SIMD execution unit supporting four 16 × 16, two 32 × 16, or one 32 × 32 multiplication per unit (p.36).
* The vocabulary lacks a shared scalar/vector/accumulator register-file value for SIMD execution units (p.36).

## open_questions
* The document does not state whether the two execution units can issue two fp32 FMAs in the same cycle.
* The document does not state whether the multiply shapes share a fractured datapath or use separate hardware.
* The document does not identify the FMA multiplier, CPA, alignment, normalization, or rounding implementations.
* The document does not identify the device/node/year used for the Figure 10 power comparison.
