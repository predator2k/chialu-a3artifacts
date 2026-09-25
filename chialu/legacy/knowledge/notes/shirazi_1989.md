---
handle: shirazi_1989
citation: Shirazi, Yun, Zhang, "RBCD: Redundant Binary Coded Decimal Adder", IEE Proceedings E - Computers and Digital Techniques, 1989
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [rbcd, bcd]
authority: landmark
pages_read: 156-160 / 5
---

## summary
The paper presents a carry-free decimal adder using a balanced 4-bit RBCD digit set and a per-digit circuit containing two small PLAs and two 4-bit binary adders. The addition delay is independent of operand digit count, while conversion from RBCD back to BCD retains a digit-to-digit propagation dependency.

## families
### redundant_decimal_addition  (role: proposes)
mechanism: Each operand digit belongs to D = {-7, ..., 7} and uses a 4-bit code whose negation is its 2s complement. A first binary adder produces the digit sum; PLA1 detects whether the result requires +6, -6, and a carry or borrow; PLA2 combines that correction with the preceding digit’s carry; and a second binary adder produces a digit in {-6, ..., 6}. The generated carry digit belongs to {-1, 0, 1}, so no carry propagates beyond the adjacent position. # p.156-158
choices:
  digit_set: rbcd_m7_p7   # p.156
  operands_redundant: both   # p.156-157
  final_conversion: carry_propagate_adder   # p.159-160
new_choices:
  implementation: binary_adders_with_correction_plas — two 4-bit binary adders and two small PLAs implement each digit, rather than directly mapping the complete addition table into a large PLA   # p.157-158, p.160
slots:
  none
parameters: radix 10; digit set {-7, ..., 7}; 4-bit digit code; output sum digit set {-6, ..., 6}; carry digit set {-1, 0, 1}; two PLAs and two 4-bit binary adders per digit   # p.156-158
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 18 | Δ | UNKNOWN, 1989 | conventional BCD adder: 7nΔ | n-digit RBCD addition; Δ is an AND/OR gate delay with at most three inputs | p.158 |
| delay | 7n | Δ | UNKNOWN, 1989 | RBCD adder: 18Δ | n-digit conventional BCD adder using carry-look-ahead circuits for each 4-bit binary adder | p.158 |
| delay | 105 | Δ | UNKNOWN, 1989 | RBCD adder: 18Δ | 15-digit conventional BCD adder | p.158 |
| relative delay | about 6 | times longer | UNKNOWN, 1989 | RBCD adder | 15-digit conventional BCD adder | p.158 |
| PLA delay | 3 | Δ | UNKNOWN, 1989 | UNKNOWN | each PLA; PLA1 has 6 terms and PLA2 has 5 terms | p.158 |
| 4-bit adder delay | 6 | Δ | UNKNOWN, 1989 | UNKNOWN | carry-look-ahead implementation | p.158 |
| one-digit layout area | 1000 × 800 | λ² | nMOS, 1989 | UNKNOWN | λ is the nMOS technology resolution | p.158 |
errors_and_checks: The mapping preserves A + B = C×10 + S exactly; no approximation, fault model, detection coverage, or checker is reported.   # p.156-157
conditions: Addition delay remains constant with digit count because each result depends only on adjacent digit positions. # p.156-158 The conversion overhead makes one-operation BCD and RBCD cycles almost equivalent, while repeated arithmetic on internally RBCD data pays the conversion penalty only once. # p.160 The paper states that conventional BCD and RBCD systems require equivalent silicon area at the one-digit level. # p.160
evidence: §2, Tables 1-5, Figs. 1-2, pp.156-158; §4, p.160

### carry_lookahead  (role: instantiates)
mechanism: Each RBCD digit uses two 4-bit carry-look-ahead binary adders. The paper derives the carry equations for a 4-bit adder and assigns a delay of 6Δ. The RBCD-to-BCD converter also expresses its interdigit dependency in the standard generate/propagate carry recurrence, so any carry-look-ahead technique can replace the ripple propagation. # p.157-159
choices:
  group_size: 4   # p.157-158
new_choices:
  none
slots:
  none
parameters: 4-bit binary adder; two instances per RBCD digit   # p.157-158
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 6 | Δ | UNKNOWN, 1989 | UNKNOWN | one 4-bit carry-look-ahead adder | p.158 |
errors_and_checks: none
conditions: Carry look-ahead is used inside each fixed-width RBCD digit and can accelerate the interdigit dependency of RBCD-to-BCD conversion, but the conversion delay still depends on the number of digits.   # p.158-160
evidence: timing analysis in §2, p.158; §3.2, p.159

## new_families
### bcd_rbcd_conversion  (domain: decimal: decimal misc, closest: decimal_encoding_codec, why_not: decimal_encoding_codec covers conventional significand storage encodings and lacks conversion to or from an arithmetic RBCD digit set)
mechanism: BCD-to-RBCD conversion detects BCD digits 7, 8, and 9, adds 6 to each detected digit in parallel, and applies the generated carries in a second digit-wise step, giving constant conversion delay. RBCD-to-BCD conversion adds 6 to negative RBCD digits and propagates a borrow condition across digits; a zero digit maps either to zero or ten according to the preceding digit’s state. The propagation recurrence can use carry look-ahead. Negative sign-magnitude BCD values are converted digit-wise and then negated by taking each RBCD digit’s 2s complement. # p.159-160
choices: direction: {bcd_to_rbcd, rbcd_to_bcd, both}; propagation: {digitwise_constant, ripple, carry_lookahead}; negative_input_handling: {sign_magnitude_then_digitwise_twos_complement}
results: none
evidence: §3.1, Table 6 and Fig. 3, p.159; §3.2, Table 7 and Fig. 4, pp.159-160

## space_gaps
* redundant_decimal_addition lacks a slot for the fixed-width binary digit adder; this design fills such a slot with a 4-bit carry_lookahead adder. # p.157-158
* redundant_decimal_addition lacks an implementation choice distinguishing a direct addition-table PLA from binary adders with correction PLAs. # p.160

## open_questions
* The paper does not report a technology node, transistor count, power, or fabricated-chip measurements.
* The paper does not give a total numerical delay for either BCD-to-RBCD or RBCD-to-BCD conversion.
