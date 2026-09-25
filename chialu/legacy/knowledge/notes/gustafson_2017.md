---
handle: gustafson_2017
citation: J. L. Gustafson, I. T. Yonemoto, "Beating Floating Point at its Own Game: Posit Arithmetic", Supercomputing Frontiers and Innovations, vol. 4, no. 2, pp. 71-86, 2017
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU, VEC_DOT_ACC]
formats: [fp8, fp16, fp32, fp64, fp128, fp256, posit8_0, posit8_1, posit16_1, posit32_3, posit64_4, posit128_7, posit256_10]
authority: landmark
pages_read: 71-86 / 16
---

## summary
The paper proposes the fixed-size posit format as a replacement for IEEE floating point and compares its range/closure/accuracy with floats (pp.71-86). The posit environment mandates correctly rounded arithmetic and exact fused operations based on a fixed-size integer accumulator (pp.77-78). The paper also proposes an 8-bit posit bit transformation that approximates a sigmoid function (p.75).

## families
### posit_adder_multiplier  (role: proposes)
mechanism: An n-bit posit contains a sign bit, a variable-length regime, up to es exponent bits, and any remaining fraction bits. A negative encoding is two’s-complemented before the regime/exponent/fraction are decoded. The regime run length supplies useed^k, the unsigned exponent supplies 2^e, and the fraction supplies 1.f, which produces tapered precision without subnormals (pp.73-75).
choices:
  es_bits: 0, 1, 2, 3, 4 [outside domain], 7 [outside domain], 10 [outside domain]   # pp.73, 76
  internal_representation: twos_complement   # p.73
new_choices:
  exception_encoding: all-zero 0 and sign-bit-only ±∞ — the two bit patterns outside positional decoding   # pp.73-75
slots:
  sig_datapath: UNKNOWN
parameters: n = 8, 16, 32, 64, 128, 256 bits; evaluated pairs include 8-bit posit es = 1 and 8-bit float with 4 exponent/3 fraction bits   # pp.76, 78
results:
| metric | value | unit | technology / device | baseline | condition | page |
| posit16 positive finite range | 4 × 10−9 to 3 × 10^8 | — | UNKNOWN / 2017 | fp16: 6 × 10−8 to 7 × 10^4 | es = 1 | p.76 |
| posit32 positive finite range | 6 × 10−73 to 2 × 10^72 | — | UNKNOWN / 2017 | fp32: 1 × 10−45 to 3 × 10^38 | es = 3 | p.76 |
| posit64 positive finite range | 2 × 10−299 to 4 × 10^298 | — | UNKNOWN / 2017 | fp64: 5 × 10−324 to 2 × 10^308 | es = 4 | p.76 |
| 8-bit reciprocal exact cases | 18.8% | inputs | UNKNOWN / 2017 | float: 13.3% | posit es = 1 | p.79 |
| 8-bit addition exact cases | 25.0% | input pairs | UNKNOWN / 2017 | float: 18.5% | exhaustive 256 by 256 tables | p.82 |
| 8-bit addition NaN cases | 0.00153% | input pairs | UNKNOWN / 2017 | float: 10.6% | exhaustive 256 by 256 tables | p.82 |
| 8-bit multiplication exact cases | 18.0% | input pairs | UNKNOWN / 2017 | float: 22.3% | exhaustive 256 by 256 tables | p.83 |
| 8-bit multiplication NaN cases | 0.00305% | input pairs | UNKNOWN / 2017 | float: 10.7% | exhaustive 256 by 256 tables | p.83 |
| expression accuracy | 6 | significant digits | UNKNOWN / 2017 | fp32: 3 correct digits | 32-bit posit es = 3 | p.84 |
| unstable quadratic root accuracy | 6 | correct decimals | UNKNOWN / 2017 | fp32: 4 correct decimals | a = 3, b = 100, c = 2 | p.85 |
errors_and_checks: Supported posit arithmetic operations must be correctly rounded; the 8-bit operation comparisons exhaustively test all 256² input pairs (pp.77-78).
conditions: Regime length must be determined before the exponent/fraction can be decoded, although extra register bits can retain size information (p.77). Posits have no subnormals/negative zero/separate signed infinities/NaN bit patterns (pp.76-77). The paper reports no implemented circuit, technology node, area, delay, or power measurement (pp.71-86).
evidence: §2.1, Table 3, §3, Figs. 8-16, §4.5.

### posit_quire_mac  (role: proposes)
mechanism: Fused operations use exact integer arithmetic in a fixed-size scratch area and round only after the final operation. Fused multiply-add/add-multiply/multiply-multiply-subtract/sum/dot product are treated as subsets of the fused dot product. The accumulator must represent products down to minpos² and sums up to maxpos²/minpos² = useed^(4n−8) (pp.77-78).
choices:
  quire_width_bits: 128, 1024 [outside domain], 4096 [outside domain], 65536 [outside domain], 1048576 [outside domain]   # p.78
  op_set: fused_ops_general   # p.77
new_choices:
  implementation_location: hardware_or_software — small accumulators can be register-sized, while larger ones use an L1/L2-cache-sized scratch area   # p.78
slots:
  none
