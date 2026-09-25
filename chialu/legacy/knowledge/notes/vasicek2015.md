---
handle: vasicek2015
citation: Z. Vasicek, L. Sekanina, "Evolutionary Approach to Approximate Digital Circuits Design", IEEE Transactions on Evolutionary Computation, vol. 19, no. 3, pp. 432-444, 2015
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [uint2, uint3, uint4, uint8, uint16]
authority: incremental
pages_read: 13 / 13
---

## summary
The document proposes an area-oriented Cartesian Genetic Programming method that evolves approximate combinational circuits under a fixed component budget. Gate-level multiplier experiments and functional-level median-circuit experiments show that heuristic population seeding improves solution quality and reduces evolutionary runtime.

## families
### approximate_logic_synthesis  (role: extends)
mechanism: A `(1+λ)` Cartesian Genetic Programming search minimizes the sum of absolute output errors while the chromosome dimensions limit the available gates/components. Repeated runs with decreasing resource limits produce an accuracy/area tradeoff. RS uses random populations; HS1 removes one gate from each preceding evolved solution; HS2 iteratively removes gates before independent evolutionary runs. Gate-level nodes implement Boolean functions, while functional-level nodes implement word-wide functions. # p.4–6
choices:
  method: cgp_evolution   # p.4–5
  formal_verification: none   # p.5
new_choices:
  optimization_orientation: {area_oriented, error_oriented} — whether resources or an error bound constrain synthesis   # p.3–4
  population_seeding: {RS, HS1, HS2} — random, interleaved heuristic, or precomputed heuristic seeds   # p.5
  representation_level: {gate, functional} — Boolean gates or word-wide components form CGP nodes   # p.4–5
slots:
  none
parameters: Multiplier widths `w=2,3,4`; exact sizes `nbst=7,23,59`; `nr=1`, `l=nc`, `λ=4`, `h=5%`; 50 runs per resource count; larger multipliers are composed to `w=8,16`. # p.6–9
results:
| metric | value | unit | technology / device | baseline | condition | page |
| gates | 5 | gates | MCNC library; node UNKNOWN; 2015 | none | M2, w=2 | p.10 |
| worst error | 13.33 | % | MCNC library; node UNKNOWN; 2015 | `2^(2w)-1` normalization | M2, w=2 | p.10 |
| error probability | 0.06 | - | MCNC library; node UNKNOWN; 2015 | exact product | M2, w=2 | p.10 |
| average error | 0.83 | % | MCNC library; node UNKNOWN; 2015 | `2^(2w)-1` normalization | M2, w=2 | p.10 |
| area | 6.7 | - | MCNC library; node UNKNOWN; 2015 | one NAND gate | M2, w=2 | p.10 |
| delay | 5.3 | ns | MCNC library; node UNKNOWN; 2015 | none | M2, w=2 | p.10 |
| gates | 47 | gates | MCNC library; node UNKNOWN; 2015 | none | C4, composed from M2 | p.10 |
| worst error | 19.61 | % | MCNC library; node UNKNOWN; 2015 | `2^(2w)-1` normalization | C4 | p.10 |
| average error | 1.23 | % | MCNC library; node UNKNOWN; 2015 | `2^(2w)-1` normalization | C4 | p.10 |
| area | 71.2 | - | MCNC library; node UNKNOWN; 2015 | one NAND gate | C4 | p.10 |
| delay | 38.9 | ns | MCNC library; node UNKNOWN; 2015 | none | C4 | p.10 |
| gates | 47 | gates | MCNC library; node UNKNOWN; 2015 | C4: 47 gates | E4a, evolved | p.10 |
| worst error | 3.92 | % | MCNC library; node UNKNOWN; 2015 | C4: 19.61% | E4a | p.10 |
| error probability | 0.17 | - | MCNC library; node UNKNOWN; 2015 | C4: 0.19 | E4a | p.10 |
| average error | 0.28 | % | MCNC library; node UNKNOWN; 2015 | C4: 1.23% | E4a | p.10 |
| area | 66.2 | - | MCNC library; node UNKNOWN; 2015 | C4: 71.2 | E4a | p.10 |
| delay | 34.4 | ns | MCNC library; node UNKNOWN; 2015 | C4: 38.9 ns | E4a | p.10 |
| gates | 276 | gates | MCNC library; node UNKNOWN; 2015 | C8: 276 gates | E8a | p.10 |
| worst error | 4.41 | % | MCNC library; node UNKNOWN; 2015 | C8: 22.05% | E8a | p.10 |
| average error | 0.32 | % | MCNC library; node UNKNOWN; 2015 | C8: 1.38% | E8a | p.10 |
| area | 407.3 | - | MCNC library; node UNKNOWN; 2015 | C8: 427.4 | E8a | p.10 |
| delay | 87.8 | ns | MCNC library; node UNKNOWN; 2015 | C8: 93.5 ns | E8a | p.10 |
| gates | 1288 | gates | MCNC library; node UNKNOWN; 2015 | C16: 1288 gates | E16a | p.10 |
| worst error | 4.44 | % | MCNC library; node UNKNOWN; 2015 | C16: 22.22% | E16a | p.10 |
| average error | 0.32 | % | MCNC library; node UNKNOWN; 2015 | C16: 1.39% | E16a | p.10 |
| area | 1926.3 | - | MCNC library; node UNKNOWN; 2015 | C16: 2006.5 | E16a | p.10 |
| delay | 178.7 | ns | MCNC library; node UNKNOWN; 2015 | C16: 184.3 ns | E16a | p.10 |
| gates | 30 | gates | MCNC library; node UNKNOWN; 2015 | C4: 47 gates | E4b | p.10 |
| worst error | 7.06 | % | MCNC library; node UNKNOWN; 2015 | C4: 19.61% | E4b | p.10 |
| average error | 1.23 | % | MCNC library; node UNKNOWN; 2015 | C4: 1.23% | E4b | p.10 |
| area | 41.9 | - | MCNC library; node UNKNOWN; 2015 | C4: 71.2 | E4b | p.10 |
| delay | 27.4 | ns | MCNC library; node UNKNOWN; 2015 | C4: 38.9 ns | E4b | p.10 |
| gates | 208 | gates | MCNC library; node UNKNOWN; 2015 | C8: 276 gates | E8b | p.10 |
| worst error | 7.94 | % | MCNC library; node UNKNOWN; 2015 | C8: 22.05% | E8b | p.10 |
| average error | 1.28 | % | MCNC library; node UNKNOWN; 2015 | C8: 1.38% | E8b | p.10 |
| area | 310.2 | - | MCNC library; node UNKNOWN; 2015 | C8: 427.4 | E8b | p.10 |
| delay | 81.4 | ns | MCNC library; node UNKNOWN; 2015 | C8: 93.5 ns | E8b | p.10 |
| generations to equal quality | 15 times fewer | generations | Intel Xeon 3 GHz / 2015 | RS | HS1/HS2 | p.8 |
errors_and_checks: Fitness is `f=Σ|y(j)-t(j)|`; multiplier fitness exhaustively covers `K=2^ni` inputs. Worst and average errors in Table III are normalized to `emax=2^(2w)-1`; no fault-detection mechanism is provided. # p.5, p.9–10
conditions: HS1/HS2 outperform RS and both tested MOEAs most clearly when 60–90% of the 4-bit multiplier gates remain. Randomly seeded CGP does not scale satisfactorily to the 25-median. Technology-dependent gate downsizing is excluded, and execution time remains the main disadvantage. # p.8, p.10–12
evidence: §III-B–F, Eq. 1, Figs. 2–9 and 14, Tables II–III, pp.4–12

