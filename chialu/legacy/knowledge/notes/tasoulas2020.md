---
handle: tasoulas2020
citation: Z.-G. Tasoulas, G. Zervakis, I. Anagnostopoulos, H. Amrouch, J. Henkel, "Weight-Oriented Approximation for Energy-Efficient Neural Network Inference Accelerators", IEEE Transactions on Circuits and Systems I, vol. 67, no. 12, pp. 4670-4683, 2020
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [int8]
authority: incremental
pages_read: 14 / 14
---

## summary
The work proposes LVRM, an 8-bit multiplier with one exact and two low-variance approximate modes, and maps each quantized NN weight to a mode at design time (pp.2, 5-8). A bias update compensates each filter’s systematic multiplication error without hardware or retraining (p.4). The evaluated method reduces multiplication energy across seven convolutional NNs and four datasets while satisfying accuracy-loss thresholds (pp.9-12).

## families
### accuracy_configurable  (role: proposes)
mechanism: LVRM applies wire-by-switch replacement to an exact multiplier’s gate-level netlist. Each inserted switch selects the original wire or a constant `0`/`1`; nested switch configurations provide exact mode LVRM0 and approximate modes LVRM1/LVRM2. A 2-bit control selects `2'b00`, `2'b01`, or `2'b11`. Only wires affecting the eight least significant output bits are candidates (p.5).
choices:
  mode_count: 3   # p.5
  reconfig_grain: wire_by_switch [outside domain]   # p.5
new_choices:
  quality_objective: low_error_variance — constrains `Var(εW)` separately for each fixed weight across all activations   # pp.4-5
slots:
  none
parameters: 8-bit multiplier; three modes; 2-bit control; LVRM1 variance bound `8²`; LVRM2 variance bound `20²`; at least 90% of weights must satisfy each bound   # pp.5-6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| energy reduction | up to 25 | % | 7nm FinFET; 2020 | exact 8-bit multiplier [30] | LVRM1 | p.6 |
| energy reduction | 18 | % | 7nm FinFET; 2020 | exact 8-bit multiplier [30] | LVRM1 average over weights | p.6 |
| energy reduction | up to 35 | % | 7nm FinFET; 2020 | exact 8-bit multiplier [30] | LVRM2 | p.6 |
| energy reduction | 22 | % | 7nm FinFET; 2020 | exact 8-bit multiplier [30] | LVRM2 average over weights | p.6 |
| area overhead | 3 | % | 7nm FinFET; 2020 | exact double-buffered 64 × 64 MAC array | LVRM array with 64 control units and 10-bit weight/control registers | p.9 |
errors_and_checks: LVRM1 has average variance 27, with 94% of weights satisfying `8²`; LVRM2 has average variance 157, with 97% satisfying `20²` (p.6). The quality function also requires `p(εW > 0) ≥ 0.80` or `p(εW > 0) = 0` to favor systematic error that bias correction can compensate (p.5).
conditions: Candidate circuits must meet the exact multiplier’s critical-path delay (pp.5-6). Additional accuracy modes would reduce energy savings because the 8-bit circuit is small and each mode requires more switches (p.5). LVRM requires an added 2-bit input but otherwise retains a structure similar to the exact multiplier (p.6).
evidence: Section III-A; Equations 2-12; Figure 4; Section III-C.

### approximate_logic_synthesis  (role: extends)
mechanism: Exhaustive design-space exploration enumerates every candidate wire as unchanged, tied to `0`, or tied to `1`. C-level simulation evaluates all 65,536 input combinations. Variance/error-probability constraints filter configurations, synthesis filters configurations that violate exact-multiplier delay, and power analysis selects the minimum-power nested configuration pair (pp.5-6).
choices:
  method: wire_by_switch_exhaustive_search [outside domain]   # pp.5-6
  error_constraint: combined   # p.5
  formal_verification: none   # pp.5-6
new_choices:
  optimization_metric: power_at_fixed_delay — minimizes power after enforcing the exact multiplier’s critical-path delay   # pp.5-6
slots:
  none
