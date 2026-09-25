---
handle: lyons_vanderkulk_1962
citation: R. E. Lyons, W. Vanderkulk, "The Use of Triple-Modular Redundancy to Improve Computer Reliability", IBM Journal of Research and Development, vol. 6, no. 2, pp. 200-209, 1962
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [binary]
authority: landmark
pages_read: 200-209 / 10
---

## summary
The document proposes triple-modular redundancy for digital systems by triplicating modules and selecting the majority output through voting circuits. The document analyzes module granularity, imperfect voters, unequal module reliability, interconnection structures, and Monte Carlo reliability estimates.

## families
none

## new_families
### triple_modular_redundancy  (domain: checker: concurrent error detection, closest: duplication, why_not: duplication detects disagreement through comparison, while this mechanism masks one faulty replica by selecting the two-out-of-three majority)
mechanism: Three identical binary-output modules feed voting circuits that deliver the majority value, so failure of one module need not cause system failure. A computer is divided into triplicated module trios, with voters placed at module inputs or shared outputs according to interconnection requirements. M-units connect to other trios through voters, Q-units connect directly, and N-units remain untriplicated. Imperfect voters create an optimum module granularity rather than making finer partitioning indefinitely beneficial. # pp.200-206
choices:
  replication: {three} — number of identical modules in each redundant group # pp.200-201
  decision_rule: {two_out_of_three_majority} — rule used to select the delivered binary output # p.201
  voter_replication: {single, triple} — one voter in the original arrangement or three voters in the analyzed TMR configuration # p.201
  voter_placement: {per_driven_module_input, shared_source_output, omitted} — placement alternatives for high-fanout interconnections # pp.204-206
  connection_unit: {m_unit, q_unit, n_unit} — voted trio, directly connected trio, or non-triplicated module # pp.205-207
  module_granularity: {whole_computer, modular_partition} — level at which triplication is applied # pp.201-204
  reliability_model: {analytical_independent_failures, monte_carlo_component_failures} — calculation methods used for TMR reliability # pp.201-208
results:
| metric | value | unit | technology / device | baseline | condition | page |
| TMR reliability | 0.95 | probability | UNKNOWN; year 1962 | nonredundant computer operated for its MTF | 60 modules and perfect voting circuits | p.202 |
| assumed voter reliability | about 0.999 | probability | present-day circuits and components; year 1962 | UNKNOWN | operating periods of one or two hundred hours | p.203 |
| maximum TMR reliability | 0.988 | probability | UNKNOWN; year 1962 | nonredundant reliability 0.368 | voter reliability 0.999 and optimum m = 1000 | p.204 |
| TMR reliability | 0.95 | probability | UNKNOWN; year 1962 | nonredundant reliability 0.368 | voter reliability 0.999 and m = 67 | p.204 |
| TMR computer size | 3.20 | times nonredundant size | UNKNOWN; year 1962 | nonredundant computer | m = 67 and TMR reliability 0.95 | p.204 |
| maximum-reliability TMR computer size | approximately 6 | times nonredundant size | UNKNOWN; year 1962 | nonredundant computer | module failure rate approximately equals associated voting-circuit failure rate | p.204 |
| equal-reliability crossover time | 0.202 | MTF | UNKNOWN; year 1962 | case 3 triplicated generator without voters versus case 4 single generator | equal timing-generator failure rates; case 4 wins above the crossover | p.207 |
errors_and_checks: The model addresses permanent component failures, although the same redundancy can combat transient failures. One failed module is masked while the other two modules and required voters operate. Modified voting circuits can indicate intermittent/permanent failure locations, but numerical detection coverage, false-alarm behavior, and alias rate are not reported. # pp.200-201, p.209
conditions: TMR improves reliability only when the unreplicated module reliability exceeds 0.5, and the benefit increases as module reliability approaches unity. # p.201 TMR applied at the whole-computer level loses to the nonredundant computer for operating time greater than its MTF under the exponential model, so the computer must be partitioned into modules whose individual operating interval is short relative to their MTF. # p.201 Imperfect voters make reliability approach zero as the module count approaches infinity, which produces an optimum module count. # p.203 Unequal module/voter reliabilities reduce attainable TMR reliability, so modules should have nearly equal reliability when voting circuitry is a small fraction of the equipment. # p.204 High-fanout sources can make per-input voting less reliable than shared voting, omitted voting, or a non-triplicated source. # pp.204-207 The analytical models assume statistically independent failures and use simplifying reliability assumptions. # pp.201-207 The Monte Carlo model assumes permanent component failures, approximately constant module-selection probabilities, exponentially decaying component reliabilities, and a Poisson count of failures. # pp.207-208
evidence: Equations 1-16 and Figures 1-5 on pp.201-204; interconnection cases, Equations 17-25, and Figure 6 on pp.204-207; Monte Carlo model, Equations 26-27, and Figures 7-8 on pp.207-209.

## space_gaps
* The checker vocabulary lacks majority-voter fault masking as distinct from disagreement detection. # pp.200-201
* The vocabulary lacks voter placement and voter reliability choices, which determine the optimum TMR module granularity. # pp.203-206
* The vocabulary lacks mixed voted/direct/unreplicated interconnection units corresponding to M-units/Q-units/N-units. # pp.205-208

## open_questions
* The document does not report the component counts, module list, failure rates, or exact numerical points underlying the four Monte Carlo designs in Figures 7-8.
* The document states that modified voters can locate failures but does not specify the voter modification or its detection coverage.
