---
handle: naini_2001
citation: A. Naini, A. Dhablania, W. James, D. Das Sarma, "1-GHz HAL SPARC64 Dual Floating Point Unit with RAS Features", ARITH-15, 2001
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [fp32, fp64, int8, int16, int32]
authority: incremental
pages_read: 173-183 / 11
---

## summary
The paper presents the HAL Sparc64-V floating-point unit, which is a 1 GHz IEEE-754 FPU in 0.15u 6-layer metal CMOS with two identical functional units, each holding a 3-cycle dual-path adder (FADD) and a 4-cycle multiplier (FMUL) that also runs Goldschmidt division and square root, plus one VIS SIMD fixed-point unit. The adder's Path 1 selection criterion is extended with a condition on the larger operand's mantissa so that Path 1 needs no rounding stage, and Path 2 rounds by selecting among A+B and A+B+2. The multiplier array is folded so the inter-level alignment shifts fall on the multiplicand instead of on the CSA sum and carry outputs, and RAS comes from dual-rail domino checking in the FADD and parity prediction in the FMUL back end.

## families
### two_path  (role: extends)
mechanism: Two concurrent pipelines, each shifting in one direction only. Path 1 takes effective subtraction with exponent difference 0, and exponent difference 1 when the mantissa of the larger-exponent operand is less than 1.5; the minuend is then in [1, 1.5) and the one-bit-right-shifted subtrahend in [0.5, 1), so the result is in (0, 1), always needs a one-bit left shift, and the guard bit lands on the LSB, which removes Path 1's rounding stage. Path 2 takes effective addition and all other subtraction. Exponent subtractions A - B and B - A both run, their low-order bits partially right shift both mantissas by 0, 1, 2 or 3, the smaller operand is then selected and swapped into the subtrahend position, and stage 2 completes the shift.
choices:
  path_threshold: 1   # p.175
  close_path_trigger: exp_diff_and_effective_sub   # p.175
  operand_order: swap_before_shift   # p.176
  path_select_point: late_result_mux   # p.177
new_choices:
  path1_round_free_condition: larger_operand_mantissa_below_1_5 — the exponent-difference-of-1 subtraction goes to Path 1 only when the larger operand's mantissa is below 1.5, which forces the normalizing left shift and removes the Path 1 rounding stage   # p.175
  rounding_increment_injection: csa_row_at_lsb_plus_1 — a CSA row before the A+B+2 adder inserts a 1 at bit 41 (single) or bit 12 (double), in place of a flagged adder whose split carry chain would slow the adder topology   # p.176
slots:
  far_align: full_align [speculative 0/1/2/3-bit pre-shift of both mantissas in stage 1, full shift in stage 2; 0/16/32/64 mux stage in Figure 3]   # p.175, p.176
  near_lz: lza [z_i = ((a_i XOR b_i) + (c . b_{i-1})), i = 1 to 63, no full carry chain]   # p.176
  close_norm: coarse_fine [mux stages 0/4/8/12 and 0/16/32/48 driven by the decoded LZC]   # p.175, p.176
parameters: adder result indexed [64:0]; double-precision result bits [63:12] with fill bits at 12 and 11, single-precision [63:41] with fill bits at 41 and 40; 3 pipe stages, the last half cycle used for result distribution.   # p.176, p.177
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 3 | cycles | 0.15u 6-layer metal CMOS / 2001 | none | FADD/FSUB, single and double precision | p.174 |
| throughput | 1 | cycles | 0.15u 6-layer metal CMOS / 2001 | none | fully pipelined | p.174 |
errors_and_checks: IEEE-754 compliant in all four rounding modes; the leading-zero prediction vector has at most one too few leading zeros, the error is detected from the MSB (hidden bit) of the normalized result and corrected by a one-bit left shift in pipe stage 3.   # p.176
conditions: only normalized results are supported, so denormal operands and denormal results are trapped as unfinished-FPop outside the extreme-underflow cases handled in hardware.   # p.176, p.181
evidence: section 2, sections 2.1-2.2, Figure 3, Tables 2-4.

### shift_round_convert  (role: instantiates)
mechanism: The conversion instructions reuse the two adder paths. Single-to-double and integer-to-floating-point conversions run in Path 1, where the left shifter normalizes a denormal incoming operand. Double-to-single and floating-point-to-integer conversions run in Path 2, because single-precision conversion needs rounding and float-to-integer needs a right shift driven by the exponent.
choices: (none fixed beyond the host paths)
new_choices: none
slots:
  shifter: barrel_mux_tree [select_encoding=one_hot_decoded, stages 0/4/8/12 and 0/16/32/48]   # p.175, p.176
  round: compound_adder_select [A+B and A+B+2 with fill bits at LSB+1 and LSB]   # p.177
