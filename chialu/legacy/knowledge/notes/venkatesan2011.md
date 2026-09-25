---
handle: venkatesan2011
citation: R. Venkatesan, A. Agarwal, K. Roy, A. Raghunathan, "MACACO: Modeling and Analysis of Circuits for Approximate Computing", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), pp. 667-673, 2011
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [binary_fixed_width]
authority: incremental
pages_read: 667-673 / 7
---

## summary
MACACO models timing-induced and functional approximations against a correct reference and computes worst-case error/error probability/error distributions. The methodology converts timing behavior into an equivalent untimed circuit, constructs a virtual error circuit, and analyzes that circuit with SAT/BDDs/Monte-Carlo simulation. # p.667, p.669-671

## families
### error_analysis_quality  (role: proposes)
mechanism: EUREkA duplicates nodes on critical paths to construct an equivalent untimed circuit whose untimed behavior matches the scaled circuit’s timed behavior. A virtual error circuit subtracts the approximate output from the reference output. A pseudo-Boolean SAT solver maximizes error, BDD traversal computes error probabilities/distributions, and Monte-Carlo simulation handles cases where BDD construction is infeasible. # p.669-671
choices:
  metric: [wce, er]   # p.669, p.671
  model: monte_carlo   # p.671
new_choices:
  analysis_engine: {pseudo_boolean_sat, bdd, monte_carlo} — selects worst-case optimization, exact distribution analysis, or statistical estimation   # p.671
  timing_model_conversion: equivalent_untimed_circuit — converts voltage/frequency timing failures into a Boolean circuit over current/previous inputs   # p.669-670
  additional_metric: {average_case_error, error_distribution} — metrics outside the declared metric domain   # p.667, p.669
slots:
  none
parameters: 32-bit RCA/CLA/HCA, 8-bit Wallace Tree multiplier with 16-bit RCA, 16-bit DSEC accumulator; Monte-Carlo confidence level 95%   # p.671-673
results:
| metric | value | unit | technology / device | baseline | condition | page |
| logic complexity | 62 | gates | UNKNOWN (2011) | none | RCA | p.673 |
| analysis runtime (BDD/MC/SAT) | 4/5.43/0.6 | Sec | UNKNOWN (2011) | same RCA | RCA | p.673 |
| logic complexity | 203 | gates | UNKNOWN (2011) | none | CLA | p.673 |
| analysis runtime (BDD/MC/SAT) | 5/5.55/0.9 | Sec | UNKNOWN (2011) | same CLA | CLA | p.673 |
| logic complexity | 362 | gates | UNKNOWN (2011) | none | HCA | p.673 |
| analysis runtime (BDD/MC/SAT) | 7/5.35/1 | Sec | UNKNOWN (2011) | same HCA | HCA | p.673 |
| logic complexity | 401 | gates | UNKNOWN (2011) | none | WTM | p.673 |
| analysis runtime (BDD/MC/SAT) | 17/6.40/1.2 | Sec | UNKNOWN (2011) | same WTM | WTM | p.673 |
| logic complexity | 160 | gates | UNKNOWN (2011) | none | TTA average | p.673 |
| analysis runtime (BDD/MC/SAT) | 0.48/4.34/0.1 | Sec | UNKNOWN (2011) | same TTA | average over truth-table approximations | p.673 |
errors_and_checks: SAT computes the maximum error; BDD analysis computes exact error probability/distribution when the BDD is feasible; Monte-Carlo estimates distributions at 95% confidence, with the margin of error selected through the stated sample-size equation. No fault model/detection coverage/false-alarm result is reported. # p.671-673
conditions: BDD runtime depends on whether the virtual error circuit has an efficient BDD representation, and BDD analysis is slower than Monte-Carlo for the evaluated multiplier. SAT is faster in the reported experiments but produces only worst-case error. Inputs are assumed equiprobable and current/previous inputs are assumed uncorrelated. # p.671-673
evidence: Abstract; Fig. 2; Algorithm 1; Fig. 4; §IV-A-B; Table I, p.667, p.669-673

### ripple_carry  (role: compares)
mechanism: A 32-bit ripple-carry adder is evaluated under frequency over-scaling. The architecture has fewer long paths, so outputs fail gradually and error probability increases slowly as scaling increases. # p.668, p.672
choices:
  none
new_choices:
  none
slots:
  none
parameters: 32-bit; frequency scaling through 50%   # p.671-672
results:
| metric | value | unit | technology / device | baseline | condition | page |
| error-distribution peak | near zero | normalized error | UNKNOWN (2011) | correct RCA | 50% frequency over-scaling | p.672 |
errors_and_checks: Error distribution is computed; no fixed accuracy bound is reported. # p.672
conditions: Functional correlation among failing output bits frequently compensates error, so observed magnitudes remain small for many inputs. # p.672
evidence: Fig. 5(a); §V-B, p.671-672

### carry_lookahead  (role: compares)
mechanism: A 32-bit carry-lookahead adder is evaluated under frequency over-scaling, with its error distribution flattening as more paths fail. # p.671-672
choices:
  none
new_choices:
  none
slots:
  none
parameters: 32-bit; multiple frequency-scaling levels   # p.671-672
results:
| metric | value | unit | technology / device | baseline | condition | page |
| input cases with error below threshold | 90 | % | UNKNOWN (2011) | correct CLA | error below 30% at all evaluated scaling levels | p.672 |
errors_and_checks: Positive and negative error probabilities differ because over-scaling introduces asymmetry. # p.672
conditions: The error distribution flattens with increased over-scaling. # p.672
evidence: Fig. 5(b); §V-B, p.671-672

