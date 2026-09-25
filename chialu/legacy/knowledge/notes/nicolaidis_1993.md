---
handle: nicolaidis_1993
citation: M. Nicolaidis, "Efficient Implementations of Self-Checking Adders and ALUs", Proc. FTCS-23, pp. 586-595, 1993
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int4, int8, int16, int32, int64]
authority: incremental
pages_read: 586-595 / 10
---

## summary
The paper proposes self-checking binary adders/ALUs that combine double-rail carry checking with parity-coded datapaths. The Carry Checking/Parity Prediction scheme avoids duplicating the carry-lookahead block and reports 18.9% transistor-count overhead for a 32-bit carry-lookahead adder. The DCVS/Domino implementations are strongly fault secure for single stuck-at/stuck-on/stuck-open faults, while static CMOS implementations provide weaker stuck-on self-testing guarantees.

## families
### self_checking_datapath  (role: proposes)
mechanism: The adder/ALU uses double-rail coding, while buses/register files/shifters use parity. A double-rail checker also generates output parity because its structure corresponds to a parity tree, which avoids a separate double-rail-to-parity translator. Input parity-to-double-rail translation can be implemented through normal/complementary outputs of duplicated input latches in the Output Checking scheme; the Carry Checking scheme avoids that latch duplication.
choices:
  encoding: parity_plus_dual_rail_carry   # p.587
new_choices:
  checking_scheme: {output_checking_parity_generation, carry_checking_parity_prediction} — selects output-code checking or checked carries plus predicted output parity   # pp.587,590
  code_translation: {duplicated_input_latches, checker_as_parity_generator, avoided_by_parity_prediction} — controls conversion between parity-coded and double-rail portions   # pp.587,590
slots:
  comparator: two_rail_tree   # p.587
parameters: binary datapaths; evaluated at 4/8/16/32/64-bit widths; pipeline depth/latency/II UNKNOWN   # p.594
results:
| metric | value | unit | technology / device | baseline | condition | page |
| hardware overhead | about 40 to 45 | % | static CMOS, node UNKNOWN; 1993 | unchecked multiply/divide array | proposed slices applied to arrays; implementation not detailed | p.595 |
errors_and_checks: DCVS/Domino implementations are SFS for single stuck-at/stuck-on/stuck-open faults. Static implementations are TSC for stuck-at/stuck-open faults and fault secure for stuck-on faults; stuck-on self-testing requires current monitoring.   # p.593
conditions: Parity checking of buses/register files requires each data line to feed only one output and requires crossed control lines to be checked.   # p.588
evidence: §II, §VI, Conclusion; Figures 1-2.

### parity_prediction_adder  (role: extends)
mechanism: The proposed scheme maintains normal output sums but represents carries as double-rail pairs. A double-rail checker checks the carries and supplies their parity for PS = PA ⊕ PB ⊕ PC. For full carry lookahead, normal carries come from the lookahead block while redundant check carries ripple independently; comparison of the lowest erroneous lookahead carry with its unaffected check carry preserves detection.
choices:
  parity_groups: 1   # p.590
  carry_scheme: dual_rail_carry   # pp.590-591
new_choices:
  checked_signal: carries — selects carry checking rather than direct double-rail checking of sum outputs   # p.590
slots:
  comparator: two_rail_tree   # p.590
  carry_replica: ripple_carry   # p.591
