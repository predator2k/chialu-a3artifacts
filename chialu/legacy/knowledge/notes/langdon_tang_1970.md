---
handle: langdon_tang_1970
citation: G. G. Langdon, C. K. Tang, "Concurrent Error Detection for Group Look-ahead Binary Adders", IBM Journal of Research and Development, vol. 14, no. 5, pp. 563-573, 1970
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int16]
authority: landmark
pages_read: 11 / 11
---

## summary
The paper compares residue mod 3 checking with parity prediction plus supplementary checks for a 16-bit group look-ahead binary adder. The paper finds that residue checking is economical only when operand residues already exist in the data flow, while parity checking has a cost advantage with three or more data-transfer checks (pp.570-571). The paper also defines polarized Boolean differences for analyzing undetected residue-check errors (pp.566, 572).

## families
### carry_lookahead  (role: instantiates)
mechanism: The adder divides 16 bits into four groups of four bits. Full look-ahead forms carries between groups and within each group, while group internal generate/propagate functions form sums without adding a separate carry-to-sum delay (pp.564-565).
choices:
  group_size: 4   # p.565
  levels: 2   # p.565
  intergroup_carry: lookahead   # pp.564-565
  block_sizing: uniform   # p.565
new_choices: none
slots: none
parameters: 16-bit operands; four 4-bit groups; full look-ahead between and within groups   # p.565
results:
| metric | value | unit | technology / device | baseline | condition | page |
| basic adder half-adder count | 80 | circuits | current-switch emitter-follower / 1970 | none | half-adder functions | p.570 |
| basic adder look-ahead count | 34 | circuits | current-switch emitter-follower / 1970 | none | group look-ahead functions | p.570 |
| group internal carry count | 24 | circuits | current-switch emitter-follower / 1970 | none | internal carry functions | p.570 |
| sum-generation count | 56 | circuits | current-switch emitter-follower / 1970 | none | sum-generation functions | p.570 |
| total basic adder count | 194 | circuits | current-switch emitter-follower / 1970 | none | complete 16-bit group look-ahead adder | p.570 |
errors_and_checks: The analyzed fault model is a single gate output stuck-at-0 or stuck-at-1 under the concurrent-check assumption; detection must occur within one adder cycle (p.565).
conditions: Four-bit grouping is presented as a compromise among speed/fan-in/fan-out (p.565). Coverage depends on group size, fan-out duplication, and independently failing complemented signals (pp.564, 568, 571).
evidence: §2; Fig. 1; Table 1; pp.563-565, 570-571.

### residue  (role: compares)
mechanism: The checker compares the mod 3 sum of operand residues with the residue of the binary sum. A four-bit combinational residue block is composed into a tree for 16-bit operands, and duplicate group-carry checks supplement the residue comparison where group look-ahead can produce undetectable error values divisible by 3 (pp.567-570).
choices:
  modulus: 3   # p.567
  granularity: endpoint   # p.567
  generator_style: four_bit_combinational_block_tree [outside domain]   # p.567
new_choices:
  operand_residue_availability: preprovided or locally_generated — distinguishes data-flow residue bits from three locally generated residues   # pp.570-571
  supplemental_group_carry_check: duplicate_and_compare — covers group carry-in failures missed by the residue comparison   # pp.568, 570
slots: none
parameters: 16-bit operands; four-bit residue blocks; mod 3 primary checker; mod 15 additional implementation   # pp.567, 571
results:
| metric | value | unit | technology / device | baseline | condition | page |
| 16-bit mod 3 tree | 70 | circuits | current-switch emitter-follower / 1970 | none | residue generation | p.570 |
| mod 3 adder | 20 | circuits | current-switch emitter-follower / 1970 | none | A/B/Cin/Cout residue addition | p.570 |
| mod 3 comparison | 4 | circuits | current-switch emitter-follower / 1970 | none | residue comparison | p.570 |
| group-carry check and comparison | 24 | circuits | current-switch emitter-follower / 1970 | none | supplementary coverage | p.570 |
| adder-only residue-checking strategy | 258 | circuits | current-switch emitter-follower / 1970 | duplicated adder costs less | three mod 3 trees plus residue adder/comparator and group-carry check | p.570 |
| residue data-flow strategy | at least 188 | circuits | current-switch emitter-follower / 1970 | parity strategy at least 200 circuits | operands already carry mod 3 bits; one generator and one checker | p.570 |
| four mod 3 checking trees | 280 | circuits | current-switch emitter-follower / 1970 | four XOR trees: 128 circuits | data-flow failure-isolation strategy | p.571 |
| 8-bit mod 15 building block | 40 / 4 | circuits / delay levels | current-switch emitter-follower / 1970 | none | carry-look-ahead/end-around-carry implementation | p.571 |
| 16-bit mod 15 tree | 120 / 8 | circuits / delay levels | current-switch emitter-follower / 1970 | mod 3 tree: 70 circuits / 9 levels | two 8-bit building blocks | p.571 |
errors_and_checks: Mod 3 detects an erroneous result only when the error value is not divisible by 3 (p.567). Group look-ahead can produce undetected values including ±3×2^i, ±7×2^i, ±15×2^i, and ±12×2^4 under single-gate failures (pp.568, 572). The supplemented design is described as completely covering single-gate failures and as providing better, unquantified multiple-failure coverage than parity checking (p.570).
conditions: Local generation of both operand residues makes residue checking costlier than parity checking and even duplication (p.570). Preprovided operand residues can make residue checking cheaper in a data-flow-wide strategy (pp.570-571). Larger moduli detect more failure patterns but increase generator cost (p.571).
evidence: §§4-5, 7-9; Figs. 4-6; Table 2; Table A-I; Appendix A; pp.567-572.

