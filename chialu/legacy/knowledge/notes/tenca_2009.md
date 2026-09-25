---
handle: tenca_2009
citation: A. F. Tenca, "Multi-Operand Floating-Point Addition", ARITH-19, pp. 161-168, 2009
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp32, fp64]
authority: incremental
pages_read: 161-168 / 8
---

## summary
The document proposes an integrated FPADDn that aligns multiple floating-point operands, adds their significands at extended precision, and rounds once. The implemented FPADD3 provides commutative/perfectly rounded results with competitive delay and an area cost that depends on the synthesis constraint.

## families
none

## new_families
### multi_operand_fp_addition  (domain: fp: floating-point adders, closest: single_path, why_not: `single_path` does not cover simultaneous addition/sticky-bit resolution/cancellation handling for more than two operands)
mechanism: FPADDn unpacks the operands, finds the maximum exponent, aligns every significand, resolves per-operand sticky information, adds the signed aligned significands once, detects catastrophic cancellation, and then normalizes/rounds once. FPADD3 anchors one operand's sign, uses an internal precision of p = 2f + 5 bits, and bypasses the internal sum when cancellation requires forwarding the smallest operand.
choices:
  operand_count: Int[3..4:1]   # pp.161, 166
  alignment_method: {max_tree_then_subtract, pairwise_difference_reuse}   # pp.163-164
  internal_precision_bits: {2f_plus_5_for_fpadd3}   # pp.165-167
  por_sticky_handling: {discard_all}   # p.165
  cor_sticky_handling: {largest_sticky_operand_for_fpadd3, signed_out_of_range_sum}   # p.165
  sign_handling: {anchor_operand_relative_complement}   # pp.164-167
  catastrophic_cancellation_handling: {detect_and_bypass_smallest_operand}   # pp.166-167
  commutative_inputs: Bool   # pp.161, 167
parameters: 3 inputs in the implemented design; single precision uses 8 exponent bits and 23 printed significand bits; double precision is also synthesized; internal adder precision p = 2f + 5 bits; implementation results are without pipeline stages.   # pp.166-168
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 47,600 | UNKNOWN | TSMC 90nm CMOS standard-cell library; 2009 | 51,200 for a network of two delay-optimized FPADD2s | double precision, tight time constraint, without pipeline stages | p.168 |
| delay | 5.6 | ns | TSMC 90nm CMOS standard-cell library; 2009 | 5.4ns for a network of two delay-optimized FPADD2s | double precision, tight time constraint, without pipeline stages | p.168 |
| area reduction | 7% | % | TSMC 90nm CMOS standard-cell library; 2009 | network of two delay-optimized FPADD2s | double precision, tight time constraint, without pipeline stages | p.168 |
errors_and_checks: FPADD3 produces a perfectly rounded result, defined as infinite-precision addition followed by one rounding, and enforces commutativity. Formality verifies the p = 2f + 5 lower bound; Matlab/high-precision simulation finds FPADD3 always more accurate than the tested FPADD2 network.   # pp.166-168
conditions: The pairwise-difference alignment is smaller/faster under tight timing, while the maximum-exponent-tree alternative becomes smaller under relaxed timing.   # p.167
conditions: FPADD3 is faster than the two-FPADD2 network in the single-precision synthesis, but the network is smaller under loose timing constraints.   # pp.167-168
conditions: Applications that prioritize small area, tolerate lower accuracy, and permit relaxed timing favor the FPADD2 network.   # p.168
conditions: Sticky-bit resolution and catastrophic-cancellation combinations grow rapidly beyond four inputs, which the document says forbids practical FPADDn use for large n > 4.   # pp.165-166
evidence: §§2-4, Figures 1-7, and Table 1 establish the mechanism and precision bound; §5 and Figure 8 provide implementation comparisons (pp.162-168).

## space_gaps
* The floating-point-adder vocabulary lacks an integrated multi-operand family with operand count, sticky-resolution, extended-precision, commutativity, and catastrophic-cancellation choices.   # pp.161-167

## open_questions
* The document does not state whether f in p = 2f + 5 includes the implicit leading significand bit; p.167 describes single precision as having “23 bits in the significand.”
* Figure 8 supplies no exact numeric single-precision area/delay coordinates, so those plotted results cannot be transcribed exactly.
* The stated network area of 51,200 is not arithmetically reproduced by two areas of 29,323 followed by the stated 17% combined-area reduction; the note preserves the printed values.
