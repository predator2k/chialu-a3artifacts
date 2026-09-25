---
handle: vangal_2006
citation: S. Vangal, Y. Hoskote, N. Borkar, A. Alvandpour, "A 6.2-GFlops Floating-Point Multiply-Accumulator With Conditional Normalization", IEEE Journal of Solid-State Circuits, vol. 41, no. 10, 2006
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp32]
authority: landmark
pages_read: 2314-2323 / 10
---

## summary
A pipelined single-precision FPMAC closes its accumulate loop in one cycle by holding the accumulated result in carry-save with delayed addition, by converting the incoming multiplier output to base 32 so every in-loop alignment is a constant 32-bit shift, and by moving normalization out of the loop into three deferred pipe stages. One "toggle detector" circuit over overlapping 3-bit windows serves both mantissa overflow prediction and leading-zero/leading-one anticipation for operands in carry-save form. The 90-nm, 2 mm2, 230K-transistor test chip sustains one FPMAC every 330 ps and delivers 6.2 GFlops at 3.1 GHz, 1.3 V, 1.2 W.

## families
### streaming_accurate_accumulator  (role: proposes)
mechanism: The incoming number in sum and carry form self-aligns rather than being aligned to the accumulator result: its mantissa is shifted left by the amount given by the five least significant exponent bits Exp[4:0], converting it to base 32 and extending the mantissa from 24 bits to 55 bits, and the exponent carried in the loop is the remaining three bits Exp[7:5]. Alignment inside the loop is then a constant 32-bit shift (SHR32 or SHL32), so no variable mantissa shifter sits in the accumulate loop. Normalization is moved outside the loop: the carry-save accumulation result is added, normalized and converted back to base 2 in the last three pipe stages, which a software-set norm_en input enables only at end of accumulation.
choices:
  approach: shifted_fixed_point_window   # p.2315
  window_bits: 55   # p.2315 (24-bit mantissa extended to 55 bits in the loop)
  in_loop_normalization: false   # p.2314, p.2315
new_choices:
  accumulation_radix: 32 — the loop's exponent radix; the incoming mantissa is pre-shifted by Exp[4:0] so every in-loop alignment is a constant 32-bit shift, and double precision would need base 64 with the mantissa extended by 63 bits   # p.2315, p.2316
  alignment_reference: incoming_operand_self_align — the incoming number aligns itself every cycle instead of being aligned to the accumulated result   # p.2315
  deferred_normalization_gating: clock_gating_plus_dynamic_sleep_transistor — the out-of-loop normalization pipeline is clock-gated and power-gated by low-Vt nMOS sleep transistors, enabled by norm_en   # p.2319
slots:
  align: bounded_align [constant SHR32/SHL32 only]   # p.2316
  lza: lza [the carry-save toggle-detector form, see new_families]   # p.2318
  cpa: sparse_prefix_hybrid   # p.2318