### parity_prediction_adder  (role: compares)
mechanism: The checker predicts result parity from grouped half-adder/generate/transmit signals. A half-sum check validates input parity and half-sum signals, while independently generated duplicate group carries are compared with the main group look-ahead carries (pp.569-570).
choices:
  parity_groups: 4   # pp.565, 569
  carry_scheme: duplicate_carry   # p.569
new_choices:
  half_sum_check: true — checks input parity and half-sum signals H_i   # p.569
  parity_predictor_input: internal_group_signals — Eq. (20) predicts group parity without operand parity bits   # p.569
slots: none
parameters: 16-bit operands; four 4-bit parity-prediction groups; one-adder-cycle concurrent detection   # pp.565, 569
results:
| metric | value | unit | technology / device | baseline | condition | page |
| 16-way XOR-tree count | 32 | circuits | current-switch emitter-follower / 1970 | none | half-sum check/sum parity functions | p.570 |
| high-speed parity prediction and comparison | 64 | circuits | current-switch emitter-follower / 1970 | none | grouped predictor | p.570 |
| parity comparison | 2 | circuits | current-switch emitter-follower / 1970 | none | predicted/actual parity comparison | p.570 |
| G/T signal coverage | 16 | circuits | current-switch emitter-follower / 1970 | cheaper unchecked H implementation | Eq. (23) implementation surcharge | p.570 |
| group-carry check and comparison | 24 | circuits | current-switch emitter-follower / 1970 | none | duplicate group carries | p.570 |
| adder-checking overhead | 138 | circuits | current-switch emitter-follower / 1970 | none | parity prediction plus supplementary checks | p.570 |
| parity data-flow strategy | at least 200 | circuits | current-switch emitter-follower / 1970 | residue strategy at least 188 circuits | adder checking plus one 30-circuit generator and one 32-circuit checker | p.570 |
| four XOR checking trees | 128 | circuits | current-switch emitter-follower / 1970 | four mod 3 trees: 280 circuits | data-flow failure-isolation strategy | p.571 |
errors_and_checks: Basic predicted parity alone does not detect carry-generation failures because the sum parity and carry parity change together (p.569). Half-sum/duplicate-carry checks produce a design described as completely covering single-gate failures, although independently failing complements require additional handling (pp.569-570).
conditions: Predicted parity requires a high-speed grouped implementation because a conventional XOR tree would arrive later than the sum (p.569). Parity has a cost advantage in conventional organizations with three or more data-transfer checks (p.571).
evidence: §§6-9; Eqs. (18)-(23); Table 3; Appendix B; pp.569-573.

## new_families
none

## space_gaps
* `residue.generator_style` lacks the four-bit combinational building-block tree used for mod 3 generation (p.567).
* `residue` lacks a choice for whether operand residues are preprovided or generated beside the adder, although that choice reverses the cost comparison (pp.570-571).
* `residue` lacks a supplementary group-carry checking choice for group look-ahead adders (pp.568, 570).
* `parity_prediction_adder` lacks a `half_sum_check` choice, which is required for the paper's complete single-gate coverage (pp.569-570).

## open_questions
* The residue/parity comparison circuits are not described as `two_rail_tree`, so the comparator slots remain unassigned.
* The circuit counts are technology-dependent estimates rather than fabricated area/delay measurements (p.570).
* Multiple-gate-failure coverage is described only qualitatively, so no coverage percentage can be recorded (p.570).
