---
handle: jessani_1996
citation: R. M. Jessani, C. H. Olson, "The Floating-Point Unit of the PowerPC 603e Microprocessor", IBM Journal of Research and Development, vol. 40, no. 5, 1996
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp32, fp64]
authority: incremental
pages_read: 559-566 / 8
---

## summary
The paper describes the PowerPC 603e on-chip floating-point unit, a three-stage (multiply, carry-propagate-add, writeback) IEEE 754 fused multiply-add engine that computes FRT = FRA * FRC + FRB with one terminal round. The multiply stage uses a radix-4 Booth-recoded Wallace tree of 4-to-2 CSAs sized at 53 by 28 bits, double-pumped for double precision, while FRB is aligned in parallel and merged by a 3-to-2 CSA. The unit occupies less than 15 mm^2, runs at 100 MHz, and is estimated at 105 on SPECfp92.

## families
### classic_fma  (role: instantiates)
mechanism: One instruction FRT = FRA * FRC + FRB; move, add, subtract and multiply are derived from it by forcing FRC to 1.0 or FRB to 0.0. The multiply stage produces the accumulated partial product in sum-and-carry form while FRB is right-shifted to align with FRA times FRC; the aligned FRB and the product are compressed by a 3-to-2 carry-save adder. The CPA stage does a 161-bit one's complement add through a carry-lookahead adder, and the result passes a leading-zero detector for the normalization shift count. The WB stage does the normalization left shift, rounding and status generation. A bypass unit routes NaN/infinity operands and abnormal operations (divide by zero, Inf - Inf, Inf * 0) straight to WB.
choices:
  subsume_fp_add: true   # p.559
  negation_handling: end_around_carry   # p.561
new_choices:
  operand_passes: 2 — the significand multiplier is half a full 53 by 53 array, so a double-precision multiply iterates the array twice (double pumping), costing an extra cycle in the multiply stage   # p.560, p.561
slots:
  multiplier: booth_recoded_parallel [booth_radix=4]   # p.561
  align: full_align   # p.560, p.562
  cpa: carry_lookahead   # p.560, p.561
  lza: lzc_after_add   # p.560, p.563
  norm_shifter: barrel_mux_tree   # p.563
parameters: three pipeline stages, multiply / CPA / WB, one cycle each in the normal case (p.560); 53 by 28-bit multiplier array (p.560), given as a 54 X 28 arrangement (p.561); 143-bit alignment, implemented as a 53-bit-input 136-bit-output right shifter (p.562); 161-bit CPA holding an 88-bit CLA and a 26-bit lookahead incrementer (p.561); 63-bit normalization shifter (p.563); three 63-bit LZDs (p.563); 32 FPRs plus 4 rename buffers, each entry 70 bits = 3-bit tag + 1-bit sign + 13-bit exponent + 53-bit mantissa (p.559, p.563).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| FPU silicon area | < 15 | mm^2 | UNKNOWN / 1996 | none | PowerPC 603e chip is 98 mm^2 | p.559 |
| peak clock frequency | 100 | MHz | UNKNOWN / 1996 | none | — | p.559 |
| SPECfp92 (estimated) | 105 | score | UNKNOWN / 1996 | none | at 100 MHz | p.559 |
| multiply-add-fuse throughput | 1 | cycle | UNKNOWN / 1996 | none | average single-pumping instruction | p.559 |
| multiply-add-fuse latency | 4 | cycles | UNKNOWN / 1996 | none | average single-pumping instruction | p.559 |
| multiply-add-fuse throughput | 2 | cycles | UNKNOWN / 1996 | none | average double-pumping instruction | p.559 |
| multiply-add-fuse latency | 5 | cycles | UNKNOWN / 1996 | none | average double-pumping instruction | p.559 |
| extra WB cycles | 1 to 2 | cycles | UNKNOWN / 1996 | none | mass cancellation in the mantissa calculation | p.561, p.563 |
| extra cycles | 1 | cycle | UNKNOWN / 1996 | none | underflow or overflow exponent correction; also denormalization of a result | p.561, p.566 |
| extra cycles before execution starts | 3 / 4 / 5 | cycles | UNKNOWN / 1996 | none | one / two / three denormalized source operands | p.566 |
errors_and_checks: Scientific mode conforms to ANSI/IEEE 754-1985 including all four rounding modes and exception status reporting, with a dependency on supporting software; real-time mode (NI bit set in the FPSCR) conforms to a subset, all exceptions handled in hardware with default results such as QNaN, maximum and zero (p.560). Exceptions split into early detect in the multiply cycle (seven invalid operations, zero divide) and late detect in WB (overflow, underflow, inexact) (p.564). Each instruction carries a 3-bit IDN so the trapping instruction is identifiable (p.564). Logic verified by a random test generation program on an FPU stand-alone model and a whole-chip model (p.560).
conditions: Design objective is a low-cost, low-power, high-performance engine inside a single-chip superscalar microprocessor (p.559). Full double-precision multiply costs an extra multiply-stage cycle because the array is half size (p.561). Denormalized source operands stall dispatch and are prenormalized through the WB normalization shifter, the LZD in the CPA stage being unusable for this because a 2:1 mux in that path would compromise timing (p.565, p.566). The unit needs the same minimum software envelope as high-end RS/6000 processors (p.566).
evidence: Abstract and Introduction (p.559); "Basic instruction pipeline stage and timing" (p.560); "Architecture/implementation" with the bypass unit, multiplier array and CPA subsections (p.561); Figure 6 (multiplier array structure) and Figure 7 (CPA); "Prenormalization/denormalization" (p.565-566); Summary (p.566).

