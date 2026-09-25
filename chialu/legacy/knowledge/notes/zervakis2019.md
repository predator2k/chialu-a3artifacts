---
handle: zervakis2019
citation: G. Zervakis, S. Xydis, D. Soudris, K. Pekmestzi, "Multi-Level Approximate Accelerator Synthesis Under Voltage Island Constraints", IEEE Transactions on Circuits and Systems II, vol. 66, no. 4, pp. 607-611, 2019
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC, other]
formats: [int8, int16]
authority: incremental
pages_read: 5 / 5
---

## summary
The document proposes a DFG-level synthesis framework that assigns algorithmic/logic/circuit approximations to arithmetic nodes under global error and voltage-island constraints. The framework uses Pareto-pruned arithmetic libraries, an ANN error model, a power proxy, binary search, and greedy voltage-island grouping to produce power-optimized approximate accelerators. Evaluation covers pipelined matrix multiplication/Sobel/DCT benchmarks in TSMC 65nm. (pp.1-5)

## families
### pp_perforation  (role: instantiates)
mechanism: Partial-product perforation supplies the algorithmic-level approximation for multiplier nodes in the multi-level arithmetic library. (p.2)
choices:
  correction: none   # p.2
new_choices:
  none
slots:
  none
parameters: 8-bit Dadda multiplier evaluation instance; perforated-row count UNKNOWN.   # p.2
results: none
errors_and_checks: Pareto configurations in Fig. 1 are restricted to MRED≤10%.   # p.2
conditions: Partial-product perforation is combined with an inexact 4:2 compressor and voltage overscaling rather than evaluated only as an isolated multiplier architecture.   # p.2
evidence: §II; Fig. 1, p.2

### approximate_compressor_tree  (role: instantiates)
mechanism: An inexact 4:2 compressor from Momeni et al. is used as the logic-level approximation in Dadda multiplier nodes. The compressor variant and approximate-column count are not identified. (p.2)
choices:
new_choices:
  none
slots:
  none
parameters: 8-bit Dadda multiplier evaluation instance; approximate_columns UNKNOWN.   # p.2
results: none
errors_and_checks: Pareto configurations in Fig. 1 are restricted to MRED≤10%.   # p.2
conditions: The inexact compressor is coordinated with partial-product perforation and voltage overscaling.   # p.2
evidence: §II; Fig. 1, p.2

### lower_part_approximate  (role: instantiates)
mechanism: Adder/subtractor nodes use truncation at the algorithmic level and an approximate full adder from Gupta et al. at the logic level. The truncated width and exact full-adder variant are not identified. (p.2)
choices:
new_choices:
  none
slots:
  none
parameters: 16-bit ripple-carry adder evaluation instance; lower_width UNKNOWN.   # p.2
results: none
errors_and_checks: Pareto configurations in Fig. 1 are restricted to MRED≤10%.   # p.2
conditions: Truncation and approximate full-adder cells are coordinated with voltage overscaling.   # p.2
evidence: §II; Fig. 1, p.2

### ripple_carry  (role: instantiates)
mechanism: A 16-bit ripple-carry adder is the concrete adder architecture used to illustrate the multi-level power-error Pareto configurations. (p.2)
choices:
new_choices:
  none
slots:
  full_adder_cell: lower_part_approximate   # p.2
parameters: 16-bit; nominal Voltage 1V; MRED≤10%.   # p.2
results: none
errors_and_checks: MRED≤10% for the configurations plotted in Fig. 1.   # p.2
conditions: The document states that the adopted approximation techniques can be applied to any adder/subtractor architecture, so ripple carry is an evaluation instance rather than a framework restriction.   # p.2
evidence: §II; Fig. 1, p.2

### error_analysis_quality  (role: extends)
mechanism: MRED constrains arithmetic-library and accelerator configurations. An ANN learns DFG output error from node-level unbiased error values, while synthesized VOS-aware simulations supply training data and SPICE-accurate simulations validate selected designs. (pp.2-4)
choices:
  metric: mred   # pp.2,4
  model: ANN [outside domain]   # pp.2-3
new_choices:
  reference_evaluation: SPICE-accurate simulation — supplies golden power/error values for exhaustive exploration and selected framework designs.   # p.4
slots:
  none
parameters: K training configurations; 50,000 training inputs and 50,000 evaluation inputs per benchmark.   # pp.3-4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| error-model MSE | 8 × 10−5 | MSE | TSMC 65nm / 2019 | SPICE-accurate simulation | matrix multiplication | p.4 |
| power-model MSE | 8 × 10−7 | MSE | TSMC 65nm / 2019 | SPICE-accurate simulation | matrix multiplication | p.4 |
| error-model MSE | 1 × 10−4 | MSE | TSMC 65nm / 2019 | SPICE-accurate simulation | Sobel | p.4 |
| power-model MSE | 4 × 10−7 | MSE | TSMC 65nm / 2019 | SPICE-accurate simulation | Sobel | p.4 |
| VIG power-model MSE | 7.81 × 10−7 | MSE | TSMC 65nm / 2019 | exhaustive voltage-island grouping | matrix multiplication | p.5 |
errors_and_checks: VOS configurations producing unknown states are assigned infinite error; selected configurations are synthesized and simulated to obtain their “exact” error.   # pp.3-4
conditions: The ANN is trained on realistic DFG output errors from synthesized algorithmic/logic configurations followed by VOS-aware gate-level simulation.   # p.2
evidence: Algorithm 1, pp.2-3; §IV, pp.4-5

