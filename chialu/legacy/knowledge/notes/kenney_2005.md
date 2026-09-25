---
handle: kenney_2005
citation: Kenney, Schulte, "High-Speed Multioperand Decimal Adders", IEEE Transactions on Computers, 2005
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [bcd8421]
authority: incremental
pages_read: 11 / 11
---

## summary
The paper proposes two correction-speculation arrays and one nonspeculative carry-save tree for exact multioperand BCD addition (pp.954-959). Synthesized 4-bit/32-bit designs cover four to 16 operands; the nonspeculative design has logarithmic delay and roughly the same area as the speculative designs (pp.960-962).

## families
### decimal_multioperand_addition  (role: proposes)
mechanism: Single Correction Speculation adds BCD digits through a linear array of binary carry-save adders. The design assumes the first addition needs no correction. A carry bit from each addition selects whether six is combined with the next operand. Two final 4-bit carry-propagate additions and combinational correction logic produce an exact BCD digit (pp.955-956).
choices:
  reduction_style: binary_csa_linear_array [outside domain]   # pp.955-956
  compressor_arity: 3_to_2   # pp.955-956
  correction_placement: speculated_during_reduction [outside domain]   # pp.955-956
new_choices:
  correction_speculation_span: one addition — the first addition is assumed not to require correction   # p.955
slots:
  reduction_tree: linear_chain   # p.956
  root_adder: bcd_direct_addition [digit_code=bcd8421, carry_scheme=full_lookahead] [outside domain]   # p.957
parameters: m operands of n BCD digits; 4-bit digit slices; a 1-digit m-operand unit uses m 4-bit CSAs, (m-1) 4-bit 2:1 multiplexers, (m-2) ai+6 logic blocks, two 4-bit CPAs, and one 4-level correction block   # pp.955-956
results: none
errors_and_checks: Exact BCD sum; the Verilog models were extensively simulated for functional correctness   # p.960
conditions: Delay grows linearly with m. The ai/ai+6 multiplexers remain on the critical path, so Double Correction Speculation removes (m-2) multiplexer delays relative to this design (p.957). The regular structure may benefit full-custom deep-submicron implementation (p.961).
evidence: Section 3.1, Figs. 3-5, Tables 1-2 (pp.955-956); Section 3.3 (p.957); Section 4 (pp.960-961)

### decimal_multioperand_addition  (role: proposes)
mechanism: Double Correction Speculation assumes the first two additions need no correction. Carry ci-2[4] selects ai or ai+6 while the preceding carry-save addition executes, which removes most selection multiplexers from the critical path. A final speculation correction of 0, 6, or 12 repairs the two speculative additions (pp.956-957).
choices:
  reduction_style: binary_csa_linear_array [outside domain]   # pp.956-957
  compressor_arity: 3_to_2   # p.957
  correction_placement: speculated_during_reduction [outside domain]   # pp.956-957
new_choices:
  correction_speculation_span: two additions — the first two additions are assumed not to require correction   # pp.956-957
slots:
  reduction_tree: linear_chain   # p.957
  root_adder: bcd_direct_addition [digit_code=bcd8421, carry_scheme=full_lookahead] [outside domain]   # p.957
parameters: m operands of n BCD digits; 4-bit digit slices; a 1-digit m-operand unit uses m 4-bit CSAs, (m-3) 4-bit 2:1 multiplexers, (m-3) ai+6 logic blocks, one 4-bit 4:1 multiplexer, two 4-bit CPAs, and one 4-level correction block   # p.957
results: none
errors_and_checks: Exact BCD sum; the Verilog models were extensively simulated for functional correctness   # p.960
conditions: Delay grows linearly with m, but only one 4-bit 2:1 multiplexer remains on the critical path (p.957). Speculation beyond two additions does not further reduce delay because the multiplexers are already outside the critical path (p.957). The final correction logic is independent of m, which may help iterative designs with variable operand counts (p.961).
evidence: Section 3.2, Figs. 4b/6/7, Table 3 (pp.956-957); Section 3.3 (pp.957-958); Section 4 (pp.960-961)