### booth_recoded_parallel  (role: instantiates)
mechanism: Radix-4 Booth recoding halves the summands, and a Wallace tree of 4-to-2 CSAs adds them; the array is a 53 by 28 (stated as 54 X 28 on p.561) arrangement capable of unsigned operations, built with three levels of 4-to-2 CSAs so it is half the size of a full 53 by 53 array. Figure 6 shows the Booth encoder driving 5:1 muxes that select 0, A, 2A and their negatives. Two feedback paths for the most significant bits of the sum and the carry each use a 2:1 mux, so the first pass is incorporated into the second pass for double-precision double pumping. Single-precision multiplication runs at one instruction per cycle.
choices:
  booth_radix: 4   # p.561
new_choices: none
slots:
  reduction: compressor_4_2_tree   # p.560, p.561
parameters: 53 by 28-bit array (p.560) / 54 X 28 arrangement (p.561); three levels of 4-to-2 CSAs (p.560); a 3-to-2 CSA merges the aligned FRB (p.560); low 26 bits of the product are produced in the first CPA cycle and saved (p.561).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| array size | half of a full 53 by 53 array | ratio | UNKNOWN / 1996 | full 53 by 53 array | area saving motive, paid for by double pumping | p.560 |
| single-precision multiply rate | 1 | instruction per cycle | UNKNOWN / 1996 | none | no data dependency | p.561 |
errors_and_checks: none
conditions: The half-size array wins silicon area but requires double pumping through the multiplier array for a full double-precision multiply (p.560, p.561).
evidence: "Basic instruction pipeline stage and timing" (p.560); "Multiplier array" subsection and Figure 6 (p.561).

### carry_lookahead  (role: instantiates)
mechanism: The carry-propagate-add stage is a 161-bit adder split into three pieces. The lower 26-bit portion is an incrementer rather than a CLA, because the lower 26-bit product from the multiply array was already generated by the CLA in the first CPA cycle and saved; carry-lookahead incrementers are smaller and faster than carry-lookahead adders, so the actual CLA is only 88 bits wide (the following sentence calls it the 87-bit CLA). Figure 7 draws the 161-bit adder divided into four sections with group carry-in equations of the form Cin_c = P_b + G and Cin_d = P_c + P_b + G. The upper 63-bit portion of the CPA result is examined for leading zeros.
choices:
  intergroup_carry: lookahead   # p.561, Figure 7