## new_families
### multi_level_approximate_accelerator_synthesis  (domain: approx: approximation methods, closest: approximate_logic_synthesis, why_not: The mechanism jointly assigns algorithmic/logic/circuit approximations across a DFG and groups voltage islands, which the circuit-level synthesis family does not represent.)
mechanism: Each arithmetic node receives a Pareto-optimal multi-level configuration. Random DFG configurations train an ANN error model, and summed node power supplies a proxy. Estimated configurations form a DFG Pareto front, on which binary search selects the highest-error design within the bound and verifies it by simulation. Greedy voltage-island grouping selects at most IC supply values and only raises node voltages, minimizing estimated power increase. (pp.2-3)
choices:
  approximation_layers: {algorithmic, logic, circuit_VOS, combined}
  error_budget_assignment: {per_node_DFG_annotation}
  error_model: {ANN}
  configuration_search: {Pareto_pruning_binary_search}
  voltage_island_grouping: {greedy_raise_only}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| synthesis speedup | 589× | × | TSMC 65nm / 2019 | exhaustive search | matrix multiplication; 120 training configurations | p.4 |
| synthesis speedup | 1827× | × | TSMC 65nm / 2019 | exhaustive search | Sobel; 200 training configurations | p.4 |
| synthesis speedup without VOSsim | 34× | × | TSMC 65nm / 2019 | exhaustive search | matrix multiplication | p.4 |
| synthesis speedup without VOSsim | 63× | × | TSMC 65nm / 2019 | exhaustive search | Sobel | p.4 |
| power reduction | 61% | less power | TSMC 65nm / 2019 | accurate design | Sobel; MRED bound 5%; no IC constraint | p.5 |
| power reduction | 40% | less power | TSMC 65nm / 2019 | accurate design | matrix multiplication; MRED bound 5%; no IC constraint | p.5 |
| power reduction | 49% | less power | TSMC 65nm / 2019 | accurate design | DCT; MRED bound 5%; no IC constraint | p.5 |
| power reduction | 24% | less power | TSMC 65nm / 2019 | best single-level technique | Sobel; MRED bound 5%; no IC constraint | p.5 |
| power reduction | 9% | less power | TSMC 65nm / 2019 | best single-level technique | matrix multiplication; MRED bound 5%; no IC constraint | p.5 |
| power reduction | 20% | less power | TSMC 65nm / 2019 | best single-level technique | DCT; MRED bound 5%; no IC constraint | p.5 |
| power reduction | 60% | less power | TSMC 65nm / 2019 | accurate design | Sobel; MRED bound 5%; IC=1 | p.5 |
| power reduction | 39% | less power | TSMC 65nm / 2019 | accurate design | matrix multiplication; MRED bound 5%; IC=1 | p.5 |
| power reduction | 48.5% | less power | TSMC 65nm / 2019 | accurate design | DCT; MRED bound 5%; IC=1 | p.5 |
| power reduction | 71% | less power | TSMC 65nm / 2019 | accurate design | Sobel; MRED bound 10%; no IC constraint | p.5 |
| power reduction | 57% | less power | TSMC 65nm / 2019 | accurate design | matrix multiplication; MRED bound 10%; no IC constraint | p.5 |
| power reduction | 57% | less power | TSMC 65nm / 2019 | accurate design | DCT; MRED bound 10%; no IC constraint | p.5 |
| VIG power overhead | 0.5% | power | TSMC 65nm / 2019 | no island constraint | matrix multiplication; MRED bound 5%; IC=2 | p.5 |
| VIG power overhead | 2% | power | TSMC 65nm / 2019 | no island constraint | matrix multiplication; MRED bound 5%; IC=1 | p.5 |
| VIG power overhead | 0.2% | power | TSMC 65nm / 2019 | no island constraint | matrix multiplication; MRED bound 10%; IC=3 | p.5 |
| VIG power overhead | 1% | power | TSMC 65nm / 2019 | no island constraint | matrix multiplication; MRED bound 10%; IC=2 | p.5 |
| VIG power overhead | 3% | power | TSMC 65nm / 2019 | no island constraint | matrix multiplication; MRED bound 10%; IC=1 | p.5 |
evidence: Fig. 2 and Algorithms 1-2, pp.2-3; Figs. 3-4 and Table I, pp.4-5

## space_gaps
* `approximate_logic_synthesis.method` lacks DFG-level joint selection of algorithmic/logic/VOS approximations using learned error propagation. (pp.2-3)
* `error_analysis_quality.model` lacks ANN-based DFG error modeling. (pp.2-3)
* The multiplier vocabulary lacks Dadda-tree reduction as an explicit reduction family or slot value. (p.2)
* Approximation families lack voltage overscaling as a circuit-level approximation choice. (pp.1-3)
* Voltage-island count/grouping is not represented as a cross-node accelerator synthesis choice. (pp.2-3)

## open_questions
* The document does not identify the number of perforated partial-product rows. (p.2)
* The document does not identify which inexact 4:2 compressor variant from [12] is used. (p.2)
* The document does not identify the truncation width or approximate full-adder variant for adders/subtractors. (p.2)
* The DCT design is not compared with exhaustive exploration because one SPICE-accurate simulation requires 58h. (p.4)
