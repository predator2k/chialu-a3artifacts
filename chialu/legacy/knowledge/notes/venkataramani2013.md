---
handle: venkataramani2013
citation: S. Venkataramani, K. Roy, A. Raghunathan, "Substitute-and-Simplify: A Unified Design Paradigm for Approximate and Quality Configurable Circuits", Design, Automation and Test in Europe (DATE), pp. 1367-1372, 2013
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC, other]
formats: [int32, UNKNOWN]
authority: incremental
pages_read: 6 / 6
---

## summary
SASIMI automatically substitutes highly correlated internal signals and simplifies the resulting circuit while enforcing a specified output-error constraint. The method synthesizes approximate adders/multipliers/MACs and other datapaths, and its quality-configurable extension selectively recomputes substitution fanout in an additional cycle.

## families
### approximate_logic_synthesis  (role: proposes)
mechanism: SASIMI identifies a target signal TS and a substitute SS that are equal with high probability. Replacing TS permits deletion of its exclusive logic cone and downsizing of timing-relaxed fanout logic. An iterative synthesis loop scores candidates using deletion potential, downsizing potential and Pdiff, performs the best substitution, simplifies the circuit, and retains the last implementation satisfying the output-error constraint.
choices:
  method: signal_substitution [outside domain]   # pp.2-4
  error_constraint: er   # p.5
  error_constraint: med   # p.5
new_choices:
  candidate_objective: deletion_downsizing_error_score — weights removable logic/timing slack against Pdiff   # p.4
slots: none
parameters: 32-bit Kogge-Stone adder in the delay sweep; α=0.75 for approximate synthesis; iterative substitutions; latency/II otherwise UNKNOWN   # pp.4-6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area reduction | 15%-25% | % | IBM 45nm; 2013 | accurate original, iso-delay | ISCAS85; error rate <0.5% | p.5 |
| power reduction | 10%-28% | % | IBM 45nm; 2013 | accurate original, iso-delay | ISCAS85; error rate <0.5% | p.5 |
| area improvement | 30%-60% | % | IBM 45nm; 2013 | accurate original, iso-delay | ISCAS85; error rate <2% | p.5 |
| power improvement | 30%-60% | % | IBM 45nm; 2013 | accurate original, iso-delay | ISCAS85; error rate <2% | p.5 |
| area improvement | 15%-65% | % | IBM 45nm; 2013 | accurate original, iso-delay | average error <0.5% maximum value | p.5 |
| power improvement | 20%-68% | % | IBM 45nm; 2013 | accurate original, iso-delay | average error <0.5% maximum value | p.5 |
errors_and_checks: Error rate is the percentage of input vectors for which Oorig differs from Oapprox. Average error magnitude is the mean of |Oorig−Oapprox|. All inputs are treated as equiprobable; output-bit difference probabilities are weighted by numerical significance for average-error estimation.   # p.5
conditions: Substitutions must not create combinational cycles or affect outputs that cannot tolerate errors. Candidate selection estimates output error separately because TS≠SS need not propagate to an output. Results include adders, multipliers, MAC, SAD, FFT butterfly, Euclidean distance and ISCAS85 circuits.   # pp.3-5
evidence: Algorithms 1-2; §III-A/III-C; §IV; Figures 4-6.

