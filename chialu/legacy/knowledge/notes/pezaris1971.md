---
handle: pezaris1971
citation: S. D. Pezaris, "A 40-ns 17-Bit by 17-Bit Array Multiplier", IEEE Transactions on Computers, vol. C-20, no. 4, pp. 442-447, 1971
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int17]
authority: landmark
pages_read: 442-447 / 6
---

## summary
The document presents a combinational array multiplier that produces the full 34-bit product of two 17-bit signed 2's-complement operands in 40 ns (p.442). The design uses 2-bit gated adders with anticipated carry, direct addition of negative partial products, and sum/carry routing that balances the longest propagation paths (pp.443-446).

## families
### carry_save_array  (role: extends)
mechanism: The multiplier forms signed partial products by treating each operand's highest-order bit as negative and every other bit as positive, then adds positive and negative partial products directly through L101/L102/L103 2-bit gated adders (pp.443-446). Carry outputs propagate diagonally, while sum outputs propagate vertically; the final row propagates internal carries horizontally and accepts previous-row carries through sum inputs (p.446). A sum-skip arrangement lets sums jump after every four adders in the 17-bit implementation (p.446).
choices:
  signed_scheme: pezaris_negative_weight   # pp.444-446
new_choices:
  reduction_cell: two_bit_gated_adder_with_2_bit_anticipated_carry — The cell forms two partial-product bits and anticipates carry across both bit positions.   # pp.443-444
  sum_propagation: sum_skip_every_four_adders — Vertical sum signals bypass intermediate adders after each group of four in the 17-bit array.   # p.446
slots:
  cpa: UNKNOWN   # p.446
parameters: 17-bit by 17-bit signed 2's-complement operands; full 34-bit product; L101/L102/L103 2-bit cells; sum skip after every four adders; conventional 14-pin packages; 4-layer printed-circuit board   # pp.442-447
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplier delay | 40 | ns | technology node UNKNOWN; current-steering MECL-like ECL; 1971 | conventional sequential add-and-shift multiplier, value UNKNOWN | Tested full 34-bit product of two 17-bit positive or negative numbers | p.443 |
| L101 carry delay | 1.6 | ns | technology node UNKNOWN; Lincoln Laboratory L101 ECL cell; 1971 | UNKNOWN | 2-bit gated adder with 2-bit anticipated carry | p.443 |
| L101 sum delay | 2.8 | ns | technology node UNKNOWN; Lincoln Laboratory L101 ECL cell; 1971 | UNKNOWN | 2-bit gated adder with 2-bit anticipated carry | p.443 |
| package power dissipation | 350 | mW | technology node UNKNOWN; conventional dual-in-line 14-pin package; 1971 | UNKNOWN | Per package | p.443 |
| L101 chip size | 35 by 45 | mil | technology node UNKNOWN; Philco-Ford fabricated two-level-metal L101; 1971 | UNKNOWN | Basic 2-bit adder chip | p.444 |
| carry-heavy longest-path delay | about 30 | ns | technology node UNKNOWN; current-steering MECL-like ECL; 1971 | UNKNOWN | 4 sum + 12 carry delays in the 17-bit multiplier | p.446 |
| sum-heavy longest-path delay | about 35 | ns | technology node UNKNOWN; current-steering MECL-like ECL; 1971 | UNKNOWN | 9 sum + 6 carry delays in the 17-bit multiplier | p.446 |
| multiplier card size | 9 by 7 | in. | technology node UNKNOWN; 4-layer printed-circuit card; 1971 | UNKNOWN | Complete 17-bit by 17-bit multiplier | p.447 |
errors_and_checks: The multiplier generates the full exact 34-bit 2's-complement product; no approximation, error metric, or concurrent fault check is reported.   # pp.442-443
conditions: The array organization targets applications requiring the highest possible multiplication speed rather than conventional sequential add-and-shift operation (p.443). The implementation restricts the circuits and packaging to methods that avoid state-of-the-art fabrication or interconnection problems (p.443). The direct signed-partial-product method avoids first converting negative operands to positive values, which the document identifies as undesirable when operand sign bits arrive last (p.445). The document states that further speed improvements may use 3-bit anticipated carry and more elaborate sum-propagation paths (p.447).
evidence: Abstract and §I (pp.442-443); L101 equations and Figs. 1-3 (§II, pp.443-445); signed partial-product construction and Figs. 4-5 (§III, pp.444-446); array routing, path counts, and Figs. 6-7 (§IV, pp.446-447); conclusion (§V, p.447).

## new_families
none

## space_gaps
* carry_save_array lacks a choice for multi-bit gated reduction cells with local anticipated carry, as instantiated by the L101/L102/L103 cells (pp.443-446).
* carry_save_array lacks a choice for the sum-skip interval and propagation arrangement, which is four adders in the 17-bit implementation (p.446).
* carry_save_array.cpa does not directly describe the final row's mixed routing of internal carries horizontally and previous-row carries through sum inputs (p.446).

## open_questions
* The document does not identify the fabrication process or technology node.
* The document does not classify the final row as `uniform` or `hybrid_arrival_driven`, so the `cpa` slot remains UNKNOWN.
* The document reports no total multiplier power or transistor/package count; 350 mW applies only per package.