parameters: 32-bit IEEE 754 single-precision operands A and B; mantissa 24 bits extended to 55 bits in the loop and sign-extended to 57 bits internally; exponent comparison on 3 bits (Exp[7:5]); 12-stage pipeline with a single-cycle accumulate loop; multiplier is a four-stage Wallace tree of 4-2 adders; normalization is the last three pipe stages; three test compute modes (basic, chained, inner dot product capturing every 32nd result with implicit reset after 32 accumulations).   # p.2315, p.2316, p.2318, p.2320
results:
| metric | value | unit | technology / device | baseline | condition | page |
| frequency | 3.1 | GHz | 90 nm 7-metal dual-Vt CMOS, 2006 | none | 1.3 V | p.2321 |
| performance | 6.2 | GFlops | 90 nm, 2006 | none | 3.1 GHz, 1.3 V | p.2322 |
| power | 1.2 | W | 90 nm, 2006 | none | 3.1 GHz, 1.3 V | p.2321 |
| power per performance | 194 | mW/GFlop | 90 nm, 2006 | none | 3.1 GHz, 1.3 V | p.2322 |
| throughput | 330 | ps per FPMAC | 90 nm, 2006 | none | sustained pipelined | p.2315 |
| frequency | 1.9 | GHz | 90 nm, 2006 | none | 0.9 V, 40 C | p.2321 |
| power | 330 | mW | 90 nm, 2006 | none | 0.9 V, 1.9 GHz | p.2321 |
| frequency | 4 | GHz | 90 nm, 2006 | none | 2 V | p.2321 |
| power | 5.9 | W | 90 nm, 2006 | none | 2 V, 4 GHz | p.2321 |
| peak performance | 8 | GFlops | 90 nm, 2006 | none | 4.0 GHz, 2.0 V | p.2322 |
| estimated FPMAC power | 920 | mW | 90 nm, 2006 | none | 1.3 V, 3.1 GHz | p.2321 |
| leakage power | 340 | mW | 90 nm, 2006 | none | 1.3 V, 85 C, 26% of total | p.2321 |
| leakage power | 85 | mW | 90 nm, 2006 | none | 0.9 V, 85 C, 24% of total | p.2321 |
| die area | 2 | mm2 | 90 nm, 2006 | none | full custom, 230K transistors | p.2320 |
| FPMAC core layout area | 0.88 | mm2 (44% of total) | 90 nm, 2006 | none | core is 151K of 230K transistors (67%) | p.2320 |
| normalization pipeline device share | 28 | % of devices | 90 nm, 2006 | whole FPMAC | normalization is out of the loop | p.2319 |
| normalization unit total power reduction | 94 | % | 90 nm, 2006 | normalization pipeline always enabled | N=32, 32 ns idle | p.2322 |
| normalization unit leakage reduction | 14X | ratio | 90 nm, 2006 | normalization pipeline always enabled | N=32 | p.2322 |
| FPMAC active power saving | 24.6 | % | 90 nm, 2006 | normalization pipeline always enabled | 1.3 V, 3.1 GHz | p.2322 |
| FPMAC standby leakage reduction | 30 | % | 90 nm, 2006 | normalization pipeline always enabled | end of accumulation signalled | p.2322 |
| frequency impact of sleep transistor | 4.5 | % | 90 nm, 2006 | no sleep transistor | 56 mV worst-case virtual-ground bounce at 25% data activity | p.2319, p.2322 |
| sleep transistor area overhead | 7.4 | % | 90 nm, 2006 | none | 4500-um nMOS in 11 columns spaced 40 um | p.2319 |
| mantissa datapath width increase | 31 | bits | 90 nm, 2006 | conventional base-2 accumulate loop | wider adder and more accumulate flip-flops | p.2316 |
errors_and_checks: The four IEEE rounding modes are not implemented in this version, and denormalized operands are unsupported and raise exceptions; Invalid, Overflow and Underflow flags are generated as specified by IEEE-754 (p.2315). The LZA count can be off by one or two bit positions for the final result and requires a compensatory shift after conversion to sign-magnitude (p.2318). No fault model, detection coverage or alias rate is reported.
conditions: The design targets sequences of dependent FPMAC instructions issued every cycle and applications such as matrix multiplication where intermediate values need no normalization (p.2319). Costs are the 31-bit wider mantissa datapath in the loop, a wider adder, more flip-flops in the accumulate registers, and correspondingly more area and power (p.2316). norm_en must be asserted a minimum of four core cycles for the normalization result to complete, and for small activation rates N clock gating alone is recommended because switching the large sleep transistor can cost more than the leakage saved (p.2322). Measurements at 85 C show 3.2%-7.5% performance degradation over the voltage range against 40 C (p.2321).
evidence: Abstract; Section II with Figs. 2, 3, 10; Section III; Section IV with Fig. 13; Section V with Figs. 16, 18-21; Conclusion.

### multipath_fma  (role: instantiates)
mechanism: The accumulator mantissa loop implements four cases as concurrent paths, all control signals generated from 3-bit exponent comparisons. Path A shifts the smaller mantissa right by 32 bits and adds, when the exponents are equal or differ by one. Path B bypasses the adder and selects the larger number when the exponents differ by more than one, since the smaller mantissa would shift right by at least 64 bits. Path C, of higher priority than B, handles more than 31 leading zeros or ones in the accumulated result: the feedback mantissa shifts left by 32 bits, the incoming mantissa shifts right by 32 bits when the feedback exponent is larger by 2, and a second 4-2 adder performs the addition. Path D selects the incoming mantissa when the feedback mantissa is zero.
choices:
  path_count: 4   # p.2316
  path_select_criterion: both   # p.2316 (3-bit exponent comparison for A and B, LZA leading-zero/one detection for C)
new_choices:
  zero_operand_path: early_zero_detect_on_carry_save — a fourth path selects the incoming mantissa when an early zero detector circuit finds the accumulated result zero in carry-save form   # p.2316
