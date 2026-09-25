---
handle: zhang_2018
citation: H. Zhang, H. J. Lee, S.-B. Ko, "Efficient Fixed/Floating-Point Merged Mixed-Precision Multiply-Accumulate Unit for Deep Learning Processors", ISCAS 2018
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp16, fp32, int8, int32]
authority: incremental
pages_read: 5 / 5
---

## summary
The paper proposes a three-stage pipelined multiply-accumulate unit that performs either one 16-bit half-precision multiplication accumulated into a 32-bit single-precision accumulator or two parallel 8-bit fixed-point multiplications accumulated into a 32-bit fixed-point accumulator, selected by one control signal float. The half-precision mantissa product is computed with the Karatsuba algorithm, so the two 8-bit sub-multipliers it needs are the same two 8-bit multipliers the fixed-point mode uses. Synthesized in STM-90nm, the merged unit has 4.6% more area and 3.5% more power than a floating-point-only multiply-accumulate unit of the same floating-point functionality.

## families

### mixed_precision_cascade_fma  (role: instantiates)
mechanism: In FLP mode the mantissas mantafp and mantbfp go to the merged multiplier, which returns the product in carry-save form; 22 bits are enough for the half-precision product, and the products are extended to 32 bits by padding zeros to the right. The single-precision accumulator is inverted when eopflp = 1 and aligned by a 58-bit shifter, and it is placed two bits to the left of the carry-save products so accumulation cannot overflow and the accumulator only shifts right. The low 32 bits of the aligned accumulator join the carry-save products in a carry-propagate adder, the high part is incremented, and the adder's carry-out selects the incremented value. An LZA+LZC gives the normalization shift amount; the last stage normalizes and rounds.
choices:
  exact_product_preserved: true   # p.2
  two_term_expansion_output: false   # p.2
new_choices:
  accumulator_left_offset_bits: 2 — the accumulator sits two bits to the left of the carry-save product so alignment is a right shift only   # p.2
slots:
  align: full_align   # p.2
  lza: lza   # p.2
  multiplier: recursive_karatsuba [split_kind=rectangular, recursion_depth=1]   # p.3
parameters: half-precision operands (1-bit s, 5-bit E, 10-bit m, bias 15), single-precision accumulator (1-bit s, 8-bit E, 23-bit m, bias 127), 22-bit half-precision product padded to 32 bits, 58-bit align shifter, exponents converted by the half/single bias difference, 3 pipeline stages, 3-cycle latency, one new operation per clock cycle   # p.1, p.2, p.4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 3 | cycles | STM-90nm, 2018 | Floating-Point MAC: 3 cycles | floating-point mode | p.4 |
| throughput | 1.25 | GOPS | STM-90nm, 2018 | Floating-Point MAC: 1.25 GOPS | floating-point mode | p.4 |
| worst delay | 0.8 | ns | STM-90nm, 2018 | Floating-Point MAC: 0.8 ns | whole design including pipeline registers | p.4 |
| worst delay | 17.78 | FO4 | STM-90nm, 2018 | Floating-Point MAC: 17.78 FO4 | 1 FO4 ≈ 45 ps | p.4 |
| area | 42710.90 | μm2 | STM-90nm, 2018 | Floating-Point MAC: 40817.54 μm2, +4.6% | whole design | p.4 |
| area | 9707 | NAND2 | STM-90nm, 2018 | Floating-Point MAC: 9276 NAND2 | 1 NAND2 ≈ 4.4 μm2 | p.4 |
| power | 14.07 | mW | STM-90nm, 2018 | Floating-Point MAC: 13.59 mW, +3.5% | 0.8 ns clock period | p.4 |
errors_and_checks: accumulation to higher precision is stated to avoid data loss due to rounding (p.1); the accumulation result is normalized and rounded to single-precision mantissa bit-length in the last stage, with a sticky bit stk and a comp signal produced during alignment (p.2); no rounding mode, ulp bound or measured error is reported; functionality is verified by simulation with extensive testing vectors (p.3).
conditions: floating-point operation requires all three pipeline stages while fixed-point operation requires the first two (p.2); the critical path is in the first pipeline stage, where the multiplier is, and the first stage also has the largest area because the multiplier and the alignment shifter are there (p.3); the design is fully pipelined and a new operation can start every clock cycle (p.4); area and power fall as the delay constraint grows, and the smallest-delay point is the one reported (p.4).
evidence: Fig. 1, Section III-A, Table II, Fig. 4.