parameters: conversion latency equals the FADD latency of 3 cycles, except integer-to-floating-point.   # p.174, p.177
results: none
errors_and_checks: none
conditions: an integer-to-floating-point conversion that needs rounding after the normalizing left shift costs one extra cycle, because Path 1 has no rounding step.   # p.177
evidence: section 2.3.

### sig_mul_then_round  (role: instantiates)
mechanism: A 60x60 mantissa array produces the product in redundant form. Pipe stage 3 assimilates the sum and carry vectors in a group carry-lookahead adder with carry select; separate circuitry generates the carry-out of the low-order 60 bits and supplies the adder's carry-in for result selection. The sticky bit is computed in parallel, directly from the redundant sum and carry bits with the propagate and kill signals of the 60-bit carry-out logic (equation 4, i = 1 to 58), and is the OR of that vector. Sums with assumed overflow and non-overflow are generated with and without carry-in, and rounding is two levels of selection: first on the carry-in bit, then on the overflow bit, round bit, sticky bit and rounding mode.
choices: (the family declares none)
new_choices:
  sticky_source: redundant_sum_carry_with_propagate_kill — the sticky tree runs on the redundant sum and carry bits in parallel with the carry-out, rather than after the CPA   # p.178
  rounding_result_selection: two_level_carry_in_then_overflow — four pre-computed sums selected first by carry-in, then by overflow/round/sticky/mode   # p.178
slots:
  sig_mul: booth_recoded_parallel [booth_radix=4]   # p.177
parameters: 60x60 mantissa array; 120-bit raw product; 4 pipe stages, of which three and a half are execution.   # p.177, p.178
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 4 | cycles | 0.15u 6-layer metal CMOS / 2001 | none | FMUL, fully pipelined | p.173 |
errors_and_checks: correctly rounded IEEE-754 result; pipe stages 1 and 2 are static logic with no RAS protection, pipe stages 3 and 4 are covered by parity prediction.   # p.182
conditions: the array is 60x60 rather than significand-sized because the division and square-root iterations need that width for correct IEEE-754 rounding.   # p.177
evidence: section 3, Figure 4, equation 4.

### booth_recoded_parallel  (role: instantiates)
mechanism: Pipe stage 1 performs operand alignment and radix-4 modified Booth recoding, generating 31 partial products in two's complement form. Sign extension is achieved by adding two extra bits, giving a 63-bit partial product vector to which the Booth sign Pbs is added (equations 2 and 3). Pipe stage 2 reduces 31 partial products plus the division/square-root residual addend, which is 32 summands, to sum and carry through four levels of 4to2 CSA rows. The array is folded: the multiplicand is routed diagonally and the partial products are aligned so the redundant CSA outputs need no shift, columns b58..b52 are duplicated in the lower half to avoid routing from column b58 to b59, and result bits and sticky bits are grouped.
choices:
  booth_radix: 4   # p.177
  sign_extension: prevention_constant   # p.177, p.178
  negative_pp_encoding: twos_complement_row   # p.177
new_choices:
  array_alignment_side: multiplicand_diagonal — the 8, 16 and 32-bit alignment shifts between CSA levels are applied to the diagonally routed multiplicand instead of to the CSA sum and carry outputs, so wire delay on the critical path is minimized   # p.178
  column_duplication: b58_to_b52_in_lower_half — the duplicated columns remove the cross-array routing from column b58 to column b59   # p.178
slots:
  reduction: compressor_4_2_tree [4 levels, 32 summands to 2]   # p.178
parameters: 60-bit operands; 31 partial products; 63-bit partial product vector; four 4to2 CSA levels.   # p.177, p.178
results: none
errors_and_checks: none
conditions: radix-8 was rejected because generating the +3 and -3 partial products adds delay, and at 60 bits both radix-4 and radix-8 recoding need four levels of 4to2 CSA, so radix-8 saves no level.   # p.177
evidence: section 3, equations 2-3, Figure 5.

### twin_precision_subword  (role: instantiates)
mechanism: The 60x60 mantissa array also executes four 8x16 signed SIMD graphics multiplies for VIS2.0. The VIS unit takes its operands from the FMUL unit and returns the result to it, which decouples it from the source and result distribution paths.
choices:
  per_lane_signed: true   # p.177