slots:
  align: bounded_align [SHR32, SHL32]   # p.2316
  lza: lza [detects more than 31 leading zeros or ones in the accumulated result]   # p.2316, p.2318
  cpa: sparse_prefix_hybrid   # p.2318
  multiplier: UNKNOWN   # p.2315 (only a four-stage Wallace tree of 4-2 adders compressing the partial product bits to a sum and carry pair is stated)
parameters: four concurrent paths; two 4-2 adder arrays in the loop, each with its own overflow prediction (Ovf1, Ovf2); the exponent loop mirrors the four mantissa cases, with control signals computed and re-timed to the previous pipe stage, removing three logic stages.   # p.2316
results:
| metric | value | unit | technology / device | baseline | condition | page |
| accumulation critical path | 9 | FO4 | 90 nm, 2006 | none | four concurrent paths, control re-timed one stage earlier, no overflow prediction | p.2316 |
| total latency of a state-of-art FPU | 100 | FO4 | UNKNOWN | none | quoted from [8] as context | p.2314 |
errors_and_checks: Path C is necessary to handle non-commutative input data streams correctly and to avoid precision loss; its second 4-2 adder can be eliminated when the additions on the input stream are commutative, an assumption general purpose FPUs often make (p.2316).
conditions: Path D is required because the feedback exponent may be non-zero when the feedback mantissa is zero, which would shift the incoming mantissa incorrectly (p.2316).
evidence: Section II-A, Figs. 4, 5, 6, Table I.

### carry_save_datapath  (role: instantiates)
mechanism: The accumulator pipe stage retains the multiplier output in carry-save format and uses an array of 4-2 carry-save adders to accumulate in that intermediate format, which removes the carry-propagate adder from the critical path (delayed addition). The sum and carry vectors are assimilated once, after the loop, by the 57-bit dual adder core, with the carry vector shifted left by one bit before the addition. Each 4-2 adder array carries its own overflow prediction: the 55-bit operands are sign-extended by one bit and the three most significant bits of both compressor output vectors are examined by the toggle detector, which triggers a right shift of the addition result with the exponent incremented accordingly.
choices:
  compressor: 4_2   # p.2315, p.2316
  carry_overflow_correction: true   # p.2316, p.2317
new_choices:
  overflow_prediction: toggle_detect_3bit_window — mantissa overflow is predicted from the three most significant bits of both carry-save vectors without performing the addition   # p.2317
slots:
  assimilator: sparse_prefix_hybrid   # p.2318
parameters: internal accumulator data width sign-extended to 57 bits; propagate, generate, zero, xnor, nand and or signals formed for each of the three most significant bit pairs; 27 possible 3-bit patterns, of which 18 imply overflow.   # p.2317, p.2318
results:
| metric | value | unit | technology / device | baseline | condition | page |
| accumulator critical path | 15 | FO4 | 90 nm, 2006 | 9 FO4 without overflow prediction | at-speed overflow prediction and recovery | p.2318, p.2322 |
| overflow prediction and recovery cost | six | logic levels | 90 nm, 2006 | none | added to the accumulator critical path | p.2318 |
errors_and_checks: The prediction is conservative: of the 18 patterns that imply overflow, 6 are pessimistic because the transition may occur one bit position lower when no carry propagates into that position, so the logic may incorrectly predict overflow in 6 of 18 cases, and the result is still large in those cases because the transition is off by only one bit position (p.2317). One further sign-extension bit, taking the internal accumulator width to 57 bits, keeps the conservative right shift from losing precision (p.2318).
conditions: Overflow during mantissa addition and the subsequent recovery are handled on the fly inside the loop (p.2316).
evidence: Section II-A, Section II-B, Figs. 7, 8.

### sparse_prefix_hybrid  (role: instantiates)
mechanism: The deferred addition uses a 57-bit sparse-tree dual adder core that divides the carry-merge tree into a critical and a non-critical section. Each adder core is composed of a critical sparse tree generating 1 in 16 carries, with non-critical side paths generating conditional 1 in 4 carries and 4-bit conditional sums. The carry generated by the sparse tree selects between the conditional carries to deliver 1 in 4 carries, and those carries in turn select between the conditional sums to generate the final sum. Two identical adders with preconditioned inputs compute two results in parallel and the appropriate result is chosen based on its sign, with the LZA and the LZC operating in parallel with the dual adder.
choices:
  log2_sparsity: 4 [outside domain]   # p.2319 (1 in 16 carries; the declared domain is 1..3)
  sum_block_style: conditional_sum   # p.2319