### integer_mac  (role: instantiates)
mechanism: In FIX mode A and B each carry two 8-bit two's complement numbers Ah, Al and Bh, Bl, and the unit computes Ah × Bh + Al × Bl + accumulator. mult8_1 and mult8_2 take one 8-bit pair each, (4,2)CSA1 adds the two products, and that result is sign extended to 32 bits to form the multiplier output. Because the fixed-point numbers are in two's complement format, the accumulator is not inverted and no alignment is performed; the 32-bit accumulator is placed directly at the low 32-bit position, and the second-stage complementer is not required. The result leaves at the fixed-point output register after two pipeline stages.
choices:
  array_style: composable_submultiplier   # p.3
  element_op: product   # p.2
  accumulation_mode: sum_together   # p.2
  accumulator_width_bits: 32   # p.2
new_choices: none
slots:
  mul: booth_recoded_parallel [booth_radix=4]   # p.3
  reduction: csa_tree   # p.3
parameters: two 8-bit by 8-bit fixed-point multiplications per operation, the two 16-bit inputs A and B each filled with two 8-bit operands, 32-bit two's complement accumulator, 2 pipeline stages, 2-cycle latency, one new operation per clock cycle   # p.2, p.4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 2 | cycles | STM-90nm, 2018 | Fixed-Point MAC: 2 cycles | fixed-point mode | p.4 |
| throughput | 2.50 | GOPS | STM-90nm, 2018 | Fixed-Point MAC: 1.43 GOPS | fixed-point mode | p.4 |
errors_and_checks: the 8-bit products accumulate into a 32-bit fixed-point accumulator, which is stated to avoid data loss due to rounding (p.1, p.2); no saturation, overflow or error behaviour is reported.
conditions: fixed-point operation uses only the first two pipeline stages and needs no alignment and no complementer (p.2); the area overhead of the merged unit over a floating-point-only unit is attributed to the multiplexers added to support fixed-point operations (p.4).
evidence: Section III-B, Section III-C, Fig. 2, Table II.

### recursive_karatsuba  (role: instantiates)
mechanism: mantafp = mah · 2^8 + mal and mantbfp = mbh · 2^8 + mbl, with mah and mbh the top 3 bits and mal and mbl the low 8 bits of the 11-bit mantissas. Three products replace four: mah × mbh in mult3, mal × mbl in mult8_2, and the difference product in mult8_1. The last term of equation (2) is rewritten as (A1 − A2) × (B2 − B1) so its subtraction becomes an addition and reuses (4,2)CSA1, which the fixed-point mode already needs. (4,2)CSA2 accumulates mah × mbh and mal × mbl, (4,2)CSA1 combines that with the difference product to give mah × mbl + mal × mbh, and (4,2)CSA3 combines the three terms after left shifts of 8 and 16 bits into the carry-save product.
choices:
  recursion_depth: 1   # p.3
  split_kind: rectangular   # p.3
  base_multiplier: booth_tree   # p.3
new_choices:
  middle_term_form: (A1 − A2) × (B2 − B1) — the difference product's operand order is flipped so the recombination is an addition rather than a subtraction   # p.3
slots:
  reduction: compressor_4_2_tree   # p.3
parameters: 11-bit by 11-bit mantissa product from one 3-bit by 3-bit multiplier (mult3) and two 8-bit by 8-bit multipliers (mult8_1, mult8_2), split at n = 8; partial terms shifted left by 8 and 16 bits; 32-bit carry-save output   # p.3
results: none
errors_and_checks: none
conditions: only one 3 × 3 multiplier is added to the two 8-bit multipliers to generate the half-precision product (p.3); mult3 is used only in FLP mode and is therefore unsigned (p.3); the algorithm requires additional adders (p.2).
evidence: Section II-B, equations (1)-(3), Section III-C, Fig. 2.

### booth_recoded_parallel  (role: instantiates)
mechanism: mult8_1 and mult8_2 are modified Booth multipliers whose partial products are ±multiplicand or ±2×multiplicand. One partial-product generate logic serves both cases: the multiplicand is extended with zero in the unsigned case and sign extended in the signed case, handled by the control signal float. The S bit, which is the complement bit for a negative partial product, is used in common, and an E bit, which determines whether the partial product and the multiplicand have the same sign, is generated for the signed case; float chooses S or E when extending ±1× or ±2×multiplicand. The unsigned case has one more partial product than the signed case, but at 8 bits the last multiplier group's top two bits are always 00, so that partial product needs no selector.
choices:
  booth_radix: 4   # p.3
  negative_pp_encoding: ones_complement_plus_neg_bit   # p.3
new_choices:
  signedness_control: float — one control signal switches the same partial-product generate logic between the unsigned operation of FLP mode and the signed operation of FIX mode   # p.3
