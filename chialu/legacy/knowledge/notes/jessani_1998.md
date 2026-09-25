---
handle: jessani_1998
citation: R. M. Jessani, M. Putrino, "Comparison of Single- and Dual-Pass Multiply-Add Fused Floating-Point Units", IEEE Transactions on Computers, vol. 47, no. 9, 1998
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp32, fp64]
authority: incremental
pages_read: 927-937 / 11
---

## summary
The paper compares a single-pass and a dual-pass multiply array inside a multiply-add fused (MAF) FPU, using the PowerPC 604e and PowerPC 603e implementations built in the same technology. The dual-pass array halves the Booth recoders, the Booth multiplexors and the CSA groups by splitting the 53-bit C operand mantissa into a 28-bit lower part and a 25-bit upper part and feeding the first pass's sum and carry back into free 4:2 CSA inputs. Seven design complications of that feedback are enumerated, in the Wallace tree, the B alignment shifter, the sticky logic and the final adder, together with the area saved and the SPECfp95 lost.

## families
### classic_fma  (role: compares)
mechanism: Single-pass MAF FPU of the PowerPC 604e. Three pipelined stages carry the multiply (53-bit x 53-bit radix-4 Booth array plus the B alignment shift), the add (AC + aligned B, with leading zero detection for the normalize shift count), and the normalize/round. T = (A x C) + B, and instructions with fewer than three operands force constants into the unused ones, C = 1.0 for T = A + B. The B mantissa is positioned 56 bits left of the AC product's binary point and right-shifted by shift count = exp(AC) - exp(B) + 56, over a 161-bit range around the 106-bit product. The aligned B enters through a 3:2 CSA level, and the 161-bit sum is formed in one's-complement with end-around-carry adjustment for effective subtraction.
choices:
  subsume_fp_add: true   # p.927
  negation_handling: end_around_carry   # p.933
new_choices:
  multiply_array_passes: 1 — passes of the multiplier operand through the array per double-precision product   # p.930
slots:
  align: full_align [53-bit input, 161-bit shift range, B positioned 56 bits left of the AC binary point]   # p.930
  multiplier: booth_recoded_parallel [booth_radix=4, 27 partial products]   # pp.928-931
  cpa: carry_select [duplication=shared_add_one, select_source=rippled_block_carries; 107-bit carry_lookahead low block, 54-bit prefix_and_incrementer upper block, carry-select multiplexor on the upper aligned-B bits]   # p.934
parameters: design class single-pass (PowerPC 604e); A and C mantissas 53 bits; AC product 106 bits with two bits left of the binary point; aligned B range 161 bits; B alignment shifter 53-bit input; final adder equivalent to 161 bits; three pipeline stages; one-cycle throughput for every instruction class   # pp.927-930, 934, 936
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
| FPU area | 19.5 | mm2 | 0.5mm CMOS [as printed] / PowerPC 604e | none | includes the floating-point registers; year 1998 | p.936 |
| multiply array area | 5.1 | mm2 | 0.5mm CMOS [as printed] / PowerPC 604e | none | year 1998 | p.936 |
| SPECfp95 (estimated) | 6.6 | score | 0.5mm CMOS [as printed] / 200 MHz PowerPC 604e, 1 MB L2 at 66 MHz, 66 MHz memory bus | none | estimate; year 1998 | p.936 |
| double-precision multiply throughput | 1 | cycle per instruction | 0.5mm CMOS [as printed] / PowerPC 604e | none | single-pass array; year 1998 | p.936 |
errors_and_checks: IEEE-754 single and double precision. The two extra bits between the B operand mantissa and the AC product keep the guard and round bits zero and drop the AC product into the sticky calculation for zero or negative shift counts, which the paper states is what makes the round function match the IEEE standard (p.930). The sticky bit is the logical OR of all bits beyond the 53rd bit of AC + B, plus every B bit shifted beyond bit 161 (p.935). No fault model or detection scheme is discussed.
conditions: The full array's Booth recoder and CSA count is called high area occupancy, which may not be desirable for a microprocessor targeted at the portable computer market (p.931). The single pass buys one-cycle throughput on double-precision multiplies (p.936).
evidence: Sections 1-3 and 6; Figs. 1, 4, 5, 10, 11, 14; Section 9 areas; Section 8 SPECfp95.

