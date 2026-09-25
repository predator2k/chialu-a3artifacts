---
handle: saporito_2020
citation: A. Saporito, M. Recktenwald, C. Jacobi, G. Koch, et al., "Design of the IBM z15 Microprocessor", IBM Journal of Research and Development, vol. 64, no. 5/6, pp. 7:1-7:18, 2020.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [fp32, fp64, hexadecimal_fp_short, hexadecimal_fp_long, decimal, uint256, uint512, uint521]
authority: survey
pages_read: 17 / 17
---

## summary
The paper describes shipped IBM z15 arithmetic enhancements, including redesigned decimal multiply/divide, chunked binary-decimal conversion, a six-stage multi-precision SIMD floating-point unit, and a dedicated ECC modulo-arithmetic engine (pp.4-9). The reported improvements include average 3x decimal multiply/divide acceleration, doubled FP32 SIMD capacity, and up to or potentially more than 3x ECC sign/verify acceleration (pp.4-9).

## families
### commercial_decimal_fpu  (role: instantiates)
mechanism: Specialized decimal-arithmetic subunits reside within the two floating-point/SIMD vector pipelines. Hardware decimal multiply/divide takes 20-150 processor cycles depending on precision and data. The z15 redesign changes the algorithms and logic without requiring recompilation (p.4).
choices:
  implementation: hardware_dfu   # p.4
new_choices:
  none
slots:
  none
parameters: variable latency of 20-150 processor cycles; exact datapath width, multiplier family, and divider family are UNKNOWN   # p.4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| decimal multiply/divide latency | 20-150 | processor cycles | UNKNOWN / IBM z15 / 2020 | none | depends on precision and data values | p.4 |
| decimal multiply/divide acceleration, average | 3 | x | UNKNOWN / IBM z15 / 2020 | prior implementation | existing code without recompilation | p.4 |
| decimal multiply/divide acceleration, maximum | 7.5 | x | UNKNOWN / IBM z15 / 2020 | prior implementation | existing code without recompilation | p.4 |
errors_and_checks: none
conditions: The redesign applies transparently to existing decimal multiply/divide code, while the paper does not disclose the underlying arithmetic algorithms (p.4).
evidence: Decimal number operation enhancements, p.4.

### binary_decimal_conversion  (role: instantiates)
mechanism: Conversion between binary and decimal numbers processes a chunk of digits iteratively. The z15 increases the chunk size, but the paper does not state the recurrence or shift-and-adjust logic (p.4).
choices:
  direction: both   # p.4
  structure: iterative_chunked [outside domain]   # p.4
new_choices:
  none
slots:
  none
parameters: chunk size UNKNOWN; digits per step UNKNOWN   # p.4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| conversion instruction performance improvement | 18%-52% | UNKNOWN | UNKNOWN / IBM z15 / 2020 | predecessor implementation | binary-decimal conversion with increased chunk size | p.4 |
errors_and_checks: none
conditions: The improvement is transparent to existing software, but the paper does not identify the conversion algorithm (p.4).
evidence: Decimal number operation enhancements, p.4.

## new_families
### multi_precision_simd_fp_pipeline  (domain: fp: floating-point execution units, closest: multi_precision_simd_fma, why_not: The paper describes an entire SIMD floating-point pipeline and does not state that its operations use an FMA organization.)
mechanism: Two floating-point/SIMD vector pipelines contain specialized subunits with different pipeline depths and a multi-stage forwarding network. The redesigned binary floating-point subunit has six pipeline stages and performs two FP64 or four FP32 operations per cycle. Its FP64 multiplier is reused for two concurrent FP32 multiplications. A hardware load balancer dynamically assigns long-running divide/square-root instructions between pipelines according to circuit utilization (pp.4-5).
choices:
  pipeline_count: Int[1..4:1] = 2   # p.4
  pipeline_stages: Int[1..10:1] = 6   # p.5
  lane_throughput: {2xfp64, 4xfp32}   # p.5
  fp64_multiplier_reused_for_fp32: Bool = true   # p.5
  long_operation_load_balancing: Bool = true   # p.5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| core design frequency | 5.2 | GHz | UNKNOWN / IBM z15 / 2020 | none | pipelines use operation-dependent depths | p.4 |