new_choices: none
slots: none
parameters: four 8x16 signed products on the 60x60 array; VIS operands are 8, 16 or 32 bits; half a cycle each way between FMUL and VIS.   # p.174, p.177
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 2 | cycles | 0.15u 6-layer metal CMOS / 2001 | none | minimum VIS instruction latency, of which half a cycle is execution | p.174 |
errors_and_checks: none
conditions: the VIS unit is static logic and gets no RAS protection.   # p.182
evidence: section 1, section 3, Figure 2.

### goldschmidt  (role: instantiates)
mechanism: Division and square root iterate on the multiplier and are not pipelined. For division the seed F0 comes from a 7-bits-in, 10-bits-out table indexed by the leading 7 bits of B; Q1 = floor(A.F0), G1 = ceil(B.F0), then Fi = floor(2 - Gi), Q_{i+1} = floor(Qi.Fi), G_{i+1} = ceil(Gi.Fi) for i = 1, 2, 3. For square root the seed comes from one of two 128-entry 9-bit tables selected by the parity of B's exponent, and Fi = floor(1/2.(3 - Gi)). The refinement factors 2 - Gi and 1/2.(3 - Gi) are formed by complementing Gi and adding the constant (1 for division, 3/2 for square root) in unused slots of the CSA rows.
choices:
  iterations: 3   # p.179 (i = 1, 2, 3; single precision stops at Q3, double precision needs Q4)
  truncated_intermediate_multiplies: true   # p.179 (directed rounding; round-up approximated by unconditionally adding one at bit 60)
new_choices:
  refinement_constant_injection: unused_csa_slots — the additive constant of the refinement factor enters unused slots of the multiplier's CSA rows, so no separate adder is used   # p.179
  seed_rounding_direction: always_below_exact — seed values are always chosen less than the infinitely precise value, minimizing the maximum relative error over [1, 2)   # p.179
slots:
  seed: monolithic_rom [input_bits=7, output_bits=10] for division; monolithic_rom [input_bits=7, output_bits=9, two tables selected by exponent parity] for square root   # p.179
  iter_mult: booth_recoded_parallel [booth_radix=4] (the 60x60 array, first three pipe stages only)   # p.179, p.180
  final_round: back_multiply_remainder [quotient_candidates=3, residual C = A - Qc.B for division and C = B - Q^2 for square root]   # p.180
parameters: each iteration multiply is 60x60 with the 120-bit result rounded to 60 bits; Qc is Q rounded up to 1/2 ulp (25 bits single, 54 bits double); the candidates are trunc(Q), trunc(Q + 1/2 ulp) and trunc(Q + 1 ulp), truncated to 24 bits single and 53 bits double; one cycle of pipeline bubble between Q3 and the residual C; the done signal is sent 6 cycles before the result drives the bus.   # p.179, p.180, p.181
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 16 | cycles | 0.15u 6-layer metal CMOS / 2001 | none | FDIV single precision | p.181 |
| latency | 19 | cycles | 0.15u 6-layer metal CMOS / 2001 | none | FDIV double precision | p.181 |
| latency | 22 | cycles | 0.15u 6-layer metal CMOS / 2001 | none | FSQRT single precision | p.181 |
| latency | 27 | cycles | 0.15u 6-layer metal CMOS / 2001 | none | FSQRT double precision | p.181 |
| throughput | 19 | cycles | 0.15u 6-layer metal CMOS / 2001 | none | FSQRT single precision, Table 1; throughput is three cycles shorter than latency for every divide/sqrt | p.174, p.181 |
| throughput | 24 | cycles | 0.15u 6-layer metal CMOS / 2001 | none | FSQRT double precision, Table 1 | p.174 |
| latency reduction | 3 | cycles | 0.15u 6-layer metal CMOS / 2001 | iterating through the full four-stage multiplier pipe | divide, bypass path that uses only the first three stages | p.182 |
| latency reduction | 5 | cycles | 0.15u 6-layer metal CMOS / 2001 | iterating through the full four-stage multiplier pipe | square root, same bypass path | p.182 |
| latency | 10 | cycles | 0.15u 6-layer metal CMOS / 2001 | none | divide and square root on special operands (Zero, QNAN, SNAN, Infinity), early exit without iterating | p.180 |
errors_and_checks: the maximum error is bounded by accumulating the algorithm's approximation error and the computational error from finite table values and finite multiplier size over the required iterations. The 120-bit raw result Q satisfies q - 1/2 ulp < Q < q for q >= 1 and q - <coefficient illegible> ulp < Q < q for q < 1 for division, and q - <coefficient illegible> ulp + ulp^2 < Q < q for square root, where ulp = 2^-23 for single precision and the double-precision exponent is illegible in the text; the bound is stated to be sufficient for a correctly rounded result in all rounding modes.   # p.181
conditions: divide and square root block the FMUL unit until they complete; a subsequent operation can enter the multiply pipe once the last iteration has moved to pipe stage 2. A bipartite seed table of the same initial accuracy was investigated and found slower than the single-table access. Four 10-bit tables and a 14-bit adder would cut one iteration through the multiplier, and the area penalty far exceeded the potential latency improvement.   # p.179, p.181
evidence: section 3.1, equations 5-8, Table 5.

