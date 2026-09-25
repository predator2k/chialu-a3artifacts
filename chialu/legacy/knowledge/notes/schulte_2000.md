---
handle: schulte_2000
citation: M. J. Schulte, P. I. Balzola, A. Akkas, R. W. Brocato, "Integer Multiplication with Overflow Detection or Saturation", IEEE Transactions on Computers, vol. 49, no. 7, pp. 681-691, 2000
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [unsigned_integer, twos_complement_integer]
authority: incremental
pages_read: pp. 681-691 / 11 pages
---

## summary
The paper integrates overflow detection or saturation into unsigned and two's-complement array/tree multipliers without computing the most significant half of the product. The proposed multipliers retain the n least significant result bits and replace discarded product logic with overflow-reduction cells or OR trees.

## families
### saturating_clamp  (role: extends)
mechanism: Unsigned saturation ORs the overflow flag into every retained product bit, which produces 2^n-1. Two's-complement saturation selects either -2^(n-1) or 2^(n-1)-1 according to the product sign. The overflow condition is derived inside the partial-product reduction rather than by comparing a completed 2n-bit product.
choices:
  detect: partial_product_and_boundary_carry_or_reduce [outside domain]   # pp. 683-688
  clamp: bitwise_force (unsigned); result_mux (two's complement)   # pp. 682, 684, 687-688
new_choices:
  saturation_limit_selection: unsigned_max_or_signed_extrema — selects the representable endpoint from operand signedness and product sign   # pp. 682, 684
slots: none
parameters: n-bit operands; n-bit saturated result; unsigned saturation adds n OR gates; signed saturation uses an n-bit 2-to-1 multiplexor   # pp. 683-684
results: none reported separately for saturation implementations
errors_and_checks: The equations implement exact overflow detection and exact endpoint saturation; no approximation/fault model/detection coverage is evaluated.   # pp. 682-688
conditions: The method applies when the most significant product bits are not required, but overflow detection or saturation is required.   # p. 690
evidence: Sections 2-3; Figs. 2, 6-8; (3), (13), (14), (23), and (25), pp. 682-688

## new_families
### integrated_multiplier_overflow_saturation  (domain: mul: integer multipliers, closest: saturating_clamp, why_not: saturating_clamp describes the endpoint clamp but not the multiplier-specific removal of high-half product logic or its integrated overflow reduction.)
mechanism: Only the retained low product bits are formed. Unsigned overflow OR-reduces partial products in columns n through 2n-2 and carries entering column n; arrays share terms through iterative o_i/v_i OVD cells, while Dadda trees use an OR tree operating in parallel with partial-product reduction. Two's-complement multiplication forms operand magnitudes within the partial-product matrix and conditionally complements the retained product. Tree correction adds t...t to S/C with a carry-save adder before a shortened CPA and conditionally XORs the result.
choices:
  operand_interpretation: {unsigned, twos_complement}   # pp. 682, 684-685
  reduction_structure: {array, dadda_tree}   # pp. 682-684, 685-688
  response: {overflow_flag, saturate}   # pp. 682-688
  overflow_reduction: {linear_ovd_cells, parallel_or_tree}   # pp. 683-684, 686-688
  signed_product_correction: {xha_conditional_complement, csa_add_ones_then_xor}   # pp. 685-688
  retained_result: {n_lsb, n_minus_1_bit_magnitude_for_saturation}   # pp. 682-683, 687-688
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | between 50 and 53 | percent less | LSI Logic 0.6 micron LCA300K gate array (2000) | conventional full-product overflow detection | unsigned array multipliers | p. 689 |
| delay | between 41 and 42 | percent less | LSI Logic 0.6 micron LCA300K gate array (2000) | conventional full-product overflow detection | unsigned array multipliers | p. 689 |
| area | about 47 | percent less | LSI Logic 0.6 micron LCA300K gate array (2000) | conventional full-product overflow detection | unsigned Dadda tree multipliers | p. 689 |
| delay | between 23 and 28 | percent less | LSI Logic 0.6 micron LCA300K gate array (2000) | conventional full-product overflow detection | unsigned Dadda tree multipliers | p. 689 |
| area | between 12 and 43 | percent less | LSI Logic 0.6 micron LCA300K gate array (2000) | conventional full-product overflow detection | two's-complement array multipliers | p. 689 |
| delay | between 10 and 33 | percent less | LSI Logic 0.6 micron LCA300K gate array (2000) | conventional full-product overflow detection | two's-complement array multipliers | p. 689 |
| area | between 14 and 37 | percent less | LSI Logic 0.6 micron LCA300K gate array (2000) | conventional full-product overflow detection | two's-complement Dadda tree multipliers | p. 690 |
| delay | between 1 and 7 | percent less | LSI Logic 0.6 micron LCA300K gate array (2000) | conventional full-product overflow detection | two's-complement Dadda tree multipliers | p. 690 |
| area | 49 | percent less | 0.25 micron CMOS standard-cell library, four metal layers (2000) | conventional full-product overflow detection | 32-bit unsigned array; post-place-and-route | p. 690 |
| delay | 57 | percent less | 0.25 micron CMOS standard-cell library, four metal layers (2000) | conventional full-product overflow detection | 32-bit unsigned array; slow process, 110 C, 2.3 Volt | p. 690 |
| area | 39 | percent less | 0.25 micron CMOS standard-cell library, four metal layers (2000) | conventional full-product overflow detection | 32-bit two's-complement Dadda tree; post-place-and-route | p. 690 |
| delay | 30 | percent less | 0.25 micron CMOS standard-cell library, four metal layers (2000) | conventional full-product overflow detection | 32-bit two's-complement Dadda tree; slow process, 110 C, 2.3 Volt | p. 690 |
evidence: Sections 2-4; Figs. 2-8; Tables 2-8, pp. 682-690

## space_gaps
* saturating_clamp.detect lacks a value for overflow derived from discarded partial products and carries entering the retained product boundary.   # pp. 683-688
* The multiplier vocabulary lacks an exact low-half multiplier family whose high-half logic is replaced by integrated overflow detection/saturation.   # pp. 683-690
* carry_save_array.signed_scheme lacks magnitude multiplication with conditional two's-complement product correction.   # pp. 685-688

## open_questions
* The supplied text does not expose the absolute numeric entries in Tables 4-8, so only the relative reductions stated in the surrounding prose are recorded.
* The paper does not report synthesized area/delay results separately for the saturation variants.