new_choices: none
slots: none
parameters: 161-bit adder; 88-bit CLA (87-bit in the next sentence); 26-bit lower incrementer; Figure 7 shows four sections (p.561).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| CLA width actually built | 88 | bits | UNKNOWN / 1996 | a full 161-bit CLA | lower 26 bits become an incrementer, upper sections are incrementers | p.561 |
errors_and_checks: none
conditions: The split is available only because the low product bits are already assimilated in the first CPA cycle, which lets an incrementer replace a CLA there (p.561).
evidence: "CPA (carry-propagate adder)" subsection and Figure 7 (p.561).

### end_around_carry  (role: instantiates)
mechanism: The CPA is a 161-bit one's complement adder with an end-around-carry adjustment. It takes the one's complement input from the aligned FRB and the result of FRA * FRC, which is always positive relative to FRB, and its output is sign-magnitude with the sign bit handled in control logic. The propagate from the carry-lookahead incrementer and the group identifier generated by the CLA are fed back to the carry-in to correct the end-around-carry problem without a closed loop. XOR gates at the output invert the result back to sign-magnitude format. The one's complement adder is used because it makes conversion back to sign-magnitude easier.
choices:
  recirculation: group identifier and incrementer propagate fed back to the carry-in, no closed loop [outside domain]   # p.561
new_choices: none
slots:
  incrementer: prefix_and_incrementer   # p.561 (the lower 26-bit carry-lookahead incrementer whose propagate drives the correction)
