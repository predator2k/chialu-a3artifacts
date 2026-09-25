---
handle: swartzlander_1980
citation: Swartzlander, "Merged Arithmetic", IEEE Transactions on Computers, 1980
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [positive_fixed_point]
authority: landmark
pages_read: 946-950 / 5
---

## summary
Merged arithmetic forms one composite bit-product matrix for a multiterm inner product, reduces the matrix to two rows with counters, and performs carry propagation once. The paper reports lower gate counts than discrete fast multipliers followed by an adder tree, with the advantage increasing with the number of product terms.

## families
### fused_csa  (role: proposes)
mechanism: All bit-product matrices and any expansion addends are combined into one composite matrix. Full-adder/half-adder counters reduce each column through Dadda-style height targets until two rows remain, and one carry look-ahead adder produces the inner product. The construction replaces all but one of the carry look-ahead adders used by separate multipliers and an adder tree. # pp.946-949
choices:
  compressor: 3:2   # pp.946-947
new_choices:
  term_count: K — number of products merged into the composite matrix   # pp.948-949
  expansion_addends: one_or_more — addends included directly in the initial composite matrix   # pp.946,949
  reduction_schedule: Dadda_height_sequence — successive maximum column heights used during counter reduction   # pp.946-947
slots:
  final_cpa: carry_lookahead   # pp.946-949
parameters: Two-term designs use 8-bit, 12-bit, and 16-bit operands; the detailed 8-bit design uses 128 AND gates, 7 half adders, 97 full adders, and one 16-stage carry look-ahead adder. The many-term design uses eight pairs of 8-bit inputs, one 18-bit expansion input, and a 20-bit result. # pp.947-950
results:
| metric | value | unit | technology / device | baseline | condition | page |
| total gate count | 1246 | two-input gates | UNKNOWN; 1980 | conventional discrete design: 1686 two-input gates | two-term 8-bit inner product; merged count is 73.9% of baseline | p.948 |
| total gate count | 2804 | two-input gates | UNKNOWN; 1980 | conventional discrete design: 3548 two-input gates | two-term 12-bit inner product; merged count is 79.0% of baseline | p.948 |
| total gate count | 4846 | two-input gates | UNKNOWN; 1980 | conventional discrete design: 5782 two-input gates | two-term 16-bit inner product; merged count is 83.8% of baseline | p.948 |
| total package count | 39 | packages | UNKNOWN; 1980 | conventional discrete design: 44 packages | two-term 8-bit inner product under the stated standard-IC assumptions | p.948 |
| total delay | Tgate + 6TFA + TCLA(16) | delay expression | UNKNOWN; 1980 | conventional: Tgate + 4TFA + TCLA(14) + TCLA(16) | two-term 8-bit inner product | pp.948-949 |
| carry look-ahead delay | 2.5-4 | TFA | UNKNOWN; 1980 | full-adder delay TFA | single-level carry look-ahead up to 16 bits with 4-bit look-ahead | p.949 |
| total gate count | 4935 | two-input gates | UNKNOWN; 1980 | conventional discrete design: 8452 two-input gates | eight-term 8-bit inner product with 18-bit expansion input; merged count is 58.4% of baseline | p.950 |
| external signals after shift-register organization | 70 | signals | UNKNOWN; 1980 | direct interface: 166 signals | eight-term design; fits the stated 84-pin package assumption | p.950 |
errors_and_checks: The merged implementation is arithmetically equivalent to the discrete multiplication/addition implementation; no approximation, fault model, or concurrent check is reported. # p.946
conditions: The examples assume positive fixed-point numbers. Baugh-Wooley correction bits are cited as permitting direct two's-complement use, but no signed implementation is evaluated. Gate count excludes layout-dependent interconnection complexity, which the paper says is typically assumed to add 50 percent of gate area. The two-term speed claim depends on a single-level carry look-ahead delay being 2.5-4 full-adder delays. # pp.947,949
evidence: Abstract and §§I-II, Fig. 1; §III, Figs. 2-3 and Tables I-IV; §IV, Figs. 4-5 and Table V, pp.946-950.

### pairwise_tree  (role: compares)
mechanism: The conventional implementation completes each product in a separate fast multiplier containing its own carry look-ahead adder, then combines the products with an N-input adder tree. The two-term comparison uses two Dadda multipliers followed by a 16-stage carry look-ahead adder; the eight-term comparison uses eight multipliers and an adder tree. # pp.946,948-950
choices:
new_choices: none
slots:
  mul: carry_save_array   # pp.946,948
  accum: binary_tree   # pp.946,949
parameters: Compared at two terms with 8-bit, 12-bit, and 16-bit operands, and at eight terms with 8-bit operands plus an 18-bit expansion input. # pp.948-950
results:
| metric | value | unit | technology / device | baseline | condition | page |
errors_and_checks: The conventional structure is the exact arithmetic baseline; no fault checks are reported. # pp.946,949
conditions: The comparison uses Dadda full-adder reduction because the paper treats that method as the appropriate optimum fast-multiplier baseline. # p.949
evidence: §I, §III and Table I-III, §IV and Table V, pp.946,948-950.

### carry_save_datapath  (role: extends)
mechanism: Carry-save multiplication forms each pseudoproduct as a sum word and a nonpropagated carry word. Merged arithmetic sums the pseudoproducts before performing carry propagation, which avoids completing every product separately. # p.950
choices:
  assimilation_point: end_of_chain   # p.950
  accumulator_redundant: true   # p.950
new_choices: none
slots:
  assimilator: UNKNOWN   # p.950
parameters: For K products of pairs of N-bit words, the conventional approach requires 2KN + N + 1 carry-save adder cycles, while the merged approach requires KN + K + N cycles. # p.950
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry-save adder cycles | KN + K + N | cycles | UNKNOWN; 1980 | conventional: 2KN + N + 1 cycles | sum of K products of pairs of N-bit words | p.950 |
| speed improvement | approaching 50 percent | UNKNOWN | UNKNOWN; 1980 | conventional carry-save multiplication-addition | large carry-save multiplication-addition designs | p.950 |
errors_and_checks: Arithmetic is retained in sum/carry form until final carry propagation; no approximation or fault check is reported. # p.950
conditions: The approximately 50 percent saving applies to carry-save multiplication-addition and is stated asymptotically from the cycle formulas. # p.950
evidence: §V and §VI, p.950.

## new_families
none

## space_gaps
* `fused_csa` lacks choices for product-term count, direct expansion-addend injection, and the counter-tree height schedule, all of which determine the reported merged construction. # pp.946-950
* `fused_csa.compressor` does not represent the paper's mixed use of full-adder and half-adder counters. # pp.947-949

## open_questions
* The paper does not specify a semiconductor technology, fabrication node, clock frequency, power, energy, or completed physical-layout area.
* The paper cites Baugh-Wooley signed support but evaluates only positive fixed-point examples.