### booth_recoded_parallel  (role: instantiates)
mechanism: Full 53-bit x 53-bit array of the PowerPC 604e. Radix-4 Booth recoding of the C operand mantissa drives 27 Booth recoders and 27 5:1 Booth multiplexors that select 0, A, A shifted left one bit, A inverted, or A shifted left one bit and inverted. The hot-one of a negative partial product is carried as b'01' concatenated to the low end of the next partial product, which sits two bit positions left; pp26 is always positive because b'0' is concatenated to the multiplier's most significant bit. Reduced sign extension gives a 57-bit pp0 and 56-bit pp1 through pp26. Thirteen groups of 4:2 CSAs in four levels reduce the rows to sum and carry, and a 3:2 CSA level adds the aligned B mantissa.
choices:
  booth_radix: 4   # p.928
  negative_pp_encoding: ones_complement_plus_neg_bit   # pp.928-929
  sign_extension: modified partial-products in a reduced left edge banded matrix, 3 bits left of bit 0 for pp0 and 2 bits for pp1 through pp27 [outside domain]   # pp.929, 935
new_choices: none
slots:
  reduction: compressor_4_2_tree [13 CSA groups in four levels, 7/3/2/1, one group being 3:2 CSAs]   # pp.930-931
parameters: 27 Booth recoders; 27 5:1 Booth multiplexors; 27 partial products; 57-bit pp0 and 56-bit pp1..pp26; 106-bit product; 13 CSA groups in four 4:2 levels; one further 3:2 CSA level for the aligned B   # pp.929-931
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
| multiply array area | 5.1 | mm2 | 0.5mm CMOS [as printed] / PowerPC 604e | none | year 1998 | p.936 |
errors_and_checks: none
conditions: 4:2 CSAs were chosen over the 3:2, 7:3 and 5:5:4 CSAs for availability of circuit resources and the dependence of design-time on schedule, while still meeting the frequency goals, and the paper notes the choice has been evaluated against techniques with faster partial-product reduction times (p.930). The CPA was chosen over an arrival-profile-driven final adder because every signal feeding it comes from a latch output and so has the same arrival time (p.934).
evidence: Sections 3 and 4; Table 1; Figs. 2, 3, 5.

### classic_fma  (role: compares)
mechanism: Dual-pass MAF FPU of the PowerPC 603e. The same three stages run, with the multiply stage and the add stage exercised twice for a double-precision multiply. The 161-bit aligned B mantissa is partitioned, the first pass taking its low 26 bits and the second pass the upper 135 bits, so the B alignment shifter has a 53-bit input and a 136-bit output and the alignment constant is 30 (56-26) in the first pass and 56 in the second. The 3:2 CSA group that injects the aligned B sits either in the multiply stage or in the add stage. The 161-bit adder becomes a 136-bit adder, because the low 26 result bits are latched in the first add cycle and incremented in the second to apply the end-around carry.
choices:
  subsume_fp_add: true   # p.927
  negation_handling: end_around_carry   # pp.933, 936
new_choices:
  multiply_array_passes: 2 — passes of the multiplier operand through the reduced array per double-precision product, 1 for single precision   # p.931
  aligned_addend_partition_bits: 26 low in pass 1 / 135 upper in pass 2 — how the 161-bit aligned B mantissa is split across the passes   # p.935
  alignment_constant_per_pass: 30 in pass 1, 56 in pass 2 — the offset constant added to the shift count in each pass   # p.933
  addend_csa_stage_placement: multiply stage or add stage — where the 3:2 CSA group that injects the aligned B mantissa sits   # p.932
slots:
  align: full_align [53-bit input, 136-bit output, 161-bit range spanned across two passes]   # pp.933, 935
  multiplier: booth_recoded_parallel [booth_radix=4, 14 partial products per pass]   # pp.931-932
  cpa: carry_select [duplication=shared_add_one, select_source=rippled_block_carries; 26-bit prefix_and_incrementer on the latched first-pass low bits feeding the carry-in of an 81-bit carry_lookahead block, then a 54-bit prefix_and_incrementer with a carry-select multiplexor]   # p.934
