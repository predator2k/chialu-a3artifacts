---
handle: mrazek2019
citation: V. Mrazek, M. A. Hanif, Z. Vasicek, L. Sekanina, M. Shafique, "autoAx: An Automatic Design Space Exploration and Circuit Building Methodology Utilizing Libraries of Approximate Components", 56th Design Automation Conference (DAC), 2019
actual_citation: same
status: out_of_scope
kind: paper
unit_classes: [other]
formats: [int8, int9, int10, int16]
authority: incremental
pages_read: 6 / 6
---

## summary
autoAx searches assignments of pre-characterized approximate adders/subtractors/multipliers to accelerator operations and constructs a QoR/hardware-cost Pareto frontier using machine-learned estimation models and stochastic hill climbing (pp.1–3). The work evaluates Sobel and Gaussian-filter accelerators, but it deliberately assumes nothing about the internal structure of each arithmetic component, so it does not establish an arithmetic-unit microarchitecture (pp.2,4).

## families
### error_analysis_quality  (role: extends)
mechanism: Each operation is profiled on application benchmark data to obtain an input probability mass function D_k. The probability mass function weights the absolute difference between exact operation M and approximate implementation M̃ to produce WMED_k. Vectors of component WMED values train an accelerator-level QoR model, while component power/area/delay values train a hardware-cost model. Model fidelity measures whether estimated pairwise orderings agree with real orderings. Final candidates receive precise QoR and hardware values through simulation and synthesis. # pp.3–5
choices:
  metric: wmed [outside domain]   # p.3
  model: regression_selected   # pp.3–5
  composition_across_blocks: true   # pp.3–5
new_choices:
  optimization_criterion: pairwise_fidelity — whether estimated values preserve the real <, = or > relation between configurations   # p.3
  application_metric: SSIM — accelerator-output quality metric used for all three image-processing case studies   # p.4
slots:
  none
parameters: 1500 training and 1500 testing configurations for Sobel ED; 4000 training and 1000 testing configurations for each Gaussian filter; random forest with 100 trees selected for Sobel ED   # pp.4–6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| Sobel SSIM-model fidelity | 96% | test fidelity | 45 nm ASIC / 2019 | naïve model: 90% | random forest, 1500 testing configurations | p.5 |
| Sobel area-model fidelity | 92% | test fidelity | 45 nm ASIC / 2019 | naïve model: 88% | random forest, 1500 testing configurations | p.5 |
| Fixed GF QoR-model fidelity | 92% | fidelity | 45 nm ASIC / 2019 | UNKNOWN | random forest, 1000 testing configurations | p.6 |
| Fixed GF area-model fidelity | 87% | fidelity | 45 nm ASIC / 2019 | UNKNOWN | random forest, 1000 testing configurations | p.6 |
| Generic GF QoR-model fidelity | 89% | fidelity | 45 nm ASIC / 2019 | UNKNOWN | random forest, 1000 testing configurations | p.6 |
| Generic GF hardware-model fidelity | 89% | fidelity | 45 nm ASIC / 2019 | UNKNOWN | random forest, 1000 testing configurations | p.6 |
errors_and_checks: WMED_k = Σ_i∈I D_k(i)·|M(i)−M̃(i)| scores each library component under the profiled application distribution; accelerator QoR is evaluated with average SSIM. The paper reports model fidelity rather than a bound on composed arithmetic error. # pp.3–5
conditions: The method requires hardware/software accelerator models, benchmark data, and libraries whose components are characterized for error and hardware parameters. The method handles arbitrary component approximation techniques, but errors between connected approximate circuits are generally not analytically composable. Model quality and the number of search iterations govern the resulting Pareto-set quality. # pp.2–4
evidence: §2.2–2.4, Algorithm 1, Tables 3–4, §4.2

## new_families
### library_based_accelerator_dse  (domain: approx: approximation methods, closest: approximate_logic_synthesis, why_not: autoAx binds complete pre-characterized approximate components to accelerator operations rather than synthesizing an approximate arithmetic-unit logic structure.)
mechanism: autoAx first filters each operation-specific component library to its application-weighted error/hardware Pareto set. Supervised models then estimate accelerator QoR and hardware cost from the selected components. A stochastic hill-climbing search changes one operation binding at a time, inserts estimated nondominated configurations into a pseudo-Pareto set, and restarts after stagnation. Simulation and synthesis assign precise values to pseudo-Pareto candidates and produce the final Pareto set. # pp.2–3
choices: component_filtering: {application_pmf_pareto}; quality_model: {supervised_regression}; hardware_model: {supervised_regression}; search: {stochastic_hill_climbing}; restart: {stagnation_random_pareto}; final_validation: {simulation_and_synthesis}   # pp.2–3
results:
| metric | value | unit | technology / device | baseline | condition | page |
| initial library size, 8-bit adders | 6979 | implementations | 45 nm ASIC / 2019 | UNKNOWN | extended EvoApprox plus QuAd/BAM libraries | p.4 |
| initial library size, 8-bit multipliers | 29911 | implementations | 45 nm ASIC / 2019 | UNKNOWN | extended EvoApprox plus QuAd/BAM libraries | p.4 |
| Sobel reduced design space | 4.92 · 10^7 | configurations | 45 nm ASIC / 2019 | 1.96 · 10^15 all possible | library pre-processing | p.6 |
| Fixed GF reduced design space | 1.73 · 10^16 | configurations | 45 nm ASIC / 2019 | 7.35 · 10^34 all possible | library pre-processing | p.6 |
| Generic GF reduced design space | 3.75 · 10^23 | configurations | 45 nm ASIC / 2019 | 7.15 · 10^63 all possible | library pre-processing | p.6 |
| Sobel final Pareto size | 62 | configurations | 45 nm ASIC / 2019 | 335 pseudo-Pareto configurations | proposed methodology | p.6 |
| Fixed GF final Pareto size | 132 | configurations | 45 nm ASIC / 2019 | 1166 pseudo-Pareto configurations | proposed methodology | p.6 |
| Generic GF final Pareto size | 102 | configurations | 45 nm ASIC / 2019 | 946 pseudo-Pareto configurations | proposed methodology | p.6 |
| configuration analysis time | 10 | s | UNKNOWN / 2019 | model estimation: 0.01 s | synthesis and simulation run in parallel | p.6 |
| Generic GF total exploration time | 17 | hours | common desktop / 2019 | exhaustive reduced-space analysis: 10^17 years | 4000 training, 10^6 model-search iterations, about 1000 precise analyses | p.6 |
| estimated-search alternative | 115 | days | UNKNOWN / 2019 | proposed approach: 17 hours | precise analysis replaces model estimation for 10^6 configurations | p.6 |
evidence: Figure 1, Algorithm 1, Tables 1–5, §§2–4

## space_gaps
* `error_analysis_quality.metric` lacks `wmed`, the application-PMF-weighted mean error distance used to characterize library components. # p.3
* The vocabulary lacks an accelerator-level family for library binding, learned QoR/hardware models, heuristic Pareto search, and precise final validation. # pp.2–3
* A component-library slot would need to accept heterogeneous approximate adders/subtractors/multipliers without claiming a shared internal microarchitecture. # pp.2,4

## open_questions
* The document does not identify the internal family of any selected approximate adder, subtractor, or multiplier and explicitly permits arbitrary approximation techniques. # p.2
* Figure 5 does not print numerical area/energy/SSIM coordinates for the final Pareto-front designs. # p.6
* The common desktop used for the 17-hour exploration is not specified. # p.6