new_choices: none
slots:
  sum_block: conditional_sum [base_block_width=4]   # p.2319
parameters: 57-bit adder core, two identical cores in the dual adder.   # p.2318, p.2319
results:
| metric | value | unit | technology / device | baseline | condition | page |
| adder core transistor count | 4200 | transistors | 90 nm, 2006 | none | one 57-bit core | p.2319 |
errors_and_checks: none
conditions: The inter-stage wiring density, interconnect length and generate/propagate fan-outs all show significant reduction against an equivalent Kogge-Stone adder, a comparison the paper attributes to [15] and reports without numbers (p.2319).
evidence: Section III, Fig. 11.

## new_families
### carry_save_toggle_detector  (domain: shift: bit counting, closest: lzd_cell_tree, why_not: the bit-counting families count leading zeros of one assimilated binary word, whereas this circuit anticipates a bit-pattern transition in the unformed sum of a sum/carry pair and serves overflow prediction as well)
mechanism: One toggle circuit examines a window of three bits of both input operands at a time and predicts a 0-to-1 or 1-to-0 transition in the corresponding window of the true sum without performing the addition, using per-bit-pair propagate, generate, zero, xnor, nand and or signals. Applied to the three most significant bits it predicts mantissa overflow. Arrayed 57 times over overlapping groups of three bits it produces a toggle vector, and counting that vector from the MSB down to the first observed transition gives the number of leading zeros or leading ones. The anticipation holds irrespective of the sign of the result or the relative magnitudes of the operands, and applies to 2's complement as well as carry-save operands.
choices: inspection_window_bits: 3 (the design fixes 3); prediction_target: enum['mantissa_overflow', 'leading_zero_one_anticipation']; operand_representation: enum['carry_save', 'twos_complement']; position_correction: enum['compensatory_shift_after_sign_magnitude_conversion']
results:
| metric | value | unit | technology / device | baseline | condition | page |
| toggle circuit instances | 57 | instances | 90 nm, 2006 | none | overlapping groups of three bits | p.2318 |
| anticipation error | one or two | bit positions | 90 nm, 2006 | none | count processed by the fast LZC of [11]; corrected by a compensatory shift | p.2318 |
| false overflow prediction | 6 of 18 | patterns | 90 nm, 2006 | none | pessimistic patterns where no carry reaches the inspected position | p.2317 |
evidence: p.2317, p.2318, Figs. 7, 8, 9.

## space_gaps
* `streaming_accurate_accumulator` has no choice for the accumulation radix, which here is base 32 and sets both the constant shift amount and the in-loop mantissa width, and which becomes base 64 for double precision (p.2315, p.2316).
* `streaming_accurate_accumulator` has no choice for whether the incoming operand self-aligns or is aligned to the accumulated result (p.2315).
* `streaming_accurate_accumulator` has no choice for power-gating the deferred normalization stage, which this design enables from a software-set norm_en input using clock gating plus nMOS sleep transistors (p.2319, p.2322).
* `sparse_prefix_hybrid.log2_sparsity` stops at 3, while this adder's critical tree generates 1 in 16 carries (p.2319).
* The `lza` slot filler carries no declared choices, so the operand representation it accepts (carry-save versus assimilated 2's complement) and its position-correction method cannot be recorded against it (p.2318).
* `multipath_fma.path_select_criterion` has no value for a zero-operand detect, which selects path D here (p.2316).
* No family choice records that a design implements no IEEE rounding mode and raises an exception on denormalized operands (p.2315).

## open_questions
* The two quantities the 57-bit dual adder core computes in parallel are lost from the extracted text; the document states only that the inputs of two identical adders are preconditioned and that the appropriate result is chosen based on its sign (p.2318).
* The partial-product generation of the multiplier is not stated; the document gives only four Wallace tree stages of 4-2 adders compressing the partial product bits to a sum and carry pair, so the multiplier family cannot be fixed (p.2315).
* The normalization shifter structure and the treatment of the final result's low bits are not described (p.2315, p.2318).
* Table I (accumulator algorithm summary) and Table II (FPMAC compute modes) did not extract, so only the prose statements of the four paths and the three compute modes are recorded (p.2317, p.2320).
* The measurement temperature printed as "40 C" may carry a sign lost in extraction; the value is copied as printed (p.2321).