parameters: design class dual-pass (PowerPC 603e); C operand mantissa split 28 low / 25 high bits with b'000' concatenated to the most significant bit; 14 partial products per pass; first pass produces an 82-bit value whose upper 56 bits are fed back and whose lower 26 bits are latched; B alignment shifter 53-bit in / 136-bit out; adder 26-bit incrementer + 81-bit CLA + 54-bit incrementer; one-cycle throughput for non-multiply and single-precision multiply instructions, two-cycle throughput for double-precision multiply instructions   # pp.931-936
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
| FPU area | 11.7 | mm2 | 0.5mm CMOS [as printed] / PowerPC 603e | none | includes the floating-point registers; year 1998 | p.936 |
| FPU area relative to single-pass | about 60 | percent | 0.5mm CMOS [as printed] / PowerPC 603e | PowerPC 604e single-pass FPU, 19.5 mm2 | year 1998 | p.936 |
| SPECfp95 (estimated) | 3.7 | score | 0.5mm CMOS [as printed] / 200 MHz PowerPC 603e system | PowerPC 604e single-pass, 6.6 | similarly equipped system; estimate; year 1998 | p.936 |
| double-precision multiply throughput | 2 | cycles per instruction | 0.5mm CMOS [as printed] / PowerPC 603e | PowerPC 604e, 1 cycle | dual pass; year 1998 | p.936 |
| dispatch stall | 1 | cycle | 0.5mm CMOS [as printed] / PowerPC 603e | none | the first multiply-stage pass of a dual-pass instruction; year 1998 | p.936 |
errors_and_checks: The B bits that fall into the sticky bit during the first pass are fed back and logically ORed into the sticky bit for the second pass (p.935). The 26-bit incrementer in the second add cycle implements the end-around carry addition and produces the proper sign-magnitude result (p.936). The lower 26 bits produced in the first pass are the low 26 bits of the 161-bit AC + B value before normalization and rounding, and the second pass does not modify them (p.935).
conditions: The dual-pass array targets low cost, low power and the portable computer market, and is stated to apply as long as the associated reduction in performance is acceptable (p.927). Single-precision multiplication needs 26 bits of the C operand mantissa and stays single-pass, ignoring the lower 27 bits and needing no additional multiplexing in the Wallace tree (p.931). The saving costs control logic and multiplexing in seven named places, which are the sum and carry feedback path, the hot-one of pp13, the 3-bit against 2-bit sign extension shared by pp0 and pp14, the 82-bit first-pass value, the per-pass shift counts of the B alignment shifter, the sticky logic, and the split CPA (pp.934-936). One 4:2 CSA level fewer in the Wallace tree may allow higher attainable frequencies of operation (p.932).
evidence: Sections 4 to 9; Figs. 6, 7, 8, 9, 11, 13, 15.

### booth_recoded_parallel  (role: instantiates)
mechanism: Half-size 53-bit x 53-bit array of the PowerPC 603e. The C operand mantissa is divided into a 28-bit lower part, which generates 14 partial products added by four groups of 4:2 CSAs in the first level with two inputs of those CSAs left free, and a 25-bit upper part, which generates 13 partial products added by the first level together with the sum and carry results of the first pass. A b'000' concatenated to the multiplier's most significant bit adds a zero pp27 and equalizes both passes at 14 partial products. The hot-one of pp13 is saved and fed back to be positioned with pp14. Two extra CSAs in the first CSA group and a multiplexor on the first three sign-extension bits keep the shared pp0 and pp14 dataflow bit-aligned.
choices:
  booth_radix: 4   # p.931
  negative_pp_encoding: ones_complement_plus_neg_bit   # pp.928-929
  sign_extension: modified partial-products in a reduced left edge banded matrix, 3 bits left of bit 0 for pp0 and 2 bits for pp1 through pp27, selected per pass by a multiplexor [outside domain]   # pp.929, 935
new_choices:
  multiply_array_passes: 2 — passes of the multiplier operand through the reduced array per double-precision product   # p.931
  multiplier_operand_split_bits: 28 low / 25 high, with b'000' concatenated to the most significant bit — how the multiplier operand is divided between the passes   # p.931
  first_pass_feedback: sum and carry into two free 4:2 CSA tree inputs, the upper 56 bits fed back and the lower 26 bits latched — how a pass's partial result re-enters the tree   # pp.934-935
  deferred_hot_one: the hot-one of pp13 saved in the first pass and re-injected with pp14 in the second — where a split array places a negative row's hot-one   # p.934
slots:
  reduction: compressor_4_2_tree [7 CSA groups; the tree admits 16 partial products per cycle, of which 14 are used]   # pp.932, 934
parameters: 14 Booth recoders; 14 Booth multiplexors; 14 partial products per pass; 7 CSA groups; one 4:2 CSA level fewer than the full array; 82-bit first-pass value; 28 CSAs avoided by feeding back only the upper 56 bits; 2 extra CSAs added in the first group of the first level   # pp.932, 934-935
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
| multiply array area | 2.5 | mm2 | 0.5mm CMOS [as printed] / PowerPC 603e | none | year 1998 | p.936 |
| multiply array area relative to single-pass | about 50 | percent | 0.5mm CMOS [as printed] / PowerPC 603e | PowerPC 604e single-pass array, 5.1 mm2 | year 1998 | p.936 |
| Booth recoders | 14 | count | 0.5mm CMOS [as printed] / PowerPC 603e | 27 in the single-pass array | double precision; year 1998 | p.932 |
| Booth multiplexors | 14 | count | 0.5mm CMOS [as printed] / PowerPC 603e | 27 in the single-pass array | double precision; year 1998 | p.932 |
| CSA groups | 7 | count | 0.5mm CMOS [as printed] / PowerPC 603e | 13 in the single-pass array | double precision; year 1998 | p.932 |
errors_and_checks: none
conditions: Single-precision multiplication uses 26 bits of the C operand mantissa, which is the 24-bit mantissa with b'00' concatenated at the least-significant bit, and completes in one pass with no additional multiplexing in the Wallace tree (p.931). Double precision needs two passes plus the feedback multiplexing and the added control logic (pp.931, 934).
evidence: Sections 4 and 7; Figs. 6, 7, 12.

