---
handle: bewick1994#s09
parent: bewick1994
citation: G. W. Bewick, "Fast Multiplication: Algorithms and Implementation", PhD dissertation, Stanford University, CSL-TR-94-617, 1994
chapter: Efficient Sticky Bit Computation
pdf_pages: 158-163
status: ok
kind: thesis_chapter
unit_classes: [BINARY_ALU]
formats: [IEEE double precision floating point]
authority: thesis
pages_read: 6 / 6
---

## summary
The chapter defines sticky-bit computation for an IEEE double-precision multiplier and classifies four implementation methods. The proposed method injects -1 into the partial-product summation network and derives the sticky result from carry-propagate/carry-generate signals, which removes sticky computation from the critical path with approximately no net hardware increase. The method supports Booth-encoded multipliers and is most efficient with the redundant Booth compensation constant.

## families
### sig_mul_then_round  (role: extends)
mechanism: A floating-point multiplier adds a 12-bit-or-less exponent adder and rounding logic to an integer multiplier. The rounding logic uses the low-order half of the 106-bit product to modify the high-order 53 bits. The proposed sticky method injects -1 into the partial-product summation network and forces the final carry-propagate adder carry-in to 1, so low-order zero detection is derived from group propagate/generate signals without computing the discarded low-order result bits.   # p.158, p.160-p.163
choices:
  none
new_choices:
  sticky_bit_computation: injected_minus_one_group_propagate_generate — derive sticky from low-order group propagate/generate after subtracting 1 in the summation network   # p.160-p.163
  propagate_definition: exclusive_or_or_or — XOR propagation removes the group-generate test because propagation and generation are mutually exclusive   # p.161-p.163
slots:
  sig_mul: booth_recoded_parallel   # p.160, p.163
  round: UNKNOWN   # p.158
  exp: UNKNOWN   # p.158
  subnormal: UNKNOWN   # p.158
parameters: 106-bit integer product; final 53-bit fraction; 12-bit-or-less exponent adder   # p.158
results:
| metric | value | unit | technology / device | baseline | condition | page |
| sticky input width | 50 or so | low-order product bits | abstract | IEEE double precision product | precise count depends on rounding mode and the high-order product bit | p.159 |
| practical OR-gate fan-in | 4 or 5 | inputs | commonly available technology | direct large-fan-in OR | smaller OR gates must be connected in series | p.159 |
| final carry-propagate adder width | 106 | bits | abstract | high-speed floating-point multiplier | direct final-product computation | p.159 |
| injected constant width | 106 | bits | abstract | two's-complement product | -1 is represented as a full-length string of ones | p.163 |
| ordinary Booth extra summation hardware | about 53 | half adders | abstract | Booth sign-extension constant begins at about bit 53 | adding the -1 constant | p.163 |
| summation-network size | 1000 or more | carry-save adders | abstract | complete multiplier summation network | each carry-save adder is about twice as complex as one half adder | p.163 |
| net hardware change | approximately no net change | hardware requirements | abstract | ordinary Booth implementation | low-order carry-propagate hardware savings offset added -1 hardware | p.163 |
| redundant Booth extra summation hardware | at most 8-14 | half adders | abstract | existing compensation constant | small hard-multiple adders are usually 8-14 bits long | p.163 |
| redundant Booth total hardware | net reduction | hardware requirements | abstract | redundant Booth multiplier without the proposed sticky method | eliminated low-order summation hardware exceeds added -1 hardware | p.163 |
errors_and_checks: The sticky bit is required for IEEE round-to-nearest and the IEEE "exact" status signal. The chapter defines the sticky bit as high when all selected low-order product bits are zero.   # p.158-p.159
conditions: The direct OR method waits for the low-order product and places a multilevel OR network on the critical path.   # p.159
  The operand trailing-zero method runs in parallel with multiplication but requires two long priority encoders, a small adder, and a small comparator.   # p.159-p.160
  The Santoro redundant-form method overlaps sticky computation with the final carry-propagate addition and saves low-order adder hardware, but it works only for non-Booth-encoded multipliers.   # p.160
  The injected-minus-one method supports Booth-encoded multipliers and avoids computing the low-order product bits.   # p.160
  The injected-minus-one method is particularly efficient with the redundant Booth compensation constant.   # p.163