parameters: about 5 million configurations; 65,536 input combinations; 80-thread dual Xeon Gold 6138 server; about 6 hours   # pp.5-6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| design-space exploration time | about 6 | hours | dual Xeon Gold 6138; 2020 | UNKNOWN | 8-bit LVRM with the two variance constraints | p.6 |
errors_and_checks: Every configuration is exhaustively simulated over all 65,536 8-bit input pairs, but no formal verification method is reported (p.5).
conditions: Exhaustive exploration is practical here because only one small 8-bit multiplier is generated; a faster general synthesis framework is outside the work’s scope (pp.5-6).
evidence: Section III-A.2, steps i-viii.

### approximate_mac_nn  (role: proposes)
mechanism: A four-step design-time procedure ranks convolution layers by accuracy loss under LVRM2, maps entire low-significance layers to LVRM2, maps small-magnitude weight ranges in remaining layers to LVRM2, and maps wider remaining ranges to LVRM1. Each mapping updates the filter bias by `B' = B + Σμ(εWj)`. Runtime control is stored with each weight or generated from per-layer range bounds (pp.4, 7-9).
choices:
  error_bias_policy: weight_oriented_shaping   # pp.7-8
  precision_scaling: none   # pp.3, 10
  retraining: false   # pp.2, 4
new_choices:
  approximation_assignment: per_weight_per_layer — selects LVRM0/LVRM1/LVRM2 from layer significance and quantized weight magnitude   # pp.6-8
  systematic_error_compensation: bias_update — adds the expected multiplication error to each filter bias   # p.4
slots:
  none
parameters: 8-bit quantized weights/activations; accuracy-loss thresholds `{0.5%, 1.0%, 2.0%}`; LVRM2 ranges `0±10`, `0±5`, and `0`; LVRM1 ranges `0±30` and `0±20`; seven NNs; four datasets; 28 models   # pp.7-10
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average multiplication-energy gain | 17.7 | % | 7nm FinFET; 2020 | exact multipliers | CIFAR-10, all examined NNs/thresholds | p.10 |
| average multiplication-energy gain | 17.7 | % | 7nm FinFET; 2020 | exact multipliers | CIFAR-100, all examined NNs/thresholds | p.11 |
| average multiplication-energy gain | 16.6 | % | 7nm FinFET; 2020 | exact multipliers | GTSRB, all examined NNs/thresholds | p.11 |
| average multiplication-energy gain | 20.2 | % | 7nm FinFET; 2020 | exact multipliers | LISA, all examined NNs/thresholds | p.11 |
| average MAC-array energy reduction | 11 | % | 7nm FinFET, 64 × 64 array at 500MHz; 2020 | exact MAC array | ResNets/MobileNet, 0.5% accuracy-loss configurations | p.12 |
| framework execution time | up to 2 | h | dual Xeon Gold 6138; 2020 | UNKNOWN | ResNet-56 on CIFAR-100 | p.13 |
errors_and_checks: The bias update gives `μ(εY) = 0` and `Var(εY) = ΣVar(εWj)` under the stated independence assumption (p.4). Evaluated inference-accuracy loss is constrained to 0.5%, 1.0%, or 2.0% (p.10).
conditions: The method targets already-trained 8-bit quantized convolutional NNs and requires no retraining (pp.3-4). The range mapping assumes small-magnitude weights contribute less and reports that examined weights cluster around zero; wider ranges can cover other distributions (pp.7-8). The mapping runs once at design time, while runtime mode changes occur only when weights change (p.8).
evidence: Sections III-A.1, III-B, III-C, IV; Equations 1-9 and 13; Figures 5-12.

## new_families
none

## space_gaps
* `accuracy_configurable.reconfig_grain` lacks `wire_by_switch`, which is LVRM’s circuit-level reconfiguration mechanism (p.5).
* `approximate_logic_synthesis.method` lacks exhaustive wire-by-switch configuration search (pp.5-6).
* `approximate_mac_nn` lacks per-weight/per-layer approximation assignment and filter-bias error compensation choices (pp.4, 6-8).

## open_questions
* The paper does not identify the microarchitecture of the exact 8-bit multiplier used as LVRM’s baseline.
* The selected gate-level wires/constants for LVRM1 and LVRM2 are not reported.