## new_families
### multipass_folded_pp_array  (domain: mul: integer multipliers, closest: booth_recoded_parallel, why_not: booth_recoded_parallel reduces every partial-product row of one product in a single pass and exposes no choice for splitting the multiplier operand across cycles or for returning a pass's sum and carry to the tree)
mechanism: The partial-product array is built for a fraction of the multiplier operand's bits and reused over several cycles. The multiplier operand is divided into parts, here 28 low bits and 25 high bits with b'000' concatenated to the most significant bit so that both passes carry 14 partial products. The first pass's sum and carry re-enter the reduction tree through inputs left free in its first level, the low result bits that later passes cannot change are latched out instead of fed back, and a negative row's hot-one is saved for re-injection at its full-array position in the next pass. Rows shared between passes need matching per-bit dataflow, so extra CSAs and sign-extension multiplexors are added.
choices: passes: 2..4; multiplier_split_bits: the per-pass share of multiplier bits; pp_rows_per_pass: 1..32; feedback_target: enum['free_csa_tree_inputs', 'separate_csa_level']; feedback_width_bits: the upper bits returned, against the low bits latched out; deferred_hot_one: bool; shared_row_sign_extension_mux: bool
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
| multiply array area | 2.5 | mm2 | 0.5mm CMOS [as printed] / PowerPC 603e | PowerPC 604e single-pass array, 5.1 mm2 | 2 passes, double precision; year 1998 | p.936 |
| CSA groups | 7 | count | 0.5mm CMOS [as printed] / PowerPC 603e | 13 in the single-pass array | 2 passes, double precision; year 1998 | p.932 |
| double-precision multiply throughput | 2 | cycles per instruction | 0.5mm CMOS [as printed] / PowerPC 603e | PowerPC 604e, 1 cycle | year 1998 | p.936 |
evidence: pp.931-936

## space_gaps
* a `classic_fma` choice for the number of multiply-array passes per product, which is 1 in the PowerPC 604e FPU and 2 in the PowerPC 603e FPU   # pp.931, 936
* a `classic_fma` choice for where the 3:2 CSA group that injects the aligned addend sits, in the multiply stage or in the add stage   # p.932
* a `classic_fma` choice for splitting the aligned addend and the final adder across passes, here the low 26 bits in pass 1 and the upper 135 in pass 2, with the adder as a 26-bit incrementer, an 81-bit CLA and a 54-bit incrementer   # pp.934-935
* a `booth_recoded_parallel` `sign_extension` value for the reduced left edge banded matrix of encoded partial products, which gives a 57-bit pp0 and 56-bit pp1 through pp26   # p.929
* an alignment parameter for a per-pass alignment constant, 30 then 56, and for a shifter output narrower than the alignment range, a 136-bit output over a 161-bit range   # p.933
* a sticky-bit choice for carrying a pass's shifted-out bits into the next pass's sticky bit   # p.935
* a `booth_recoded_parallel` parameter for the reduction tree's row capacity against the rows used, here 16 admitted and 14 used   # p.934

## open_questions
* The add stage is said to perform leading zero detection for the normalize shift count, and the document does not say whether that detection anticipates in parallel with the adder (`lza`) or counts the adder's output (`lzc_after_add`), so no `lza` slot is filled   # p.928
* Table 1 (radix-4 Booth encoding), Table 2 (single- and dual-pass comparison) and every figure are images whose contents are absent from the extracted text, so Table 2's summary numbers are not recorded here   # pp.929, 937
* The technology appears as "0.5mm CMOS technology" in the extracted text, and whether the printed unit is a millimeter or a micrometer is not resolvable from the text   # p.936
* The normalize/round stage's rounding circuit and its normalize shifter are not described, so no `round` or `norm_shifter` slot is filled   # p.928
* Whether the document's reduced sign extension is the vocabulary's `roorda_compact` is not stated; the document cites Vassiliadis-Schwarz-Sung and Bewick and names neither scheme   # p.929
* The document does not state which 3:2 CSA placement of Fig. 8 the PowerPC 603e uses, only that the choice is made on logic complexity and timing requirements, with Fig. 9 given for the Fig. 8b case   # pp.932-933
