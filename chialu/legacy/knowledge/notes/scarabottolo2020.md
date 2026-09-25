---
handle: scarabottolo2020
citation: I. Scarabottolo, G. Ansaloni, G. A. Constantinides, L. Pozzi, S. Reda, "Approximate Logic Synthesis: A Survey", Proceedings of the IEEE, vol. 108, no. 12, pp. 2195-2213, 2020
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [uint8, uint16, uint32]
authority: survey
pages_read: 19 / 19
---

## summary
The survey classifies approximate logic synthesis at the gate-netlist, Boolean-representation, and behavioral/RTL/C levels and reviews error estimation methods that guide or validate simplifications (pp.2-3). Its comparative experiments cover approximate multipliers, adders, multiply–add units, and an eight-point FFT (pp.14-16).

## families
### approximate_logic_synthesis  (role: analyzes)
mechanism: Approximate logic synthesis transforms an exact function into an inexact implementation under an error constraint. Structural methods prune, substitute, or mutate mapped-netlist nodes; rewriting methods simplify Boolean optimization forms, Boolean matrices, BDDs, or AIGs; approximate high-level synthesis transforms AST/IR descriptions through width reduction, operator substitution, expression rewriting, and loop approximation (pp.2, 6-13).
choices:
  method: [signal_substitution, behavioral_transform]   # pp.7, 12-13
  formal_verification: [bdd, sat_miter]   # pp.8, 11-12
new_choices:
  abstraction_level: {gate_netlist, boolean_representation, behavioral_rtl_c} — the representation on which approximation operates   # pp.2-3
  transformation_strategy: {gate_pruning, signal_substitution, stochastic_gate_transform, evolutionary_mutation, boolean_optimization, boolean_matrix_factorization, bdd_rewrite, aig_rewrite, bit_width_reduction, operator_substitution, expression_rewrite, loop_transform} — the simplification applied to the representation   # pp.6-13
  search_strategy: {greedy, exhaustive_bounded, stochastic, evolutionary, pareto_evolutionary, integer_linear_programming} — the method used to select approximation transformations   # pp.6-8, 12-13
slots: none
parameters: 8-bit and 16-bit unsigned multipliers; 32-bit adder; 4-bit multiply–add; eight-point FFT   # pp.14-16
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area saving | 22% | % | FreePDK 45-nm; 2020 | exact eight-point FFT | 0.12% reduction in accuracy; ABACUS variants | p.2 |
| area reduction | 36% | % | UNKNOWN; result year UNKNOWN | exact x2 circuit | 2.79% bit flips; BLASYS | p.10 |
| area reduction | half | original multiplier area | FreePDK 45-nm / Yosys-ABC; 2020 | exact 8-bit unsigned multiplier | 0.32% mean absolute error; BLASYS or EvoApprox Pareto result | p.14 |
| area reduction | 45% | % | FreePDK 45-nm / Yosys-ABC; 2020 | exact 8-bit unsigned multiplier | 0.2% error threshold; EvoApprox | p.14 |
| area reduction | 18% | % | FreePDK 45-nm / Yosys-ABC; 2020 | exact 8-bit unsigned multiplier | 0.2% error threshold; operand truncation | p.14 |
| area reduction | half | original adder area | FreePDK 45-nm / Yosys-ABC; 2020 | exact 32-bit adder | 0.1% maximum error; BLASYS | p.15 |
| resulting area | less than 30% | original area | FreePDK 45-nm / Yosys-ABC; 2020 | exact 4-bit multiply–add | 14% maximum error; CC and BLASYS | p.15 |
| runtime ratio | 22× | BLASYS/ABACUS runtime | UNKNOWN; 2020 | ABACUS | eight-point FFT comparison | p.16 |
errors_and_checks: CC guarantees that actual output error does not exceed its maximum-error threshold, while GLP and BLASYS provide soft bounds from Monte Carlo evaluation; AIG rewriting uses SAT to guarantee its error bound, and SCALS attaches a confidence level through hypothesis testing (pp.7, 12, 14-15).
conditions: Structural methods are beneficial for large circuits when the exact circuit structure approximates a useful inexact structure (p.16). Rewriting methods require scalable representations or partitioning, which can reduce optimality (pp.16-17). Gate/Boolean methods provide finer approximation control, while AHLS produces coarser points with better scalability and more interpretable designs (p.16).
evidence: Figs. 3, 7-21; Sections III-VI; Table 2 (pp.2, 6-17)

