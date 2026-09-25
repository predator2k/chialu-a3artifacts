---
handle: lynch_1995
citation: T. Lynch, A. Ahmed, M. Schulte, T. Callaway, R. Tisdale, "The K5 Transcendental Functions", Proc. 12th IEEE Symposium on Computer Arithmetic, pp. 163-170, 1995.
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [binary_fp_24bit_mantissa, binary_fp_32bit_mantissa, binary_fp_53bit_mantissa, binary_fp_64bit_mantissa]
authority: incremental
pages_read: 8 / 8
---

## summary
The K5 implements x86 transcendental instructions as ROM-resident RISC sequences that reuse an existing pipelined floating-point unit (p.163). The algorithms combine argument reduction, table lookup, Horner polynomial evaluation, and multiprecision arithmetic to keep maximum error below 1 ulp without widening the datapath (pp.163-165).

## families
### lut_plus_poly  (role: instantiates)
mechanism: The transcendental routines perform argument reduction, evaluate a polynomial over the reduced range with Horner's rule, and form the final result with table values (pp.164-165). For 2^x-1, u = Rnd(r·x)/r and v = x-u; a Taylor polynomial produces h = 2^v-1, a table supplies g = 2^u-1, and the result is g·h+g+h (pp.164-165).
choices:
  degree: 9 [outside domain]   # p.165
  basis: taylor   # p.165
  breakpoint_placement: uniform   # p.165
new_choices:
  coefficient_generation: on_the_fly — coefficients are generated during evaluation to reduce constant storage   # p.165
slots:
  range_reducer: range_reduction [method=table_augmented, reduction_type=additive]   # pp.164-165
  evaluator: horner   # p.165
parameters: sin(x), cos(x), tan(x), arctan(x), 2^x, log(x), log(x+1), and 2^x-1; r=16; 33 table entries; 9 Taylor terms; at least 88 bits for three-digit multiprecision values   # pp.164-165
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum error | <1 | ulp | UNKNOWN / AMD K5 / 1995 | exact function | transcendental routines | p.163 |
| maximum relative approximation error | roughly 2^-72 | relative | UNKNOWN / AMD K5 / 1995 | arbitrary-precision reference | Level 2 F2XM1 implementation | p.169 |
| final error | <3ε/4 | relative | UNKNOWN / AMD K5 / 1995 | exact 2^x-1 | fixed-precision F2XM1 analysis, ε=2^-63 | p.169 |
errors_and_checks: The required maximum error is less than 1 ulp; verification uses approximation-error plots, step-by-step roundoff bounds, full-chip simulation with generated tolerance checks, and random tests against an arbitrary-precision reference (pp.163, 166-169).
conditions: The method reuses a 66-bit adder, a 32×32-bit multiplier, comparators, and a rounder already present in the K5 floating-point unit (p.163). Multiprecision operations compensate for the absence of guard bits beyond the largest architecture-visible type (pp.163-164). Taylor evaluation is selected because coefficients can be generated on-the-fly under limited constant-memory capacity (p.165).
evidence: §2, §2.1, §2.2, §4; Figures 2-5 (pp.164-169)

### range_reduction  (role: instantiates)
mechanism: The detailed 2^x-1 reduction selects u from 33 uniformly spaced values using u = Rnd(16x)/16 and computes v=x-u, which confines v to [-1/32,1/32] (p.165). Trigonometric routines instead subtract integer multiples of π/2 represented with up to about 256 bits to reduce inputs from [-2^63,2^63] to (-π/4,π/4) (p.164).
choices:
  method: table_augmented   # p.165
  reduction_type: additive   # pp.164-165
new_choices: none
slots: none
parameters: r=16; 33 table entries; v∈[-1/32,1/32]; trigonometric reduction constant up to about 256 bits   # pp.164-165
results: none
errors_and_checks: The F2XM1 error analysis treats the operations producing u and v as exact; the analysis then bounds representation/rounding errors introduced by ln(2) and subsequent arithmetic (p.169).
conditions: Multiprecision arithmetic is required when reduction constants exceed the hardware significand width (p.164). The document does not give corresponding table sizes or reduced intervals for every supported function (pp.164-165).
evidence: §2, §2.2, §4.4 (pp.164-165, 169)

### horner  (role: instantiates)
mechanism: The reduced function is evaluated as a nested Horner series, with the detailed 2^x-1 implementation using a nine-term Taylor approximation (p.165). Most intermediate operations use fixed precision, while selected terms and the final addition use multiprecision arithmetic (pp.165, 169).
choices: none
new_choices: none
slots: none
parameters: 9 terms for 2^x-1; intermediate precision selected as one, two, or three floating-point digits   # pp.165, 167
results: none
errors_and_checks: Truncation error is plotted at Level 2, and approximation plus propagated roundoff error is bounded at Level 3 (pp.166-169).
conditions: Horner evaluation minimizes stored coefficients, while multiprecision is applied only at steps identified by error analysis (pp.164-165).
evidence: §2.2, §3.3, §3.4, §4.3, §4.4; Figures 3-5 (pp.165-169)

## new_families
### microcoded_transcendental  (domain: sfu, closest: lut_plus_poly, why_not: lut_plus_poly describes the approximation datapath but not ROM-dispatched instruction sequencing over a reused floating-point unit)
mechanism: Complex x86 transcendental instructions are translated into RISC instruction sequences stored in a RISC-code ROM (p.163). Up to four transcendental-code operations are dispatched at a time and may complete out of order on the existing pipelined floating-point unit (p.163). Multiprecision values span multiple floating-point registers, and a compiler schedules symbolic temporaries into fifteen 41-bit registers (pp.163-164, 167).
choices:
  instruction_source: {risc_code_rom}
  dispatch_width: Int[1..4:1]
  execution_order: {in_order, out_of_order}
  precision_extension: {native, multiprecision_digits}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum error | <1 | ulp | UNKNOWN / AMD K5 / 1995 | exact function | microcoded transcendental routines | p.163 |
evidence: §1, §2.1, §3.5 (pp.163-164, 167)

## space_gaps
* `lut_plus_poly.degree` excludes the nine-term degree-9 Taylor polynomial used for 2^x-1 (p.165).
* `lut_plus_poly` lacks a coefficient-generation choice for the documented on-the-fly coefficient strategy (p.165).
* `range_reduction.method` lacks multiprecision subtraction of a long reduction constant, as used with the approximately 256-bit representation of π/2 (p.164).
* The vocabulary lacks a family for ROM-microcoded transcendental instruction sequences that reuse a general floating-point datapath (pp.163, 167).

## open_questions
* The document does not map its 24/32/53/64-bit mantissa types to named architectural formats.
* The document does not report technology node, area, power, instruction latency, or throughput.
* The document does not give table sizes, polynomial degrees, or complete reduction details for functions other than the 2^x-1 example.