slots: none
parameters: two 8-bit by 8-bit multipliers with 16-bit carry-save outputs; the 3-bit by 3-bit multiplier mult3 is unsigned and is not Booth recoded   # p.3
results: none
errors_and_checks: none
conditions: mult8_1 and mult8_2 are used in both modes, so an unsigned multiplier is required in FLP mode and a signed multiplier in FIX mode (p.3); in the signed case float sets the last partial product to all zeros (p.3).
evidence: Section III-C, Fig. 2, Fig. 3.

## new_families

### fixed_floating_point_merged_mac  (domain: dot, closest: multi_precision_simd_fma, why_not: multi_precision_simd_fma splits one datapath across floating-point precisions, whereas this unit shares one multiplier, one accumulation path and one accumulator between a floating-point multiply-accumulate and two packed fixed-point multiply-accumulates selected at run time.)
mechanism: The control signal float selects between a 16-bit half-precision multiplication accumulated into a 32-bit single-precision accumulator and two 8-bit fixed-point multiplications accumulated into a 32-bit fixed-point accumulator. The Karatsuba decomposition of the half-precision mantissa multiplier yields two 8-bit multipliers, and those same two multipliers perform the two parallel fixed-point multiplications, so only a 3 × 3 multiplier is added. float also switches the Booth partial-product generation between unsigned and signed, selects the 32-bit sign-extended fixed-point product instead of the shifted Karatsuba recombination, and in fixed-point mode bypasses the accumulator inversion, the alignment shifter and the complementer. The fixed-point result leaves after two pipeline stages and the floating-point result after three.
choices: submultiplier_decomposition: enum['karatsuba', 'direct_split']; fixed_point_lane_count: 1..4 by 1; fixed_point_accumulator_width_bits: 16..48 by 8; shared_partial_product_signedness: bool; bypass_alignment_in_fixed_mode: bool
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 42710.90 | μm2 | STM-90nm, 2018 | FIX+FLP design (the two single-mode units combined): -21% | same functionality as the two single-mode units | p.4 |
| power | 14.07 | mW | STM-90nm, 2018 | FIX+FLP design (the two single-mode units combined): -30.4% | 0.8 ns clock period | p.4 |
| stage 1 delay | 0.74 | ns | STM-90nm, 2018 | none | combinational logic of pipeline stage 1 | p.3 |
| stage 1 area | 20003.75 | μm2 | STM-90nm, 2018 | none | combinational logic of pipeline stage 1 | p.3 |
| stage 1 power | 7.5 | mW | STM-90nm, 2018 | none | combinational logic of pipeline stage 1 | p.3 |
| stage 2 delay | 0.70 | ns | STM-90nm, 2018 | none | combinational logic of pipeline stage 2 | p.3 |
| stage 2 area | 7958.69 | μm2 | STM-90nm, 2018 | none | combinational logic of pipeline stage 2 | p.3 |
| stage 2 power | 1.87 | mW | STM-90nm, 2018 | none | combinational logic of pipeline stage 2 | p.3 |
| stage 3 delay | 0.68 | ns | STM-90nm, 2018 | none | combinational logic of pipeline stage 3 | p.3 |
| stage 3 area | 4227.95 | μm2 | STM-90nm, 2018 | none | combinational logic of pipeline stage 3 | p.3 |
| stage 3 power | 0.63 | mW | STM-90nm, 2018 | none | combinational logic of pipeline stage 3 | p.3 |
evidence: Fig. 1, Fig. 2, Section III, Table I, Table II, Section IV.

## space_gaps
* `recursive_karatsuba.split_kind` has no value for a two-way split into unequal parts; the 11-bit mantissa is split into a 3-bit high part and an 8-bit low part   # p.3
* `booth_recoded_parallel` has no choice for run-time signedness selection, which one control signal provides here over a shared partial-product generate logic   # p.3
* no `dot` family carries a slot or choice for a multiplier shared between a floating-point mantissa product and packed fixed-point products   # p.3
* `integer_mac` has no choice for a fixed-point mode that bypasses the alignment shifter and the complementer of the floating-point path   # p.2

## open_questions
* Section III-C first states that (mah − mal) × (mbh − mbl) is calculated by mult8_1 and mah × mbh by mult3, then states that mult3 calculates (mah − mal) × (mbl − mbh); which multiplier forms the difference product is not settled   # p.3
* Fig. 1 labels the floating-point output mantflp with width 10 and expflp with width 5, while Section III-A states the result is rounded to single-precision mantissa bit-length and combined into IEEE 754 single-precision format   # p.2
* The rounding mode of the final rounding stage is not stated   # p.2
* The carry-propagate adder, the incrementer, the normalization shifter and the rounding circuit are named but their structures are not given, so the corresponding slots stay open   # p.2
* The venue is not printed in the document text; only the year 2018 appears, in the IEEE copyright line at the foot of each page   # p.1