### error_analysis_quality  (role: instantiates)
mechanism: Arithmetic-circuit candidates are evaluated by exhaustive absolute-error accumulation. Median-circuit candidates are evaluated with randomly generated training/test vectors because their complete input spaces contain `256^9` or `256^25` vectors. # p.5, p.10
choices:
  metric: med   # p.3, p.5, p.9
  model: exhaustive_sim (multipliers); monte_carlo (median) [outside domain]   # p.5, p.10–11
new_choices:
  normalization_reference: maximum_output_value — Table III divides worst and average error by `2^(2w)-1`   # p.9
slots:
  none
parameters: `10^4` training vectors for 9-median; `10^5` for 25-median; `10^6` vectors for final median error/power evaluation. # p.10–11
results:
| metric | value | unit | technology / device | baseline | condition | page |
| relative error deviation | 0.98 | % | Intel Xeon 3 GHz / 2015 | repeated random samples | 9-median, `10^4` test vectors | p.10 |
| relative error deviation | 0.30 | % | Intel Xeon 3 GHz / 2015 | repeated random samples | 25-median, `10^5` test vectors | p.10 |
| relative error deviation | 0.01 | % | Intel Xeon 3 GHz / 2015 | repeated random samples | either median, `10^7` test vectors | p.10 |
errors_and_checks: Error is absolute output deviation from the exact circuit; no accuracy bound, false-alarm model, or fault coverage is specified. # p.5, p.10
conditions: Exhaustive evaluation is used only where every input combination is tractable. Sampled median fitness depends on the number of random vectors. # p.5, p.10
evidence: §III-D, §IV-B, Eq. 1, Table IV, pp.5,10–11

## new_families
### approximate_median_network  (domain: approx: approximation methods, closest: approximate_logic_synthesis, why_not: the vocabulary contains synthesis methods but no median-operator microarchitecture)
mechanism: An exact bitonic sorting network supplies a seed composed of 8-bit `MIN`/`MAX` components. Functional-level CGP removes or rewires components under a fixed resource budget and minimizes sampled absolute median error. The evaluated operators select the median of 9 or 25 unsigned 8-bit inputs. # p.6, p.10–11
choices: input_count: {9, 25}; seed_network: {bitonic_sorter}; component_set: {BUF_MIN_MAX}; seeding: {RS, HS1, HS2}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| power | 10.8 | mW | MCNC library; node UNKNOWN; 2015 | none | best exact 9-median | p.11 |
| area | 2314.2 | - | MCNC library; node UNKNOWN; 2015 | one NAND gate | best exact 9-median | p.11 |
| delay | 285.9 | ns | MCNC library; node UNKNOWN; 2015 | none | best exact 9-median | p.11 |
| power | 72.4 | mW | MCNC library; node UNKNOWN; 2015 | none | exact 25-median | p.11 |
| area | 16497.7 | - | MCNC library; node UNKNOWN; 2015 | one NAND gate | exact 25-median | p.11 |
| delay | 539.5 | ns | MCNC library; node UNKNOWN; 2015 | none | exact 25-median | p.11 |
evidence: §IV-B, Figs. 10–13, Tables IV–V, pp.10–12

## space_gaps
* `approximate_logic_synthesis` needs choices for resource-oriented optimization, population seeding, and gate/functional representation levels. # p.3–6
* The multiplier families lack a value for an unconstrained CGP-evolved Boolean netlist whose topology does not retain a named multiplier architecture. # p.4–10

## open_questions
* The MCNC library has no reported technology node. # p.9
* Exact numerical power/error points for approximate median circuits appear only in plots, so the note does not estimate them. # p.11–12
* The paper does not identify named adder/reduction families inside the evolved multiplier netlists. # p.4–10