parameters: posit n/accumulator bits = 16/128, 32/1024, 64/4096, 128/65536, 256/1048576; one terminal rounding   # pp.77-78
results:
| metric | value | unit | technology / device | baseline | condition | page |
| exact accumulator size | 128 | bits | UNKNOWN / 2017 | none | n = 16 | p.78 |
| exact accumulator size | 1024 | bits | UNKNOWN / 2017 | none | n = 32 | p.78 |
| exact accumulator size | 4096 | bits | UNKNOWN / 2017 | none | n = 64 | p.78 |
| exact accumulator size | 65536 | bits | UNKNOWN / 2017 | none | n = 128 | p.78 |
| exact accumulator size | 1048576 | bits | UNKNOWN / 2017 | none | n = 256 | p.78 |
| LINPACK solution | {1, 1, . . . , 1} | vector entries | UNKNOWN / 2017 | fp64: none of 100 entries exactly 1 | n = 100; 32-bit posits; fused-dot residual and iterative correction | pp.85-86 |
errors_and_checks: Products and accumulation are exact integers, and rounding is deferred until the fused operation completes (p.77).
conditions: A complete posit environment must provide the fused operations through software or hardware (p.78). Large accumulator sizes require a scratch area comparable with L1/L2 cache rather than register-sized storage (p.78).
evidence: §3, Table 4, §4.6.

### integer_compare_on_bits  (role: instantiates)
mechanism: Posit equality is bitwise identity, and posit less-than uses the same ordering as signed integers. Existing signed-integer comparison instructions can therefore compare posit encodings (pp.76-77).
choices:
new_choices:
  format: posit — comparison operates directly on the posit encoding   # pp.76-77
slots:
  none
parameters: n-bit posit operands   # pp.73, 76-77
results:
| metric | value | unit | technology / device | baseline | condition | page |
errors_and_checks: Posits have no NaN encodings or negative zero that require exceptional equality handling (pp.76-77).
conditions: Signed-integer wraparound still requires care (p.77).
evidence: §2.4.

### sigmoid_tanh_pwl  (role: proposes)
mechanism: The 8-bit posit sigmoid approximation flips the first bit of the posit encoding and shifts the result right by two positions with zero fill. The resulting encoded function closely resembles 1/(1 + e^−x) and has the correct slope at the y-axis intersection (p.75).
choices:
  approximation: bit_level_mapping   # p.75
new_choices:
  bit_transform: flip_first_bit_then_logical_right_shift_2 — representation-level sigmoid evaluation   # p.75
slots:
  none
parameters: posit8, es = 0; one bit flip; two-bit right shift   # p.75
results:
| metric | value | unit | technology / device | baseline | condition | page |
| conventional sigmoid latency | over a hundred | clock cycles | UNKNOWN / 2017 | math-library exp(x) plus division | common 1/(1 + e^−x) evaluation | p.75 |
errors_and_checks: No maximum/mean approximation error or training-quality result is reported (p.75).
conditions: The transformation is specific to the 8-bit posit representation with es = 0 (p.75).
evidence: §2.2, Fig. 6.

### correct_rounding_strategy  (role: analyzes)
mechanism: A posit environment requires every supported arithmetic operation to be correctly rounded. The paper states that interpolation tables can avoid the Table-Maker’s Dilemma associated with polynomial approximations, but it supplies no table construction or precision bound (p.77).
choices:
  strategy: interpolation_tables [outside domain]   # p.77
new_choices:
  none
slots:
  none
parameters: UNKNOWN
results:
| metric | value | unit | technology / device | baseline | condition | page |
errors_and_checks: The required contract is correct rounding for all supported operations (p.77).
conditions: Covert extra exponent/fraction bits that change results across systems are forbidden (p.77).
evidence: §3.

### posit_ieee_interop  (role: proposes)
mechanism: Fixed-size posits are presented as a direct replacement for IEEE floats rather than an interval or variable-size format. The replacement retains rounding after inexact operations while changing encoding, exception handling, tapered precision, and fused-operation requirements (pp.71-72, 77).
choices:
  interop_style: isa_posit_replaces_float   # pp.71, 86
  quire_present: true   # pp.77-78
new_choices:
  none
slots:
  none
parameters: replacements discussed from 8 through 256 bits; 32-bit posit substitution for fp64 is emphasized   # pp.75-76, 84-86
results:
| metric | value | unit | technology / device | baseline | condition | page |
| projected calculation speed | 2 − 4× | — | UNKNOWN / 2017 | current float-based systems | smaller posit operands; no implementation measurement | p.86 |
errors_and_checks: Bitwise-identical results across systems depend on mandated correct rounding and prohibition of covert extra precision (pp.71, 77, 86).
conditions: The paper provides no boundary converter or unified dual-format datapath (pp.71-86).
evidence: Abstract, §3, §5.

## new_families
none

## space_gaps
* `posit_adder_multiplier.es_bits` excludes the es = 4, 7, and 10 formats reported in Table 3 (p.76).
* `posit_quire_mac.quire_width_bits` excludes the 1024/4096/65536/1048576-bit accumulator sizes in Table 4 (p.78).
* `correct_rounding_strategy.strategy` lacks the paper’s interpolation-table strategy (p.77).
* `posit_quire_mac` lacks a choice for register/software/cache-backed scratch-area implementation (p.78).

## open_questions
* The paper names the sign-bit-only exception value “±∞” while also stating that posits lack separate +∞ and −∞ values, so the merge must preserve this paper’s terminology (pp.73, 76).
* The paper does not specify actual adder/multiplier/reduction/rounding circuitry for a posit processing unit (pp.71-86).
* The projected circuitry/power/speed advantages have no synthesized or fabricated implementation baseline in this document (pp.71, 86).