### error_analysis_quality  (role: analyzes)
mechanism: Error profiling encodes outputs in their intended numeric representation and measures the distance between exact f and approximate f˜. The survey distinguishes maximum/average magnitude, squared/relative error, Hamming distance, and error rate. Evaluation uses exhaustive simulation, Monte Carlo sampling, SAT/BDD methods, statistical certification, change-propagation matrices, or conservative propagated bounds (pp.4-5).
choices:
  metric: [er, med, mred, wce]   # p.4
  model: [exhaustive_sim, monte_carlo]   # pp.4-5
  composition_across_blocks: true   # pp.4, 13
new_choices:
  estimation_method: {statistical_hypothesis_testing, change_propagation_matrix, node_significance_propagation, partition_and_propagate, sat_evaluation, bdd_evaluation} — scalable alternatives or complements to exhaustive error evaluation   # pp.5-8
  structural_cost_metric: {approximate_efficiency, significance, activity, significance_activity_product} — circuit-cost information combined with induced error during transformation selection   # pp.4, 6
slots: none
parameters: CPM size M × N × O; P&P subgraphs limited to Is inputs; five million input combinations in the reported 32-bit-adder activity example   # pp.5-6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| batch error-estimation complexity | O(MOT) | asymptotic operations | UNKNOWN; result year UNKNOWN | O(MNT) naïve Monte Carlo | CPM evaluates T candidate transformations for M patterns, N nodes, and O outputs | p.5 |
| P&P complexity | O(N + S + E) | asymptotic operations | UNKNOWN; result year UNKNOWN | UNKNOWN | N nodes, S subgraphs, and E inter-subgraph edges | p.6 |
| activity-computation time | 15–20 min | min | UNKNOWN; result year UNKNOWN | UNKNOWN | 32-bit adder with five million input combinations | p.7 |
errors_and_checks: Monte Carlo provides an unbiased estimate for average errors but cannot guarantee maximum-error thresholds or account for unsampled outliers. Conservative reachable-output significance bounds guarantee an upper bound but overestimate errors because they ignore masking; P&P derives tighter maximum-error bounds (pp.5-6).
conditions: Exact error computation grows exponentially with input precision, so exhaustive evaluation becomes intractable for large circuits (pp.4-5). Application-level QoR may instead require SNR, SSIM, or classification accuracy measured over representative inputs (p.4).
evidence: Section II; Figs. 4-6 (pp.3-6)

## new_families
none

## space_gaps
* `approximate_logic_synthesis.method` omits gate pruning, stochastic netlist transformation, Boolean matrix factorization, BDD/AIG rewriting, bit-width reduction, operator substitution, expression rewriting, and loop transformation (pp.6-13).
* `error_analysis_quality.metric` omits Hamming distance and mean squared error, both explicitly defined or used by the survey (p.4).
* `error_analysis_quality.model` omits statistical hypothesis testing, change-propagation matrices, node-significance propagation, and partition-and-propagate bounds (pp.5-8).
* `approximate_logic_synthesis` lacks choices for abstraction level and search strategy, which distinguish the surveyed methods (pp.2-3, 6-13).

## open_questions
* The supplied document uses accepted-manuscript pages 1-19, while the citation identifies final journal pages 2195-2213.
* Table 1 and most individual points in Figs. 18-21 are not numerically transcribed, so only values stated in the surrounding prose are recorded.
* The phrase “cuts the multiplier’s area by half” is preserved because the document does not state whether the plotted area ratio is exactly 50% (p.14).