## new_families
### quality_configurable_logic_synthesis  (domain: approx, closest: accuracy_configurable, why_not: accuracy_configurable is an approximate-adder family, while SASIMI configures arbitrary synthesized circuits through detected substitutions and variable-latency recovery)
mechanism: The circuit retains TS logic and monitors every TS/SS difference. Approximate modes accept selected substitutions in one cycle. Accurate or tighter modes accumulate difference signals and selectively extend the clock by one cycle, switch affected substitution circuits back to TS, and recompute downstream logic. Substitutions are nested across quality modes, so tighter modes recover a strict superset of the errors recovered by looser modes.
choices:
  mode_count: Int[2..N]
  recovery: {none, selective_extra_cycle, universal_extra_cycle}
  substitution_grouping: {nested_by_quality_constraint}
  clock_extension_power_gating: Bool
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 0.65 | ns | IBM 45nm; 2013 | accurate original | RCA; AEM | p.6 |
| area reduction | 16.2 | % | IBM 45nm; 2013 | accurate original | RCA; AEM | p.6 |
| power reduction | 21.6 | % | IBM 45nm; 2013 | accurate original | RCA; AEM | p.6 |
| two-cycle probability | 0.24 | % | IBM 45nm; 2013 | accurate mode | RCA; AEM | p.6 |
| accurate energy saving | 2.69 | % | IBM 45nm; 2013 | accurate original | RCA; AEM | p.6 |
| approximate energy saving | 36.7 | % | IBM 45nm; 2013 | accurate original | RCA; AEM | p.6 |
| average error | 0.03 | % | IBM 45nm; 2013 | exact output | RCA; approximate mode | p.6 |
| delay | 0.17 | ns | IBM 45nm; 2013 | accurate original | CLA; AEM | p.6 |
| area reduction | 29.5 | % | IBM 45nm; 2013 | accurate original | CLA; AEM | p.6 |
| power reduction | 26.72 | % | IBM 45nm; 2013 | accurate original | CLA; AEM | p.6 |
| two-cycle probability | 0.067 | % | IBM 45nm; 2013 | accurate mode | CLA; AEM | p.6 |
| accurate energy saving | 21.8 | % | IBM 45nm; 2013 | accurate original | CLA; AEM | p.6 |
| approximate energy saving | 34.9 | % | IBM 45nm; 2013 | accurate original | CLA; AEM | p.6 |
| average error | 0.01 | % | IBM 45nm; 2013 | exact output | CLA; approximate mode | p.6 |
| delay | 0.55 | ns | IBM 45nm; 2013 | accurate original | MAC; AEM | p.6 |
| area reduction | 13.7 | % | IBM 45nm; 2013 | accurate original | MAC; AEM | p.6 |
| power reduction | 16.8 | % | IBM 45nm; 2013 | accurate original | MAC; AEM | p.6 |
| two-cycle probability | 0.014 | % | IBM 45nm; 2013 | accurate mode | MAC; AEM | p.6 |
| accurate energy saving | 15.6 | % | IBM 45nm; 2013 | accurate original | MAC; AEM | p.6 |
| approximate energy saving | 18.3 | % | IBM 45nm; 2013 | accurate original | MAC; AEM | p.6 |
| average error | 0.01 | % | IBM 45nm; 2013 | exact output | MAC; approximate mode | p.6 |
| delay | 0.47 | ns | IBM 45nm; 2013 | accurate original | EUDIST; AEM | p.6 |
| area reduction | 24.1 | % | IBM 45nm; 2013 | accurate original | EUDIST; AEM | p.6 |
| power reduction | 22.24 | % | IBM 45nm; 2013 | accurate original | EUDIST; AEM | p.6 |
| two-cycle probability | 0.0075 | % | IBM 45nm; 2013 | accurate mode | EUDIST; AEM | p.6 |
| accurate energy saving | 21.6 | % | IBM 45nm; 2013 | accurate original | EUDIST; AEM | p.6 |
| approximate energy saving | 24 | % | IBM 45nm; 2013 | accurate original | EUDIST; AEM | p.6 |
| average error | 0.12 | % | IBM 45nm; 2013 | exact output | EUDIST; approximate mode | p.6 |
| delay | 0.35 | ns | IBM 45nm; 2013 | accurate original | MUL; AEM | p.6 |
| area reduction | 32.9 | % | IBM 45nm; 2013 | accurate original | MUL; AEM | p.6 |
| power reduction | 36.5 | % | IBM 45nm; 2013 | accurate original | MUL; AEM | p.6 |
| two-cycle probability | 0.05 | % | IBM 45nm; 2013 | accurate mode | MUL; AEM | p.6 |
| accurate energy saving | 33.3 | % | IBM 45nm; 2013 | accurate original | MUL; AEM | p.6 |
| approximate energy saving | 40.05 | % | IBM 45nm; 2013 | accurate original | MUL; AEM | p.6 |
| average error | 1.2 | % | IBM 45nm; 2013 | exact output | MUL; approximate mode | p.6 |
| delay | 0.5 | ns | IBM 45nm; 2013 | accurate original | SAD; AEM | p.6 |
| area reduction | 11.6 | % | IBM 45nm; 2013 | accurate original | SAD; AEM | p.6 |
| power reduction | 12.1 | % | IBM 45nm; 2013 | accurate original | SAD; AEM | p.6 |
| two-cycle probability | 0.002 | % | IBM 45nm; 2013 | accurate mode | SAD; AEM | p.6 |
| accurate energy saving | 12.0 | % | IBM 45nm; 2013 | accurate original | SAD; AEM | p.6 |
| approximate energy saving | 14.44 | % | IBM 45nm; 2013 | accurate original | SAD; AEM | p.6 |
| average error | 0.01 | % | IBM 45nm; 2013 | exact output | SAD; approximate mode | p.6 |
| delay | 0.2 | ns | IBM 45nm; 2013 | accurate original | KSA; error rate | p.6 |
| area reduction | 16.3 | % | IBM 45nm; 2013 | accurate original | KSA; error rate | p.6 |
| power reduction | 14.79 | % | IBM 45nm; 2013 | accurate original | KSA; error rate | p.6 |
| two-cycle probability | 0.009 | % | IBM 45nm; 2013 | accurate mode | KSA; error rate | p.6 |
| accurate energy saving | 14.02 | % | IBM 45nm; 2013 | accurate original | KSA; error rate | p.6 |
| approximate energy saving | 22.27 | % | IBM 45nm; 2013 | accurate original | KSA; error rate | p.6 |
| error rate | 0.7 | % | IBM 45nm; 2013 | exact output | KSA; approximate mode | p.6 |
| delay | 0.22 | ns | IBM 45nm; 2013 | accurate original | c880; error rate | p.6 |
| area reduction | 13.1 | % | IBM 45nm; 2013 | accurate original | c880; error rate | p.6 |
| power reduction | 18.03 | % | IBM 45nm; 2013 | accurate original | c880; error rate | p.6 |
| two-cycle probability | 0.064 | % | IBM 45nm; 2013 | accurate mode | c880; error rate | p.6 |
| accurate energy saving | 12.78 | % | IBM 45nm; 2013 | accurate original | c880; error rate | p.6 |
| approximate energy saving | 31.9 | % | IBM 45nm; 2013 | accurate original | c880; error rate | p.6 |
| error rate | 4.8 | % | IBM 45nm; 2013 | exact output | c880; approximate mode | p.6 |
| delay | 0.25 | ns | IBM 45nm; 2013 | accurate original | c1908; error rate | p.6 |
| area reduction | 13.8 | % | IBM 45nm; 2013 | accurate original | c1908; error rate | p.6 |
| power reduction | 22.9 | % | IBM 45nm; 2013 | accurate original | c1908; error rate | p.6 |
| two-cycle probability | 0.0102 | % | IBM 45nm; 2013 | accurate mode | c1908; error rate | p.6 |
| accurate energy saving | 22.11 | % | IBM 45nm; 2013 | accurate original | c1908; error rate | p.6 |
| approximate energy saving | 31.31 | % | IBM 45nm; 2013 | accurate original | c1908; error rate | p.6 |
| error rate | 0.95 | % | IBM 45nm; 2013 | exact output | c1908; approximate mode | p.6 |
| delay | 0.22 | ns | IBM 45nm; 2013 | accurate original | c2670; error rate | p.6 |
| area reduction | 5.09 | % | IBM 45nm; 2013 | accurate original | c2670; error rate | p.6 |
| power reduction | 15.68 | % | IBM 45nm; 2013 | accurate original | c2670; error rate | p.6 |
| two-cycle probability | 0.0051 | % | IBM 45nm; 2013 | accurate mode | c2670; error rate | p.6 |
| accurate energy saving | 15.25 | % | IBM 45nm; 2013 | accurate original | c2670; error rate | p.6 |
| approximate energy saving | 24.51 | % | IBM 45nm; 2013 | accurate original | c2670; error rate | p.6 |
| error rate | 0.2 | % | IBM 45nm; 2013 | exact output | c2670; approximate mode | p.6 |
| delay | 0.36 | ns | IBM 45nm; 2013 | accurate original | c3540; error rate | p.6 |
| area reduction | 21.94 | % | IBM 45nm; 2013 | accurate original | c3540; error rate | p.6 |
| power reduction | 19.72 | % | IBM 45nm; 2013 | accurate original | c3540; error rate | p.6 |
| two-cycle probability | 0.008 | % | IBM 45nm; 2013 | accurate mode | c3540; error rate | p.6 |
| accurate energy saving | 19.08 | % | IBM 45nm; 2013 | accurate original | c3540; error rate | p.6 |
| approximate energy saving | 23.56 | % | IBM 45nm; 2013 | accurate original | c3540; error rate | p.6 |
| error rate | 0.65 | % | IBM 45nm; 2013 | exact output | c3540; approximate mode | p.6 |
| delay | 0.32 | ns | IBM 45nm; 2013 | accurate original | c7552; error rate | p.6 |
| area reduction | 12.79 | % | IBM 45nm; 2013 | accurate original | c7552; error rate | p.6 |
| power reduction | 19.18 | % | IBM 45nm; 2013 | accurate original | c7552; error rate | p.6 |
| two-cycle probability | 0.064 | % | IBM 45nm; 2013 | accurate mode | c7552; error rate | p.6 |
| accurate energy saving | 14.01 | % | IBM 45nm; 2013 | accurate original | c7552; error rate | p.6 |
| approximate energy saving | 22.54 | % | IBM 45nm; 2013 | accurate original | c7552; error rate | p.6 |
| error rate | 4.8 | % | IBM 45nm; 2013 | exact output | c7552; approximate mode | p.6 |
evidence: Figures 2-3; Equations 1a-1d; Algorithm 3; Tables I-II; §III-B/III-C/§V-B.

## space_gaps
* approximate_logic_synthesis.method needs `signal_substitution`, because SASIMI substitutes correlated internal signals rather than using the declared methods.   # pp.2-4
* A generic quality-configurable synthesis family needs selective extra-cycle recovery/error-detection choices outside the approximate-adder-specific `accuracy_configurable` family.   # pp.3-6

## open_questions
* The widths/formats of RCA/CLA/MAC/MUL/SAD/EUDIST and Table II benchmarks are not reported.
* The number and exact constraints of quality modes beyond the evaluated two-mode circuits are not reported.
* The paper does not report formal worst-case verification of the error constraints.