### bridge_fma  (role: instantiates)
mechanism: uFMADD and uFMSUB are two non-SPARC unfused instructions in which rounding happens twice: multiply, round, add or subtract, round. src1 and src2 go to the FMUL unit and src3 to the FADD unit, and the FMUL result reaches the FADD unit over an internal FMA bus. No add, subtract, conversion, compare or move instruction is scheduled to that FADD unit in the cycle the bridged add runs. Rounding after the multiply makes the intermediate IEEE-754 compliant and makes exceptions precise.
choices:
  composition_style: cascade_mul_then_add   # p.173
  cascade_product_rounding: ieee754_active_rounding_mode [outside domain]   # p.173
new_choices: none
slots: none stated
parameters: three source operands per instruction; the FRS has six read ports, three per functional unit; 16-entry reservation station; two instructions issued out of order per cycle.   # p.173
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 7 | cycles | 0.15u 6-layer metal CMOS / 2001 | none | uFMADD/uFMSUB | p.174 |
| throughput | 1 | cycles | 0.15u 6-layer metal CMOS / 2001 | none | uFMADD/uFMSUB | p.174 |
| peak rate | 4 | GFLOPS | 0.15u 6-layer metal CMOS / 2001 | none | two uFMADD/uFMSUB scheduled per cycle at 1 GHz | p.173 |
| cycle time | 1 | ns | 0.15u 6-layer metal CMOS / 2001 | none | 85 C; the supply voltage prints illegibly as "1.W" | p.182 |
| transistor count | 1.9 | Million | 0.15u 6-layer metal CMOS / 2001 | none | whole FPU, full custom methodology | p.182 |
| transistor density | 87 | KT/mm2 | 0.15u 6-layer metal CMOS / 2001 | none | whole FPU | p.182 |
| footprint | 9.1 x 2.4 | mm2 | 0.15u 6-layer metal CMOS / 2001 | none | whole FPU | p.182 |
errors_and_checks: the product is rounded before the addition, so the instruction is not a fused multiply-add; if the multiply raises an exception the add or subtract is not executed and the multiply's exception state is forwarded to the trap handler.   # p.173
conditions: one half cycle of every latency is reserved for result distribution, because the result bus wires are long and back-to-back execution matters.   # p.173
evidence: section 1, Figure 1, Table 1, Table 8.

### parity_prediction_adder  (role: instantiates)
mechanism: Data buses are parity protected on the 32-bit word boundary instead of the 8-bit byte, which reduces the number of parity bits distributed and stored; 32-bit parity generation takes five levels of logic, so parity is distributed one cycle after the data. The FRS registers hold data for more than one cycle and are parity protected, with parity written and read one cycle after the data and checked on read. FMUL pipe stages 3 and 4 use single-rail dynamic circuits and are covered by parity prediction, which lags the data by half a cycle; Figure 7 works the prediction through a 1-bit left shift.
choices: (the paper fixes none of the declared choices)
new_choices:
  parity_word_granularity_bits: 32 — one parity bit per 32-bit word on the data buses rather than per byte   # p.181
  prediction_latency: half_cycle_lag — the predicted parity trails the data by half a cycle   # p.182
slots: none stated
parameters: 32-bit parity groups; five levels of logic per parity generation; parity distributed one cycle after the data.   # p.181
results:
| metric | value | unit | technology / device | baseline | condition | page |
| target failure rate | 240 | fit (failures per 10^9 hours) | 0.15u 6-layer metal CMOS / 2001 | none | Sparc64-V RAS target | p.174 |
| soft error rate | 0.00052 | unit not printed | 0.15u 6-layer metal CMOS / 2001 | none | latch, Table 7 | p.181 |
| soft error rate | 0.0013 | unit not printed | 0.15u 6-layer metal CMOS / 2001 | none | dynamic circuit, Table 7 | p.181 |
errors_and_checks: the fault model is soft errors from cosmic rays and alpha particles. Static-circuit soft errors are recoverable most of the time and become unrecoverable once they propagate into a latch or flip-flop; dynamic circuits and storage elements are non-recoverable, so RAS covers the dynamic circuits and every register holding state for more than one cycle. A detected error reschedules the instruction, correction is attempted on re-execution, and unresolved errors are logged into software-accessible registers. FPU RAS error reporting is synchronized with floating-point exception reporting.   # p.181, p.182
conditions: parity prediction for the arithmetic functions is expensive in both area and speed, which is why the FADD uses dual-rail domino checking instead.   # p.181
evidence: section 5, Table 7, Figure 7.

