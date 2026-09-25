---
handle: nicolaidis_2003
citation: M. Nicolaidis, "Carry Checking/Parity Prediction Adders and ALUs", IEEE Transactions on VLSI Systems, vol. 11, no. 1, pp. 121-128, 2003
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary_int]
authority: incremental
pages_read: 8 / 8
---

## summary
The document proposes self-checking binary adders and ALUs that combine parity prediction with double-rail checking of normal/check carries. # p.121
Three reductions fuse the parity generator with the carry checker, replace duplicated complex carry logic with ripple-style check-carry slices, and share selected carry/sum logic through partial duplication. # pp.123-125
The resulting designs are fault secure for the stated single logic-fault model and TSC for single stuck-at faults when the underlying optimized circuits contain no redundant faults. # pp.123-126

## families
### self_checking_datapath  (role: proposes)
mechanism: Output parity is predicted from operand parities, carry input, and carry parity, while a double-rail checker compares normal and check carries. The checker also produces the carry-parity signals, so a separate parity generator is omitted. Each check-carry slice uses ripple-carry logic but takes its carry input from the preceding normal carry, which avoids duplicating carry-lookahead/skip logic without adding linear delay. Partial duplication shares a signal used by the normal carry, check carry, and sum output, so common-mode carry errors become parity-visible. # pp.123-125
choices:
  encoding: parity_plus_dual_rail_carry   # pp.123-125
new_choices:
  check_carry_generation: ripple_slice_from_normal_predecessor — selects ripple-style check-carry slices driven by normal carries rather than a duplicated fast carry block   # pp.123-124
  carry_duplication_scope: partial_shared_sum_logic — shares selected logic among the normal carry/check carry/sum output   # pp.124-125
  checker_parity_fusion: true — uses the double-rail checker outputs as the carry-parity signals   # p.123
slots:
  comparator: two_rail_tree [input_code=two_rail, embedded=true]   # pp.123-124
parameters: Adder schemes include ripple-carry/group carry-lookahead/full carry-lookahead/skip-carry/conditional-sum; ALU functions include addition/XOR/OR/NAND; evaluated widths include 16/32/64 bits. # pp.121,125,127-128
results:
| metric | value | unit | technology / device | baseline | condition | page |
| hardware overhead | 12 | % | UNKNOWN; 2003 | duplication, 100% overhead | 64-bit carry-lookahead adder including latches; checker cost excluded in both schemes | p.127 |
| hardware overhead | 13 | % | UNKNOWN; 2003 | duplication, 100% overhead | 32-bit carry-lookahead adder; latch treatment is not restated in the conclusion | p.128 |
| hardware overhead | 39 | % | UNKNOWN; 2003 | duplication, 100% overhead | 16-bit carry-lookahead ALU including latches; checker cost excluded in both schemes | p.127 |
errors_and_checks: The design is fault secure for single logic faults affecting the enumerated carry-generation/check-carry/bit-slice modules. # pp.123-126 The single logic-fault model permits arbitrary logic-valued errors at one faulty module's outputs and includes stuck-at faults. # p.123 Self-testing holds for single stuck-at faults when optimized adder/ALU blocks have no redundant faults, which yields TSC together with fault security. # p.126 False-alarm behavior is not reported.
conditions: The scheme applies to ripple-carry/group carry-lookahead/full carry-lookahead/skip-carry/conditional-sum adders and ALUs. # pp.121,127 Fast adders and ALUs obtain lower relative overhead because their complex normal carry-generation blocks are not duplicated. # p.127 ALUs incur more overhead than adders because logic operations require additional parity-prediction logic. # p.127 Global ALU control lines require parity coding and an endpoint parity checker because one control fault can affect multiple slices. # p.126 An odd-width NAND ALU requires an additional controlled XOR inversion. # p.125
evidence: Sections IV-VII; Figs. 3-9; Tables I-II; Theorems 2-5, pp.123-127.

