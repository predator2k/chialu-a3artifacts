---
handle: trong_2007
citation: S. D. Trong, M. Schmookler, E. M. Schwarz, M. Kroener, "P6 Binary Floating-Point Unit", 18th IEEE Symposium on Computer Arithmetic, 2007
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [fp32, fp64, int32, int64]
authority: landmark
pages_read: 11 / 11
---

## summary
The document describes the POWER6 binary floating-point unit, which uses a seven-stage fused multiply-add pipeline with six-cycle dependent-operation issue, unfinished-result forwarding, a radix-4 multiplier, and a 120-bit end-around-carry adder (p.2-p.3, p.6-p.7). The unit also implements functional-iteration floating-point/fixed-point division and square root using linear reciprocal/reciprocal-square-root estimates with slightly more than 14 bits of precision (p.7-p.9). The 65nm SOI implementation runs close to 6 GHz, occupies about 2.5 mm2, and consumes 310 mW under the reported simulation condition (p.11).

## families
### classic_fma  (role: proposes)
mechanism: The seven-cycle fused multiply-add dataflow overlaps addend alignment with radix-4 partial-product generation, merges the aligned addend into the last 3:2 row, resolves the result through a 120-bit end-around-carry adder and LZA, normalizes across cycles 5-6, and rounds across cycles 6-7. Stage-6 results can be forwarded before rounding and final one-bit normalization; multiplier correction terms and delayed addend substitution preserve the final value (p.2-p.3, p.5-p.7).
choices:
  negation_handling: end_around_carry   # p.3
  pipeline_depth: 7   # p.2
new_choices:
  unfinished_result_forwarding: stage6_unrounded_partially_normalized — forwards a value before rounding/final normalization and corrects its later use   # p.6-p.7
slots:
  align: full_align   # p.3-p.4
  lza: lza   # p.3, p.5
  cpa: end_around_carry   # p.3
  round: increment_adder   # p.5-p.6
  multiplier: booth_recoded_parallel [booth_radix=4]   # p.3-p.4
parameters: 7 physical stages; 6 effective stages for most dependent instructions; 188-bit significand dataflow; 176-position alignment; normalization across cycles 5-6; rounding across cycles 6-7   # p.2-p.6
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| cycle time | 13 | FO4 | technology-independent (2007) | Power5: 23 FO4 | independent operations | p.1, p.11 |
| dependent-operation delay | 78 | FO4 | technology-independent (2007) | predecessor designs: 132 FO4 | most dependent BFU instructions | p.11 |
| effective dependent latency | 6 | cycles | POWER6, 65nm SOI (2007) | Power4/Power5: 6 cycles | excludes special forwarding cases | p.1-p.2 |
| tested frequency | close to 6 | GHz | POWER6, 65nm SOI (2007) | UNKNOWN | laboratory test | p.11 |
| dataflow power | 310 | mW | POWER6, 65nm SOI (2007) | UNKNOWN | 1.1V, 4GHz, 100% utilization | p.11 |
| unit area | about 2.5 | mm2 | POWER6, 65nm SOI (2007) | UNKNOWN | complete BFU | p.11 |
errors_and_checks: The multiplier correction term compensates for rounding increments on one or both forwarded product operands; the addend path substitutes the correctly rounded stage-7 fraction after stage-6 exponent use (p.6-p.7). Numerical error bounds are not reported.
conditions: Stage-6 forwarding is blocked when underflow/overflow/invalid-operation conditions may occur and for every single-precision instruction; invalid-operation traps can block both stage-6 and stage-7 forwarding (p.9-p.10). The datapath handles denormal operands and massive cancellation without the pipeline stalls used by predecessor designs (p.1, p.4-p.5).
evidence: Figure 1 (p.2), Figure 3 (p.5), Figure 4 (p.5), Tables 1-2 (p.6-p.7), §§2-7.

### booth_recoded_parallel  (role: instantiates)
mechanism: Traditional radix-4 Booth encoding generates 33 terms for a 64x64-bit product. Separate macros reduce the upper 17 terms and lower 16 terms plus the rounding-correction term across the first two cycles; a third macro completes reduction and merges the aligned addend during cycle 3 (p.3-p.4).
choices:
  booth_radix: 4   # p.3-p.4
  hard_multiple_gen: none   # p.4
new_choices:
  reduction_schedule: mixed_4_2_and_3_2 — mixes 4:2 and 3:2 carry-save rows across cycle boundaries   # p.3-p.4
slots:
  reduction: compressor_4_2_tree   # p.3-p.4
  hard_multiple_adder: none   # p.4
parameters: 64x64-bit operands; 33 partial-product terms; one rounding-correction term; 3 reduction cycles   # p.3-p.4
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| partial-product reduction latency | 3 | cycles | POWER6, 65nm SOI (2007) | UNKNOWN | includes aligned-addend merge in the final row | p.3-p.4 |
errors_and_checks: none
conditions: The 64x64-bit multiplier supports fixed-point multiplication and IEEE double-precision multiply-add; decoded implied bits remove the leading one/zero correction term used by cited implementations (p.3-p.4).
evidence: Figure 1 (p.2), §4 (p.4).

### end_around_carry  (role: instantiates)
mechanism: A 120-bit end-around-carry adder combines the multiplier-array partial sums with the aligned addend. The adder operates in parallel with the LZA across latch boundaries from the end of cycle 3 into the beginning of cycle 5, followed by conditional recomplementation (p.3).
choices:
  modulus: UNKNOWN
  recirculation: UNKNOWN
new_choices:
  none
slots:
  none