evidence: Sections B.1-B.5; Equations B.1-B.6 and the final XOR-propagate simplification

## taxonomy
* Sticky-bit computation methods   # p.159-p.163
  * Final-product methods   # p.159
    * Large fan-in OR over computed low-order product bits -> unmapped   # p.159
  * Parallel operand-analysis methods   # p.159-p.160
    * Count trailing zeros in both operands, add the counts, and compare against the sticky width -> unmapped   # p.159-p.160
  * Redundant-product methods   # p.160
    * Santoro low-order redundant-form zero test
      * Non-Booth-encoded multiplier -> unmapped   # p.160
  * Constant-injection methods   # p.160-p.163
    * Inject -1 into the partial-product summation network and add 1 at the final carry-propagate adder -> unmapped   # p.160-p.162
      * OR/XOR-compatible propagate with group-generate exclusion -> unmapped   # p.161-p.162
      * XOR propagate with sticky equal to low-order group propagate -> unmapped   # p.162-p.163
      * Ordinary Booth sign-extension constant integration -> unmapped   # p.163
      * Redundant Booth compensation-constant integration -> unmapped   # p.163

## primary_sources
* Santoro, Bewick, and Horowitz, UNKNOWN — high-speed rounding methods and a redundant-form sticky computation method for non-Booth multipliers [23]   # p.158, p.160

## new_families
### minus_one_prefix_sticky  (domain: fp: floating-point multipliers, closest: sig_mul_then_round, why_not: sig_mul_then_round has no sticky-computation choice or component slot)
mechanism: The summation network computes the product minus 1, and the final carry-propagate adder restores the product by using carry-in 1. A selected low-order result group is all zeros exactly when the injected carry propagates across the group and the group generates no carry. XOR-form bit propagates make group propagate and group generate mutually exclusive, so the sticky result reduces to the group-propagate signal.   # p.160-p.163
choices:
  propagate_form: {exclusive_or, or}   # p.161-p.163
  booth_integration: {ordinary_sign_extension_constant, redundant_booth_compensation_constant}   # p.163
results:
| metric | value | unit | technology / device | baseline | condition | page |
| sticky expression | group propagate AND NOT group generate | Boolean expression | abstract | general OR/XOR propagate definition | selected low-order group | p.161-p.162 |
| simplified sticky expression | group propagate | Boolean expression | abstract | general expression | individual propagates use EXCLUSIVE-OR | p.162-p.163 |
| critical-path effect | sticky bit eliminated from the critical path | qualitative | abstract | post-product zero detection | computation overlaps final carry-propagate addition | p.163 |
| ordinary Booth added hardware | about 53 | half adders | abstract | existing sign-extension constant | -1 requires about 53 additional ones | p.163 |
| redundant Booth added hardware | at most 8-14 | half adders | abstract | existing compensation constant | compensation constant supplies a suitable one position | p.163 |
evidence: Sections B.4-B.5; Equations B.1-B.6; pages 160-163

## space_gaps
* sig_mul_then_round lacks a sticky-computation choice and a sticky-logic component slot for final-product OR, operand trailing-zero counting, redundant-form testing, and injected-minus-one prefix testing.   # p.159-p.163
* minus_one_prefix_sticky requires `propagate_form` values for both EXCLUSIVE-OR and OR carry-propagate definitions.   # p.161-p.163
* booth_recoded_parallel lacks a choice for reusing its sign-extension or redundant-Booth compensation constant to inject the sticky-computation -1.   # p.163

## open_questions
* The chapter defines the sticky bit as high when all selected low-order bits are zero, so the merge pass must not assume the opposite polarity.   # p.159
* The exact low-order bit range depends on rounding mode and the high-order product bit, but the chapter gives only "50 or so" for IEEE double precision.   # p.159
* The chapter does not identify the propagate topology or final carry-propagate-adder family.   # p.160-p.163
* Reference [23] is named but its publication year is not present in this chapter.   # p.158, p.160