### parity_prediction_adder  (role: extends)
mechanism: The predicted result parity is formed from both operand parities, the input carry, and the parity of the carries. Using normal carries for carry parity makes every fault confined to carry-generation logic undetectable because the predicted and actual parity change identically. Duplicated carries provide finite detection latency but remain non-fault-secure when one carry fault produces an even number of output errors. The proposed extension checks the normal/check carry pairs with a double-rail checker, which detects carry-propagated errors while parity prediction detects isolated output errors. # pp.122-123
choices:
  parity_groups: 1   # p.122
  carry_scheme: duplicate_carry   # pp.122-123
new_choices:
  checked_partial_carry_replication: true — distinguishes checked ripple-style check carries with partial sharing from conventional unchecked carry duplication   # pp.123-125
slots:
  comparator: two_rail_tree [input_code=two_rail, embedded=true]   # pp.123-124
  carry_replica: ripple_carry   # pp.123-124
parameters: One parity bit covers the complete result; the construction is presented for adders and ALUs. # pp.122-125
results:
| metric | value | unit | technology / device | baseline | condition | page |
| fault-detection probability per clock cycle | greater than 1/2 | probability | UNKNOWN; 2003 | duplicated-carry parity prediction | uniform input-vector distribution for a stuck-at carry fault | p.122 |
| detection latency | infinite | cycles | UNKNOWN; 2003 | carry parity derived from normal carries | faults affecting only carry-generation logic | pp.122-123 |
errors_and_checks: Conventional parity prediction detects every single-output error and every single-input fault but is not fault secure for carry faults that produce even-multiplicity output errors. # pp.121-123 Checking duplicated carries makes the proposed extension fault secure for the stated single logic-fault model. # p.123
conditions: Operand parity bits are assumed available in parity-encoded datapaths, so only carry parity must be generated. # p.122 Carry parity must not be derived solely from normal carries because carry-generation faults then have infinite detection latency. # pp.122-123
evidence: Sections III-IV; Figs. 2-5; Theorems 1-4, pp.122-125.

### two_rail_tree  (role: instantiates)
mechanism: The double-rail checker receives pairs comprising normal and check carries and produces a double-rail output pair. The checker has a one-to-one correspondence with a parity tree, so its outputs compute complementary carry-parity signals and replace the separate parity generator. # p.123
choices:
  input_code: two_rail   # p.123
  embedded: true   # pp.123-124
new_choices:
  parity_output_reuse: true — exposes whether checker outputs also serve as predicted-parity inputs   # p.123
slots:
  none
parameters: Tree arity is UNKNOWN. # p.123
results:
| metric | value | unit | technology / device | baseline | condition | page |
| separate parity generators removed | 1 | generator | UNKNOWN; 2003 | trivial carry-checking/parity-prediction combination | checker outputs supply the two carry-parity signals | p.123 |
errors_and_checks: A valid alternating output pair represents code-valid inputs and checker operation; detailed checker fault coverage and false-alarm behavior are not quantified separately. # pp.122-123
conditions: The fusion requires the parity-tree correspondence of the double-rail checker. # p.123
evidence: Section IV-A; Fig. 3, p.123.

## new_families
none

## space_gaps
* `self_checking_datapath` lacks a choice for ripple-style check carries driven from preceding normal carries rather than a fully duplicated carry network. # pp.123-124
* `self_checking_datapath` lacks a choice for partial carry duplication that shares logic with the sum path while preserving fault security. # pp.124-125
* `two_rail_tree` lacks a choice stating whether the checker outputs are reused as parity-generator outputs. # p.123
* `parity_prediction_adder.carry_scheme` cannot distinguish conventional duplicated carries from checked partial carry replication. # pp.122-125

## open_questions
* Tables I and II contain additional gate-count overhead rows whose values are not legible in the supplied document text; the original tables must be consulted before merging those rows.
* The exponent in the stated probability that a duplicated-carry fault remains undetected after 30 cycles is missing from the supplied text. # p.122
* The conclusion reports 13% overhead for a 32-bit carry-lookahead adder without restating whether input/output latches are included. # p.128