| pipeline stages | 6 | pipeline stages | UNKNOWN / IBM z15 / 2020 | 7 pipeline stages on z14 | redesigned binary floating-point unit | p.5 |
| dependent-operation latency reduction | 12% | UNKNOWN | UNKNOWN / IBM z15 / 2020 | z14 | binary floating-point operations | p.5 |
| FP32 SIMD capacity | 2 | x | UNKNOWN / IBM z15 / 2020 | z14 | redesigned binary floating-point unit | pp.4-5 |
| FP64 throughput per subunit | 2 | operations per cycle | UNKNOWN / IBM z15 / 2020 | none | FP64 operation mode | p.5 |
| FP32 throughput per subunit | 4 | operations per cycle | UNKNOWN / IBM z15 / 2020 | none | FP32 operation mode | p.5 |
| issue-stall-cycle reduction | approximately 15% | UNKNOWN | UNKNOWN / IBM z15 / 2020 | asymmetric pipeline assignment | divide-intensive workloads using dynamic load balancing | p.5 |
evidence: SIMD and floating point improvements, pp.4-5.

### ecc_modulo_arithmetic_engine  (domain: redundant: residue number systems, closest: rns_channel_arithmetic, why_not: The unit operates on full-width binary operands for selected prime moduli, with no independent residue channels stated.)
mechanism: A dedicated non-speculative execution unit accelerates ECC through a firmware-hidden microarchitectural instruction set. The unit has 16 521-bit registers, transfers cache data in 64-bit chunks, and supports binary add/subtract/multiply plus modular add/subtract/additive inverse/halve/multiply/multiplicative inverse. Firmware selects fixed P256/P384/P521/X255-19/X448 moduli or a custom modulus, although modular multiply cannot use the custom modulus (pp.8-9).
choices:
  binary_width: {256, 512, 521}   # p.9
  modulus_profile: {P256, P384, P521, X255-19, X448, custom}   # p.9
  register_count: Int[1..32:1] = 16   # p.9
  register_width_bits: Int[1..1024:1] = 521   # p.9
  cache_transfer_width_bits: Int[1..128:1] = 64   # p.9
  speculative_execution: Bool = false   # p.8
  custom_modulus_multiply: Bool = false   # p.9
results:
| metric | value | unit | technology / device | baseline | condition | page |
| ECC sign/verify acceleration | up to and potentially more than 3 | x | UNKNOWN / IBM z15 / 2020 | software implementation | KDSA firmware/hardware implementation | p.8 |
| unit area | about 0.3 | square milli-meters | UNKNOWN / IBM z15 / 2020 | none | physical area at processor-core edge | p.8 |
| key-exchange speed-up | 18.6 | UNKNOWN | UNKNOWN / IBM z15 / 2020 | software on the same hardware | NIST 256 | p.9 |
| key-exchange speed-up | 26.6 | UNKNOWN | UNKNOWN / IBM z15 / 2020 | software on the same hardware | NIST 384 | p.9 |
| key-exchange speed-up | 39.1 | UNKNOWN | UNKNOWN / IBM z15 / 2020 | software on the same hardware | NIST 521 | p.9 |
| sign speed-up | 38.2 | UNKNOWN | UNKNOWN / IBM z15 / 2020 | software on the same hardware | NIST 256 | p.9 |
| sign speed-up | 49.6 | UNKNOWN | UNKNOWN / IBM z15 / 2020 | software on the same hardware | NIST 384 | p.9 |
| sign speed-up | 81.1 | UNKNOWN | UNKNOWN / IBM z15 / 2020 | software on the same hardware | NIST 521 | p.9 |
| verify speed-up | 10.9 | UNKNOWN | UNKNOWN / IBM z15 / 2020 | software on the same hardware | NIST 256 | p.9 |
| verify speed-up | 13.2 | UNKNOWN | UNKNOWN / IBM z15 / 2020 | software on the same hardware | NIST 384 | p.9 |
| verify speed-up | 19.2 | UNKNOWN | UNKNOWN / IBM z15 / 2020 | software on the same hardware | NIST 521 | p.9 |
evidence: Modulo Arithmetic Unit, Figure 6 and Tables 1-2, pp.8-9.

## space_gaps
* `commercial_decimal_fpu` lacks a value for an iterative chunked binary-decimal conversion structure, which the paper distinguishes from decimal multiply/divide hardware (p.4).
* The vocabulary lacks dynamic utilization-based assignment of variable-latency divide/square-root operations across duplicated floating-point pipelines (p.5).

## open_questions
* Table 1 labels its values as speed-up but prints no unit, while the prose reports acceleration of up to and potentially more than 3x; the merge pass must not interpret the table values as ratios or percentages without another source (pp.8-9).
* The paper does not disclose the decimal multiply/divide algorithms, binary floating-point adder/FMA topology, or modulo-multiply reduction algorithm (pp.4-9).