### residue  (role: compares)
mechanism: No residue checker is built. The paper states that multiplier arrays are in general protected with residue checking because residue arithmetic takes less area, but that residue generation timing is more critical than the critical timing of the array itself.
choices: none
new_choices: none
slots: none
parameters: none
results: none
errors_and_checks: the multiplier array (pipe stages 1 and 2) is left unprotected and built in static logic.   # p.182
conditions: at a 1 ns cycle the residue generator's timing, rather than its area, rules the scheme out.   # p.182
evidence: section 5.

## new_families
### dual_rail_domino_code_check  (domain: checker: two-rail / self-checking, closest: two_rail_tree, why_not: two_rail_tree reduces many code pairs through a morphic-cell tree to one self-checking alternating output pair, whereas here each dual-rail domino cone's true and complement outputs are XORed in place and no code-disjoint tree is built.)
mechanism: The FADD is 80% dynamic circuits. Building it as dual-rail domino lets the true and complement signals at the last cone of logic be XORed, and an XOR output of zero indicates an error, because a fault-free dual-rail pair is complementary. The check covers the align, compare and add blocks of the FADD. In the adder the final carry and carry-complement are XORed, which detects a fault only as long as the carry and carry-complement logic are independent. Figure 6 shows the check on a dual-rail domino AND gate, and the paper states the concept applies to any dual-rail domino gate.
choices: checked_blocks: enum of the dynamic-logic blocks whose last cone is XORed (align, compare, add); independent_dual_rail_cones: Bool (the true and complement logic must be independent for the check to hold)
results:
| metric | value | unit | technology / device | baseline | condition | page |
| coverage | 80 | % of the domino logic | 0.15u 6-layer metal CMOS / 2001 | none | FADD unit, which is itself 80% dynamic circuits | p.181 |
evidence: p.181, p.182, Figure 6.

## space_gaps
* The fp adder families have no `round` slot, so Path 2's A+B and A+B+2 compound-adder rounding with fill bits has nowhere to go, while the dot families carry `round: {increment_adder, compound_adder_select, injection, flagged_prefix}`.   # p.176, p.177
* `sig_mul_then_round` declares no choices and no `round` slot, so the multiplier's two-level rounding selection and its sticky-from-redundant-form cannot be recorded as choices.   # p.178
* `two_path.close_path_trigger` has no value for the paper's third condition, which is the magnitude of the larger operand's mantissa against 1.5.   # p.175
* `two_path.operand_order` has no value for Path 2, which partially right shifts both mantissas by 0 to 3 before the precedence is known and swaps afterwards.   # p.176
* `bridge_fma.cascade_product_rounding` lacks the unit's active IEEE-754 rounding mode, which is what the unfused instructions apply after the multiply.   # p.173
* The checker section has parity_prediction_adder and parity_prediction_multiplier but no parity prediction for a shifter, which is the worked example of Figure 7.   # p.182
* `goldschmidt.iter_add` assumes a carry-propagate adder, but the refinement constants 1 and 3/2 are added in unused slots of the multiplier's CSA rows.   # p.179
* The reduction-tree slot fillers have no choice for which side carries the inter-level alignment shift, which is the diagonally routed multiplicand here rather than the CSA sum and carry outputs.   # p.178

## open_questions
* The supply voltage in Table 8 prints as "1.W", so only the 1 ns cycle time and 85 C are recoverable.   # p.182
* The fractional ulp coefficients of the division bound for q < 1 and of the square-root bound print as "VI", and the double-precision ulp exponent prints as "2.''", so those constants are not recoverable.   # p.181
* The Table 1 rows for FDIVs and FDIVd are blank in the text; the 16-cycle and 19-cycle latencies come from the prose of section 3.1.   # p.174, p.181
* Whether the FMUL's parity prediction uses a duplicate carry or a carry-dependent sum is not stated.   # p.182
* Table 7 gives no unit for the latch and dynamic-circuit soft error rates.   # p.181