### decimal_multioperand_addition  (role: proposes)
mechanism: Nonspeculative Addition reduces BCD operands with a logarithmic binary carry-save tree and forms a preliminary binary sum. Operand-count-specific combinational logic derives a modulo-16 sum correction g and decimal carry correction cout. A digit CPA applies g, and a word-wide decimal carry-lookahead adder incorporates the carry corrections (pp.958-959).
choices:
  reduction_style: binary_tree_then_convert   # pp.958-959
  compressor_arity: 3_to_2   # pp.958-960
  correction_placement: at_root   # pp.958-959
new_choices:
  none
slots:
  reduction_tree: csa_tree   # pp.958-960
  root_adder: bcd_direct_addition [digit_code=bcd8421, carry_scheme=full_lookahead] [outside domain]   # p.959
parameters: m operands of n BCD digits; 4-bit digit slices; a 1-digit m-operand unit uses (m-2) 4-bit CSAs, one 4-bit CPA, one 5-level correction block for up to 16 operands, and one 3-bit CPA; critical path includes roughly floor(log3/2(m-1)) CSAs   # p.959
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay overhead | 1.44 to 2.34 | times | LSI Logic lcbg11p 0.18 micron CMOS / 2005 | Binary Tree Adders | 32-bit multioperand adders, four to 16 operands, area-optimized synthesis | p.961 |
| area overhead | 1.61 to 2.03 | times | LSI Logic lcbg11p 0.18 micron CMOS / 2005 | Binary Tree Adders | 32-bit multioperand adders, four to 16 operands, area-optimized synthesis | p.961 |
errors_and_checks: Exact BCD sum; the Verilog models were extensively simulated for functional correctness   # p.960
conditions: Delay grows logarithmically and is lower than the speculative designs in the selected standard-cell library (pp.960-961). The correction logic becomes more complex as m increases (p.959). Optional 4:2 compressors may improve performance and regularity (p.961).
evidence: Section 3.4, Figs. 8c/9/10, Table 4, equations (4)-(5) (pp.958-959); Figs. 11-14 and Section 4 (pp.960-961)

### bcd_direct_addition  (role: instantiates)
mechanism: The final word-wide adder generates interdigit carries in parallel, selects decimal correction values, and adds the corrections to the 4-bit sum digits. The nonspeculative variant derives digit propagate/generate signals from sum/carry digits and uses decimal carry-lookahead logic to produce the final BCD word (pp.957-959).
choices:
  digit_code: bcd8421   # pp.954-959
  correction_placement: direct_decimal_carry_logic   # pp.954, 957-959
  carry_scheme: full_lookahead   # pp.954, 957-959
new_choices:
  none
slots:
  none
parameters: 32-bit implementations contain eight 1-digit multioperand adders followed by one word-wide decimal carry-lookahead adder   # p.960
results: none
errors_and_checks: Exact BCD result   # pp.954, 957-959
conditions: The word-wide carry-propagate stage is deferred until the carry-save reduction finishes (pp.954, 957-959).
evidence: Section 2 (p.954); Sections 3.3-3.4 (pp.957-959)

## new_families
none

## space_gaps
* `decimal_multioperand_addition.reduction_style` lacks a binary CSA linear-array value for correction-speculation designs (pp.955-957).
* `decimal_multioperand_addition.correction_placement` lacks speculation during reduction, which differs from both `per_level` and `at_root` (pp.955-957).
* `decimal_multioperand_addition` lacks a correction-speculation-span choice that distinguishes one-addition and two-addition speculation (pp.955-957).
* `decimal_multioperand_addition.root_adder` excludes `bcd_direct_addition`, although every proposed word-wide design uses a decimal carry-lookahead final adder (pp.957-959).

## open_questions
* Figs. 11-14 plot individual area/delay points without tabulating their numeric values, so the merge pass must not reconstruct exact point values from the curves (pp.960-961).