parameters: 4/8/16/32/64-bit adders; 4-bit carry-lookahead units in the evaluated lookahead design   # p.594
results:
| metric | value | unit | technology / device | baseline | condition | page |
| ripple overhead, parity prediction | 36.6 | % | static CMOS, node UNKNOWN; 1993 | unchecked ripple adder | 4 bits; normalized checker treatment | p.594 |
| ripple overhead, proposed | 43.7 | % | static CMOS, node UNKNOWN; 1993 | unchecked ripple adder | 4 bits; checker excluded | p.594 |
| lookahead overhead, parity prediction | 51.4 | % | static CMOS, node UNKNOWN; 1993 | unchecked lookahead adder | 4 bits; normalized checker treatment | p.594 |
| lookahead overhead, proposed | 36.3 | % | static CMOS, node UNKNOWN; 1993 | unchecked lookahead adder | 4 bits; checker excluded | p.594 |
| ripple overhead, parity prediction | 23.6 | % | static CMOS, node UNKNOWN; 1993 | unchecked ripple adder | 8 bits; normalized checker treatment | p.594 |
| ripple overhead, proposed | 30.8 | % | static CMOS, node UNKNOWN; 1993 | unchecked ripple adder | 8 bits; checker excluded | p.594 |
| lookahead overhead, parity prediction | 41.4 | % | static CMOS, node UNKNOWN; 1993 | unchecked lookahead adder | 8 bits; normalized checker treatment | p.594 |
| lookahead overhead, proposed | 26.4 | % | static CMOS, node UNKNOWN; 1993 | unchecked lookahead adder | 8 bits; checker excluded | p.594 |
| ripple overhead, parity prediction | 17.2 | % | static CMOS, node UNKNOWN; 1993 | unchecked ripple adder | 16 bits; normalized checker treatment | p.594 |
| ripple overhead, proposed | 24.3 | % | static CMOS, node UNKNOWN; 1993 | unchecked ripple adder | 16 bits; checker excluded | p.594 |
| lookahead overhead, parity prediction | 36.5 | % | static CMOS, node UNKNOWN; 1993 | unchecked lookahead adder | 16 bits; normalized checker treatment | p.594 |
| lookahead overhead, proposed | 21.4 | % | static CMOS, node UNKNOWN; 1993 | unchecked lookahead adder | 16 bits; checker excluded | p.594 |
| ripple overhead, parity prediction | 14.0 | % | static CMOS, node UNKNOWN; 1993 | unchecked ripple adder | 32 bits; normalized checker treatment | p.594 |
| ripple overhead, proposed | 21.1 | % | static CMOS, node UNKNOWN; 1993 | unchecked ripple adder | 32 bits; checker excluded | p.594 |
| lookahead overhead, parity prediction | 34.0 | % | static CMOS, node UNKNOWN; 1993 | unchecked lookahead adder | 32 bits; normalized checker treatment | p.594 |
| lookahead overhead, proposed | 18.9 | % | static CMOS, node UNKNOWN; 1993 | unchecked lookahead adder | 32 bits; checker excluded | p.594 |
| ripple overhead, parity prediction | 12.3 | % | static CMOS, node UNKNOWN; 1993 | unchecked ripple adder | 64 bits; normalized checker treatment | p.594 |
| ripple overhead, proposed | 19.4 | % | static CMOS, node UNKNOWN; 1993 | unchecked ripple adder | 64 bits; checker excluded | p.594 |
| lookahead overhead, parity prediction | 31.7 | % | static CMOS, node UNKNOWN; 1993 | unchecked lookahead adder | 64 bits; normalized checker treatment | p.594 |
| lookahead overhead, proposed | 17.7 | % | static CMOS, node UNKNOWN; 1993 | unchecked lookahead adder | 64 bits; checker excluded | p.594 |
| ripple asymptotic overhead, parity prediction | 10.7 | % | static CMOS, node UNKNOWN; 1993 | unchecked ripple adder | width approaches infinity | p.594 |
| ripple asymptotic overhead, proposed | 17.8 | % | static CMOS, node UNKNOWN; 1993 | unchecked ripple adder | width approaches infinity | p.594 |
| lookahead asymptotic overhead, parity prediction | 31.5 | % | static CMOS, node UNKNOWN; 1993 | unchecked lookahead adder | width approaches infinity | p.594 |
| lookahead asymptotic overhead, proposed | 16.4 | % | static CMOS, node UNKNOWN; 1993 | unchecked lookahead adder | width approaches infinity | p.594 |
errors_and_checks: Conventional parity prediction detects single output errors but is not fault secure when one carry fault produces multiple output errors. The proposed double-rail carry check supplies SFS/TSC behavior under the technology-dependent fault guarantees stated above.   # pp.586,590,593
conditions: Ripple parity prediction has slightly lower area than the proposed scheme, but lacks fault security. The proposed scheme has lower overhead for evaluated carry-lookahead adders because conventional parity prediction duplicates a fast carry network. Checker areas are excluded or normalized as described in §VII.   # pp.593-594
evidence: §IV, §VI, §VII; Figures 13-18; Table 1.

