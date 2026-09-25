---
handle: bruguera_1999
citation: J. D. Bruguera and T. Lang, "Leading-One Prediction with Concurrent Position Correction", IEEE Transactions on Computers, 1999
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [ieee_binary_fp]
authority: incremental
pages_read: 1083-1097 / 15
---

## summary
The paper proposes leading-one prediction with parallel detection trees that correct a possible one-position prediction error during normalization without adding delay to the significand-addition/normalization critical path. The method supports positive or negative subtraction results and is evaluated in single-path and double-path floating-point adders. # p.1085, p.1092, p.1095-1096

## families
### single_path  (role: extends)
mechanism: The significand subtraction, leading-one prediction, and concurrent error detection operate in parallel. The correction modifies the fine normalization-shifter stage, which eliminates the later compensation shifter and exponent incrementer and permits the final two pipeline stages to be merged. # p.1092, p.1094-1095
choices:
  pipeline_depth: 4   # p.1095
new_choices:
  none
slots:
  norm: coarse_fine   # p.1091-1092
parameters: five pipeline stages with uncompensated LOP; four stages with concurrent correction; latency cycles and II UNKNOWN   # p.1095
results:
| metric | value | unit | technology / device | baseline | condition | page |
| pipeline depth | 4 | stages | UNKNOWN / 1999 | 5-stage single-datapath adder using LOP without concurrent correction | Same critical-path delay after eliminating the compensation shifter and exponent incrementer | p.1095 |
errors_and_checks: The leading-one position is exact after detection and correction of the possible one-position prediction error. # p.1083, p.1088
conditions: The LOP applies when the effective operation is significand subtraction after alignment. The operands use sign-and-magnitude representation, while the magnitude adder computes |A-B|. # p.1085
evidence: §2, §4.2, §6.1; Figs. 3, 10, and 12, p.1085, p.1091-1095

### two_path  (role: extends)
mechanism: The FAR path handles additions and effective subtractions with exponent difference larger than one. The CLOSE path handles effective subtractions with exponent difference at most one and uses the LOP because it can require a full-length normalization shift. Concurrent correction removes the CLOSE-path compensation shift, which makes the FAR/CLOSE path delays equal. # p.1095-1096
choices:
  path_threshold: 1   # p.1095
  close_path_trigger: exp_diff_and_effective_sub   # p.1095
new_choices:
  none
slots:
  near_lz: lza   # p.1095
  close_norm: coarse_fine   # p.1091-1092, p.1095
parameters: four pipeline stages; a three-stage implementation is described only as possibly obtainable; latency cycles and II UNKNOWN   # p.1096
results:
| metric | value | unit | technology / device | baseline | condition | page |
| pipeline depth | 4 | stages | UNKNOWN / 1999 | double-datapath adder with a CLOSE-path compensation shift | Concurrent correction eliminates the compensation shift and gives both paths the same delay | p.1096 |
errors_and_checks: The CLOSE-path normalization shift is corrected exactly for the possible one-position LOP error. # p.1095-1096
conditions: The FAR path needs at most a one-bit left normalization shift. The CLOSE path needs at most a one-bit alignment shift but may need a full-length normalization shift. # p.1095
evidence: §6.2 and Fig. 13, p.1095-1096

## new_families
### leading_one_prediction_concurrent_correction  (domain: fp: floating-point adders, closest: lzd_cell_tree, why_not: lzd_cell_tree detects the leading position from a completed result, whereas this mechanism predicts from aligned operands in parallel with significand subtraction and concurrently corrects a possible one-position error.)
mechanism: A carry-free radix-2 signed-digit subtraction forms W=A-B from aligned significands. Shared pre-encoding produces F for a binary leading-one encoding tree and separate Gp/Gn strings for positive/negative correction-pattern trees. The detection trees identify the patterns that make the basic prediction one position early. Their output increments the encoded shift amount through the fine normalization-shifter stage while earlier shifter stages operate. The design supports either sign of W and produces an exact normalization shift without selecting an adder carry. # p.1085-1092
choices:
  result_sign_support: {positive_only, positive_or_negative} — whether the predictor assumes a nonnegative subtraction result or handles either result sign   # p.1085
  correction_detection: {post_shift_compensation, carry_checking, parallel_detection_trees} — how the possible one-position error is detected or corrected   # p.1083-1085, p.1092-1095
  detection_tree_count: Int[1..2:1] — whether positive/negative correction patterns share a tree or use separate trees   # p.1088-1089
  correction_timing: {after_normalization, concurrent_with_normalization} — whether correction adds a compensation shift or overlaps normalization   # p.1083-1084, p.1091-1092
  correction_stage: {fine_normalization_stage} — the shifter stage modified to admit one additional shift position   # p.1091-1092
results:
| metric | value | unit | technology / device | baseline | condition | page |
| addition-plus-shift delay saved | 13 | percent | UNKNOWN / 1999 | LOP without concurrent correction | Estimated compensation-shifter delay eliminated by the proposed correction | p.1092 |
| LOP area increase | about 80 | percent | UNKNOWN / 1999 | LOP without concurrent correction | Rough gate-level estimate; proposed logic adds pre-encoding/detection/correction and removes the compensation shifter | p.1094 |
| adder-plus-shifter delay reduction | about 10 | percent | UNKNOWN / 1999 | concurrent correction based on carry checking | Rough gate-level estimate of carry-selection/shift-correction delay relative to the coarse shifter | p.1095 |
| carry-selection-logic area difference | about 10 | percent smaller | UNKNOWN / 1999 | proposed concurrent-correction logic | Rough gate-level estimate for the carry-checking alternative | p.1095 |
| significand-addition-and-normalization delay reduction | about 10 | percent | UNKNOWN / 1999 | LOP without concurrent correction and LOP with carry checking | Conclusion-level summary of the rough estimates | p.1096 |
errors_and_checks: The basic LOP can err by one position. The positive and negative detection trees detect the documented correction patterns, and the shift amount is incremented by one when correction is required. The resulting normalization shift is exact; fault coverage and false-alarm behavior are not evaluated. # p.1088-1092
evidence: §2-§5; Tables 1-3; Figs. 3-11, p.1085-1095

## space_gaps
* The `near_lz` slots admit `lza`, but the vocabulary defines no `lza` family for operand-based leading-zero/leading-one anticipation or its correction method. # p.1083-1092
* A leading-one-prediction family needs a `correction_detection` choice covering compensation shift/carry checking/parallel detection trees. # p.1084, p.1092-1095
* A leading-one-prediction family needs a `result_sign_support` choice because the proposed design handles positive or negative subtraction results, while earlier designs can require operand comparison/swapping. # p.1084-1085

## open_questions
* The paper gives no implemented technology, operand precision, significand width, clock frequency, or measured silicon results.
* The delay/area comparisons are qualitative gate-level estimates and depend on technology/floating-point-unit requirements. # p.1092
* The conclusion summarizes both alternative comparisons as about 10 percent, while §5.2 separately estimates 13 percent against the nonconcurrent scheme. # p.1092, p.1096
* The three-stage double-path pipeline is described as a possibility rather than an established implementation result. # p.1096