parameters: 161-bit one's complement add; sign-magnitude output; correction in one pass (p.561).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| adder width | 161 | bits | UNKNOWN / 1996 | none | one's complement, end-around-carry adjusted | p.561 |
errors_and_checks: none
conditions: The choice is justified by the ease of converting the result back to sign-magnitude format rather than by delay (p.561, p.562).
evidence: "CPA (carry-propagate adder)" subsection, Figure 7 levels 1 and 2 (one's complement adder examples with end-around-carry adjustments) (p.561-562).

### barrel_mux_tree  (role: instantiates)
mechanism: The alignment shifter for the B mantissa is a 53-bit-input 136-bit-output right shifter, reduced by double pumping, implemented as a partial decode with three levels of partial-shift groups, or as a modulo shifter of maximum shift count 143, each nested shift amount being calculated with modulo arithmetic. The three levels shift by binary (0, 1, 2, 3), by multiples of 4 bits (0, 4, 8, 12) and by multiples of 16 bits (0, 16, 32, 48, 64, 80, 96, 112, 128). A bypass port in the third level prevents shifting from a negative shift count and lets the first two levels compute their shift counts sooner. The shifter also includes automatic sticky-bit detection for the bits shifted off. The normalization shifter is a separate three-level, incomplete left shifter of maximum shift count 63 that accumulates a sticky bit beyond bit 53.
choices:
  stage_radix: 4 for levels 1 and 2; level 3 selects nine multiples of 16 from 0 to 128 [outside domain]   # p.562
  stage_order: small_shift_first   # p.562
  select_encoding: partial decode with partial-shift groups [outside domain]   # p.562
  sticky_collect: true   # p.562, p.563
new_choices: none
slots: none
parameters: alignment shifter 53-bit input, 136-bit output, maximum shift count 143, three levels (p.562); normalization shifter maximum shift count 63, three levels, one pass for a normal CPA result (p.563); denormalization of a result loops back through a 56-bit hardwired right shift and a left shift by 56 minus the denorm bit position (p.566).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| normalization passes | 1 | pass | UNKNOWN / 1996 | none | normal CPA result | p.563 |
| normalization passes | 2 to 3 | passes | UNKNOWN / 1996 | none | mass cancellation from unlike-sign add, one to two extra cycles | p.563 |
errors_and_checks: The sticky bit is accumulated for bits beyond bit 53 in the normalization shifter and for bits shifted off in the alignment shifter (p.562, p.563).
conditions: The normalization shifter is not a complete shifter, so a mass-cancellation result needs one or two extra cycles, and a denormalized result needs the hardwired 56-bit right shift plus a further left shift (p.563, p.566).
evidence: "Alignment shifter" subsection and Figure 8 (p.562); "Normalization shifter" subsection (p.563); "Prenormalization/denormalization" (p.566).

### lzd_cell_tree  (role: instantiates)
mechanism: Three 63-bit leading-zero detectors calculate the number of leading zeros. The most time-critical one sits at the CPA stage after the 161-bit add and is implemented by three levels of coarse and fine circuits: a first level of sixteen 4-bit leading-zero-detect circuits, a second level of four 16-bit leading-zero-detect circuits, and a final level of one 64-bit leading-zero-detect circuit. The other two LZDs are not time-critical and are implemented by synthesis; one of them sits in the bypass unit and serves denormalized source operands. The upper 63-bit portion of the 161-bit CPA result is the input that is examined.
choices:
  block_primitive: nibble_cell   # p.563
  output_form: binary_count   # p.562, p.563
new_choices: none
slots: none
parameters: three 63-bit LZDs; levels of 16 x 4-bit, 4 x 16-bit and 1 x 64-bit circuits; input is the upper 63 bits of the 161-bit CPA result (p.562, p.563).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| LZD levels | 3 | levels | UNKNOWN / 1996 | none | CPA-stage detector, custom; the other two LZDs synthesized | p.563 |
errors_and_checks: none
conditions: The CPA-stage LZD is on a time-critical path and could not be reused for denormalized-operand prenormalization, because adding a 2:1 mux in that path would compromise timing; the bypass-unit LZD, which is not time-critical, is used instead (p.566).
evidence: "LZD (leading-zero detector)" subsection (p.563); "Prenormalization/denormalization" (p.566).

### restoring_nonrestoring  (role: instantiates)
mechanism: The FPU employs a 2-bit nonrestoring division algorithm which produces two correct mantissa bits per cycle, using most of the existing hardware.
choices:
  style: nonrestoring   # p.564
new_choices: none
slots: none
parameters: two mantissa bits per cycle (p.564).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| single-precision divide latency | "IS" as printed in the text on file | cycles | UNKNOWN / 1996 | none | normal divide | p.564 |
| double-precision divide latency | 33 | cycles | UNKNOWN / 1996 | none | normal divide | p.564 |
errors_and_checks: none
conditions: The divider reuses most of the existing FMA hardware rather than adding a dedicated array (p.564).
evidence: "Division" subsection (p.564).

## new_families
none

## space_gaps
* `booth_recoded_parallel` has no choice for a significand array narrower than the operand that is iterated over several passes; the 603e array is half a full 53 by 53 array and is double-pumped for double precision   # p.560, p.561
* `end_around_carry` has no `recirculation` value for a one-pass correction that feeds the incrementer's propagate and the CLA's group identifier back to the carry-in without a closed loop   # p.561
* `barrel_mux_tree` has no `select_encoding` value for a partial decode with partial-shift groups, and `stage_radix` cannot express a level that selects nine multiples of 16   # p.562
* `classic_fma` has no choice recording denormal handling, although the 603e prenormalizes denormalized sources through the WB normalization shifter and denormalizes results there at a stated cycle cost; the fp adder families carry `subnormal_representation` but the FMA families do not   # p.565, p.566

## open_questions
* The printed single-precision divide latency reads "IS cycles" in the document text on file, so the digits are not recoverable   # p.564
* The CPA's lookahead adder is called 88 bits wide in one sentence and "the 87-bit CLA" in the next   # p.561
* The multiplier array is called "53 by 28-bit" on p.560 and "a 54 X 28 arrangement" on p.561
* The rounding hardware in the WB stage is named but not described, so the `classic_fma` `round` slot is unset   # p.560
* The CMOS technology node, transistor count and power figures are not stated anywhere in the document