### ripple_carry  (role: instantiates)
mechanism: Ripple slices are implemented with double-rail DCVS, mixed DCVS/Domino, or static differential XOR/carry gates. The Output Checking scheme produces double-rail sums; the Carry Checking scheme produces conventional sum bits while retaining double-rail carries.
choices:
  full_adder_cell: DCVS/static differential [outside domain]   # pp.588-589
new_choices:
  implementation_style: {DCVS, DCVS_Domino, static_differential} — selects the circuit technology used for the self-checking slice   # pp.588-589
slots: none
parameters: static self-checking bit slices use 36 or 44 transistors; operand widths evaluated at 4/8/16/32/64 bits   # pp.589,594
results:
| metric | value | unit | technology / device | baseline | condition | page |
| bit-slice transistor count | 36 | transistors | static CMOS, node UNKNOWN; 1993 | none | self-checking ripple slice without separate P/G outputs | p.589 |
| bit-slice transistor count | 44 | transistors | static CMOS, node UNKNOWN; 1993 | 36-transistor slice | self-checking slice generating propagate/generate signals | p.589 |
errors_and_checks: The fault guarantees depend on DCVS/Domino versus static CMOS implementation as stated for self_checking_datapath.   # p.593
conditions: The 36-transistor design is preferred for ripple addition, while the 44-transistor design supplies propagate/generate signals needed by lookahead/skip structures.   # p.589
evidence: §III.1, §IV.1; Figures 3-7, 13.

### carry_lookahead  (role: instantiates)
mechanism: Full lookahead generates normal carries through a shared fast network and redundant check carries through ripple logic. Group lookahead applies the ripple checking scheme inside each group and checks group carry inputs against redundant carries.
choices:
  group_size: 4   # p.594
  intergroup_carry: lookahead   # pp.590-591
new_choices: none
slots: none
parameters: full/group carry lookahead; evaluated with cascaded 4-bit carry-lookahead units and 4/8/16/32/64-bit adders   # pp.590-591,594
results: none
errors_and_checks: The lowest erroneous lookahead carry is compared with an unaffected check carry, which prevents a shared lookahead fault from escaping through correlated later carries.   # p.591
conditions: Ripple-generated check carries do not delay sum generation and are ready for comparison when the adder outputs are ready.   # p.591
evidence: §III.1.d, §IV.2-§IV.3; Figures 12, 14; Table 1.

### carry_skip  (role: extends)
mechanism: The paper states that the carry-checking/parity-prediction implementation extends to carry-skip adders/ALUs, using propagate/generate signals from the differential slice, but provides no detailed carry-skip circuit.
choices: none
new_choices: none
slots: none
parameters: UNKNOWN
results: none
errors_and_checks: UNKNOWN
conditions: Applicability is asserted without implementation details or separate measurements.   # p.593
evidence: §V.

### conditional_sum  (role: extends)
mechanism: The paper states that the carry-checking/parity-prediction implementation extends to conditional-sum adders/ALUs, but provides no detailed conditional-sum circuit.
choices: none
new_choices: none
slots: none
parameters: UNKNOWN
results: none
errors_and_checks: UNKNOWN
conditions: Applicability is asserted without implementation details or separate measurements.   # p.593
evidence: §II, §V.

## new_families
none

## space_gaps
* self_checking_datapath lacks a checking_scheme choice distinguishing Output Checking/Parity Generation from Carry Checking/Parity Prediction.   # pp.587,590
* self_checking_datapath lacks a code_translation choice for reused checker outputs, duplicated complementary latches, or translation avoidance.   # pp.587,590
* ripple_carry.full_adder_cell lacks DCVS/DCVS-Domino/static-differential self-checking cell values.   # pp.588-589
* parity_prediction_adder lacks a checked_signal choice distinguishing output/carry checking.   # p.590

## open_questions
* Table 2’s ALU overhead values are unreadable in the supplied document text and must not be reconstructed.
* The conclusion gives 32.3% conventional parity-prediction overhead for a 32-bit full carry-lookahead adder, while Table 1 gives 34.0%; the merge pass must preserve the Table 1 value and flag the discrepancy.   # pp.594-595
