---
handle: blankenship1974
citation: P. E. Blankenship, "Comments on 'A Two's Complement Parallel Array Multiplication Algorithm'", IEEE Transactions on Computers, 1974
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [twos_complement_integer]
authority: incremental
pages_read: 1 / 1
---

## summary
The correspondence confirms the Baugh-Wooley two's-complement multiplication algorithm and describes a programmed ALU/Wallace-tree implementation. The implementation combines partial-product formation with first-level addition and reports 45 ns measured worst-case settling time for 12 × 12-bit and 16 × 8-bit configurations.

## families
### carry_save_array  (role: analyzes)
mechanism: Baugh-Wooley sign compensation produces a uniform partial-product array that can be summed by several techniques. Alternative treatments of the two most significant columns preserve equivalent full-adder logic, and the highest product bit may be omitted when it is redundant. # p.1327
choices:
  signed_scheme: baugh_wooley   # p.1327
new_choices:
  sign_compensation_variant: {baugh_wooley_original, pezaris_same_and_functions, inclusive_or_sign_bits} — selects the logic used in the two most significant partial-product columns   # p.1327
  highest_product_bit_formation: {formed, omitted_when_redundant} — controls formation of Pn+m-1   # p.1327
slots:
  none
parameters: signed two's-complement multiplication; operand widths are not fixed by the algorithm   # p.1327
results: none
errors_and_checks: none
conditions: The method targets modestly high-performance signed multiplication built from commercially available standard components. Omitting Pn+m-1 is invalid when the product of the greatest negative operands is required.   # p.1327
evidence: Main correspondence text and the three equivalent modifications of the Pn+m-1/Pn+m-2 columns, p.1327

## new_families
### programmed_alu_wallace_multiplier  (domain: mul: integer multipliers, closest: carry_save_array, why_not: the implementation uses a Wallace reduction tree with programmable first-level cells rather than the regular 2-D CSA structure)
mechanism: Multiplier-bit pairs directly control programmable ALU-type devices that combine effective partial-product formation with the first addition level. Later Wallace-tree levels use simple full adders. Standard 10 000-series ECL functions are connected by point-to-point wire wrap. # p.1327
choices: first_level_cell: {programmable_alu_type}; first_level_fusion: {partial_product_and_addition}; later_level_cell: {full_adder}; reduction_structure: {wallace_tree}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| measured worst-case settling time | 45 | ns | standard 10 000 series ECL functions, point-to-point wire wrap; 1974 | UNKNOWN | 12 × 12-bit and 16 × 8-bit configurations | p.1327 |
evidence: Implementation description and measured timing paragraph, p.1327

## space_gaps
* carry_save_array lacks a reduction slot that can name Wallace-tree summation, although the document states that the uniform Baugh-Wooley partial-product array supports several summation techniques. # p.1327
* carry_save_array lacks choices for the most-significant-column sign-compensation variant and optional omission of the redundant highest product bit. # p.1327

## open_questions
* The document does not distinguish whether 45 ns was measured separately for both configurations or represents a common reported worst case.
* The exact programmable ALU device types and output widths are not reported.