parameters: 120-bit width; spans the end of cycle 3 through the beginning of cycle 5   # p.3
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
errors_and_checks: none
conditions: The adder is the terminal carry-propagate stage for the fused partial products and aligned addend (p.3).
evidence: Figure 1 and §2 (p.2-p.3).

### goldschmidt  (role: extends)
mechanism: Floating-point divide and square root use functional iteration equivalent to Goldschmidt algorithms. Multiply-add operations avoid extra feedback-path complementing circuits, while wider integer/hexadecimal-capable paths retain enough intermediate precision to keep accumulated rounding error below one quarter ulp. Fixed-point division uses the same reciprocal-estimate flow and conditionally adds a Newton-Raphson refinement for full 64-bit precision (p.8-p.9).
choices:
  iterations: UNKNOWN
  internal_guard_bits: UNKNOWN
  truncated_intermediate_multiplies: UNKNOWN
new_choices:
  final_refinement: conditional_newton_raphson — used for 64-bit division unless the numerator has fewer than 50 significant bits   # p.9
slots:
  seed: linear_pwl_reciprocal_seed [precision=slightly_more_than_14_bits]   # p.7-p.8
  iter_mult: booth_recoded_parallel [booth_radix=4]   # p.8-p.9
  final_round: UNKNOWN   # p.8
parameters: floating-point divide/square root with data-dependent latency; fixed-point signed/unsigned 32-bit and 64-bit division; one conditional Newton-Raphson step   # p.8-p.9
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| non-IEEE latency reduction | 7 | cycles | POWER6, 65nm SOI (2007) | IEEE mode | rounding test omitted | p.8 |
| fixed-point divide latency | 45 | cycles | POWER6, 65nm SOI (2007) | UNKNOWN | doubleword divide with larger numerator; excludes BFU/GPR transfers | p.9 |
| fixed-point divide latency | 33 | cycles | POWER6, 65nm SOI (2007) | 45-cycle path | smaller numerator or any single-word divide | p.9 |
| conditional refinement saving | 12 | cycles | POWER6, 65nm SOI (2007) | path with Newton-Raphson step | 32-bit divide or numerator with fewer than 50 significant bits | p.9 |
errors_and_checks: Accumulated intermediate rounding error is much less than a quarter ulp for floating-point divide/square root (p.8). The final IEEE rounding-test mechanism is not described.
conditions: Denormal operands require extra normalization cycles because divide/square-root latency is data dependent (p.8). Non-IEEE mode omits the rounding test when correct IEEE rounding is unnecessary (p.8).
evidence: §8 (p.7-p.9).

### residue  (role: instantiates)
mechanism: Residue-checking logic protects the full internal significand dataflow for every multiply-add operation. Residue 3 is selected for timing reasons; the generator structure and comparison point are not described (p.10-p.11).
choices:
  modulus: 3   # p.11
new_choices:
  protected_scope: full_significand_dataflow — covers internal multiply-add arithmetic   # p.10-p.11
slots:
  comparator: UNKNOWN   # p.10-p.11
parameters: one residue-3 check path for the significand dataflow   # p.10-p.11
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
errors_and_checks: Detection coverage, false-alarm behavior, and alias rate are UNKNOWN.
conditions: Residue checking covers all multiply-add operations; parity separately protects FPR bytes, load/store inputs, and BFU input/output buses (p.10-p.11).
evidence: “Checking - Clock gating” (p.10-p.11).

## new_families
### linear_pwl_reciprocal_seed  (domain: div: reciprocal seed tables, closest: monolithic_rom, why_not: The unit stores line offsets and radix-8 Booth-decoded slopes and evaluates a linear approximation rather than returning a table value.)
mechanism: The seed unit partitions the normalized operand by its first six fraction bits into 64 linear segments. One reciprocal table and two reciprocal-square-root tables for even/odd exponents supply an offset and encoded slope; a small radix-8 multiplier uses the next 11 operand bits, and a final addition produces slightly more than 14 bits of precision in three cycles (p.7-p.8).
choices: function: {reciprocal, reciprocal_square_root, both}; segments: {64}; tables: {1, 2, 3}; slope_encoding: {radix8_booth_decoded}; operand_tail_bits: {11}; latency_cycles: {3}
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| estimate precision | slightly more than 14 | bits | POWER6, 65nm SOI (2007) | prior architecture estimates: 8-bit reciprocal/5-bit reciprocal-square-root | reciprocal and reciprocal-square-root estimates | p.7 |
| estimate latency | 3 | cycles | POWER6, 65nm SOI (2007) | UNKNOWN | linear approximation | p.7-p.8 |
evidence: “Reciprocal Estimate Tables” (p.7-p.8).

## space_gaps
* The `goldschmidt.seed` slot should admit `linear_pwl_reciprocal_seed`, because the implemented seed combines coefficient tables with a linear multiplier (p.7-p.8).
* The `classic_fma` family lacks an unfinished-result-forwarding choice for stage-6 unrounded/partially normalized feedback with later correction (p.6-p.7).
* The Booth reduction vocabulary lacks a value for mixed 4:2/3:2 carry-save rows (p.3-p.4).
* The checker vocabulary lacks a general parity family for register bytes, buses, and data movement (p.10-p.11).

## open_questions
* The exact number of Goldschmidt iterations for each floating-point operation/format is not stated.
* The IEEE divide/square-root rounding test is named but its mechanism is not described.
* The end-around-carry adder's modulus and recirculation organization are not stated.
* The residue generator, comparison point, detection coverage, false-alarm behavior, and alias rate are not reported.