### parallel_prefix  (role: compares)
mechanism: The evaluated 32-bit Han-Carlson adder merges carries on even bits and transmits odd-bit generate/propagate signals through the prefix tree. Many odd bits fail under small clock-period reductions, which produces clustered high-magnitude errors. # p.672
choices:
  topology: han_carlson   # p.668, p.671-672
new_choices:
  none
slots:
  none
parameters: 32-bit   # p.671
results:
| metric | value | unit | technology / device | baseline | condition | page |
| probability in three error peaks | more than 90 | % | UNKNOWN (2011) | correct HCA | frequency over-scaling | p.672 |
errors_and_checks: Error probability/distribution is reported; no maximum-error bound is established. # p.672
conditions: Zero-error probability drops rapidly and peaks occur near 50% normalized error, so the evaluated HCA scales poorly. # p.672
evidence: Fig. 5(c); §V-B, p.671-672

### segmented_carry_speculative  (role: compares)
mechanism: DSEC divides an accumulator into smaller adders according to the degree of over-scaling. Ignored inter-section carries are accumulated, and a correction cycle adjusts the accumulator value. # p.668
choices:
  correction: extra_cycle   # p.668
new_choices:
  segmentation_pattern: {358, 457, 466, 556} — ordered widths of the accumulator’s adder stages   # p.672-673
slots:
  none
parameters: 16-bit accumulator; segmentation patterns 358/457/466/556   # p.671-673
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum error | bounded, value not tabulated | normalized error | UNKNOWN (2011) | exact accumulator | 358 segmentation when delay is decreased to 50% | p.672 |
errors_and_checks: Ignored carries are compensated in a later correction cycle; exact correction latency/remaining error is not quantified. # p.668, p.672
conditions: Different segmentations support different over-scaling levels; 556 fails with a small amount of over-scaling, while 358 remains bounded at the stated reduction. # p.672
evidence: Fig. 1(a); Fig. 8(a); §III; §V-C, p.668, p.672

### lower_part_approximate  (role: compares)
mechanism: Reverse carry propagation partitions a 32-bit adder so approximations occur in lower-order bits. The lower-order outputs fail first under over-scaling, which limits error magnitude relative to designs whose MSB fails first. # p.669, p.672-673
choices:
  lower_cell: reverse_carry_rcpa   # p.668-669
new_choices:
  forward_path_partition: {FOR8, FOR10, FOR12} — number of MSBs in the forward propagation path   # p.672-673
slots:
  upper_adder: ripple_carry   # p.672-673
parameters: 32-bit RCA-based adder; FOR8/FOR10/FOR12 partitions   # p.672-673
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum error | partition-dependent | normalized error | UNKNOWN (2011) | exact 32-bit RCA | RCP under frequency over-scaling | p.672-673 |
errors_and_checks: The initial functional error and subsequent maximum error depend on the partition; no exact bound is printed in the text. # p.672-673
conditions: Functional correlation among failing bits can reduce maximum error as over-scaling increases. # p.672-673
evidence: Fig. 1(c); Fig. 8(b); §III; §V-C, p.668-669, p.672-673

## new_families
### truth_table_approximate_adder  (domain: approx: approximate adders, closest: lower_part_approximate, why_not: the paper alters a full-adder truth table without establishing an exact-upper/approximate-lower partition)
mechanism: Selected full-adder truth-table entries are changed to simplify the implementation. The resulting error distribution depends on how many inputs produce an erroneous sum and whether carry-bit errors compensate or exacerbate sum-bit errors. # p.668-669, p.672
choices: erroneous_sum_input_count: Int[2..3:1]; carry_error_interaction: {none, compensating, exacerbating}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| compared implementations | 4 | adders | UNKNOWN (2011) | exact full-adder truth table | Adder1-Adder4 | p.672 |
evidence: Fig. 1(b); Fig. 7; §III; §V-B, p.668-669, p.672

### wallace_tree_multiplier  (domain: mul: integer multipliers, closest: carry_save_array, why_not: the vocabulary lacks a Wallace reduction-tree family and the document does not describe a regular 2-D CSA array)
mechanism: The evaluated 8-bit Wallace Tree multiplier uses a 16-bit ripple-carry adder at its final stage. Its critical path passes through that RCA, which makes its over-scaling behavior comparatively gradual. # p.671-672
choices: final_adder: {ripple_carry}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| input cases with error below threshold | 94 | % | UNKNOWN (2011) | correct WTM | error below 12.5% at 13% frequency scaling | p.672 |
evidence: Fig. 6; §V-B, p.671-672

## space_gaps
* `error_analysis_quality.metric` lacks average-case error and full error-distribution values. # p.667, p.669
* `error_analysis_quality.model` lacks exact BDD traversal and pseudo-Boolean SAT optimization. # p.671
* `segmented_carry_speculative` lacks nonuniform segmentation patterns and correction-term accumulation. # p.668, p.672

## open_questions
* The technology node/cell library is not identified, so every reported result retains `UNKNOWN`. # p.671
* The printed text does not define the denominator used for “% Error”/“Normalized Error,” so the merge pass must not reinterpret those quantities. # p.672-673
* The exact truth tables for Adder1-Adder4 and numerical Fig. 8 maximum-error values are not provided in the included text. # p.672-673
