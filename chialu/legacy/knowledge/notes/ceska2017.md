---
handle: ceska2017
citation: M. Ceska, J. Matyas, V. Mrazek, L. Sekanina, Z. Vasicek, T. Vojnar, "Approximating Complex Arithmetic Circuits with Formal Error Guarantees: 32-bit Multipliers Accomplished", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), pp. 416-423, 2017
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary_integer_12b, binary_integer_16b, binary_integer_20b, binary_integer_24b, binary_integer_28b, binary_integer_32b, binary_integer_64b, binary_integer_128b]
authority: landmark
pages_read: 416-423 / 8
---

## summary
The document proposes a CGP-based logic-synthesis method that approximates gate-level arithmetic circuits subject to formally verified worst-case absolute error bounds. A resource-limited SAT miter drives evolution toward promptly verifiable candidates and produces Pareto sets for multipliers with operands up to 32 bits and adders with operands up to 128 bits. The document reports the first 32-bit approximate multipliers with formal error guarantees. 

## families
### approximate_logic_synthesis  (role: proposes)
mechanism: A gate-level Cartesian genetic programming search mutates a correct circuit and accepts a smaller candidate only when an ABC `iprove` query proves `WCAE(G,C) ≤ T` within resource limit `L`. Candidates that are not smaller, violate the bound, or exceed `L` receive infinite fitness. The search therefore optimizes relative gate area while favoring sequences of candidates whose approximate-equivalence checks complete promptly. # p.419-420
choices:
  method: cgp_evolution   # p.419-420
  error_constraint: wce   # p.418-420
  formal_verification: sat_miter   # p.418-420
new_choices:
  search_strategy: verifiability_driven — improving candidates must satisfy the error bound within resource limit `L`   # p.419-420
  candidate_representation: gate_level_cgp — chromosomes encode DAGs of arbitrary two-input logic functions   # p.419
  fitness_objective: relative_gate_area — size is minimized subject to `WCAE(G,C) ≤ T`   # p.419-421
  verification_resource_limit: conflicts_per_AIG_node — `L` bounds the verifier work for each candidate   # p.420
slots:
  none
parameters: multiplier operands 12/16/20/24/28/32 bits; adder operands 20/24/28/32/64/128 bits; population 2; 5 mutated integers; 30 runs per target WCAE; 2 hours per run normally, 4 hours for 24-bit multipliers, and 6 hours for larger multipliers; evaluated `L=∞`, `L=160K`, and `L=20K`   # p.421-422
results:
| metric | value | unit | technology / device | baseline | condition | page |
| SAT calls | 22,050 | calls | Intel Xeon X5670 2.4 GHz / 2017 | 856 calls at `L=160K`; 170 calls at `L=∞` | 16-bit multiplier, `WCAE=0.1%`, `L=20K` | p.421 |
| calls terminated by resource limit | 11% | % | Intel Xeon X5670 2.4 GHz / 2017 | 15% at `L=160K` | 16-bit multiplier, `WCAE=0.1%`, `L=20K` | p.421 |
| mean calls terminated by resource limit | 8.84% | % | Intel Xeon X5670 2.4 GHz / 2017 | 6.28% at `L=160K` | average across all target errors, `L=20K` | p.421 |
| calls terminated by resource limit | 36.9% | % | Intel Xeon X5670 2.4 GHz / 2017 | 2.4% for 12-bit multipliers | 32-bit multipliers, `L=20K` | p.422 |
| evolved unique multipliers | over 1190 | circuits | 45 nm / 2017 | accurate multipliers synthesized from Verilog `*` | 12-bit through 32-bit experiments | p.422 |
| non-dominated implementations | 16 to 18 | implementations | 45 nm / 2017 | accurate adder synthesized from Verilog `+` | 24-bit, 28-bit, and 32-bit adders; PDP/WCAE fronts | p.422 |
| non-dominated tradeoffs | 12 | tradeoffs | 45 nm / 2017 | accurate adder synthesized from Verilog `+` | 64-bit and 128-bit adders; restricted target-error levels | p.422 |
errors_and_checks: Every accepted circuit is formally proved to satisfy `WCAE(G,C) ≤ T`; exact WCAE for the 16-bit comparison is found by binary search, while MAE is estimated using `10^9` simulated vectors. # p.418-421
conditions: The method handles functional approximation rather than voltage/frequency overscaling. # p.416 The fitness function optimizes relative gate area, so synthesized area/PDP can occasionally be worse than the accurate circuit when loose resource limits are used. # p.421 Resource limit `L` can discard candidates that are feasible with more verification time or that begin useful improving sequences. # p.420
evidence: Contributions and scope on p.416-417; miter construction on p.418-419; Algorithm/Fig. 4 on p.419-420; experimental setup and Figs. 5-8 on p.421-423.

### error_analysis_quality  (role: extends)
mechanism: `WCAE` and `MAE` normalize absolute arithmetic error by the output range `2^m`. The formal checker computes the two's-complement difference `d=fG(x)-fC(x)` and separately compares positive and negative cases against constant threshold `T`. This construction removes the absolute-value XOR chain and replaces the full comparator with logic specialized to the constant threshold. # p.418-419
choices:
  metric: wce   # p.418
  model: sat_miter [outside domain]   # p.418-420
  composition_across_blocks: false   # p.416-418
new_choices:
  secondary_metric: mae — mean absolute error is simulated after synthesis and compared with WCAE   # p.418, p.421-422
slots:
  none
parameters: miter difference width `m+1`; example `T=5`, `N=6`; measured 64-bit outputs with `T` from `0.0001%` to `0.5%` of `2^64`   # p.419
results:
| metric | value | unit | technology / device | baseline | condition | page |
| miter AIG-node reduction | about 25–35% | % | UNKNOWN / 2017 | absolute-value and full-comparator miter | arithmetic circuits with 64 output bits; `T=0.0001%` to `0.5%` of `2^64` | p.419 |
| MAE relative to WCAE | around 30% | % | 45 nm / 2017 | WCAE | multiplier operand widths 12 through 32 bits | p.422 |
errors_and_checks: The SAT miter emits 1 iff the candidate violates threshold `T`; an UNSAT result proves the worst-case absolute error bound for all inputs. MAE has no formal guarantee because it is obtained from simulation. # p.418-421
conditions: WCAE is selected because excessive worst-case error can be unacceptable even when average error is low. # p.417 `#SAT` error-rate counting is reported as beyond contemporary tools even for 12-bit multipliers. # p.418
evidence: Definitions and prior checking methods on p.418; Fig. 1, Fig. 2, and the proposed miter derivation on p.418-419; WCAE/MAE observations on p.421-422.

## new_families
none

## space_gaps
* `approximate_logic_synthesis` lacks choices for a verifier-aware search strategy, candidate representation, optimization objective, and per-query resource limit. # p.419-420
* `error_analysis_quality.model` lacks formal SAT-miter evaluation, which provides exhaustive worst-case guarantees without exhaustive simulation. # p.418-420

## open_questions
* The document does not state whether the multiplier and adder operands are signed or unsigned.
* The document does not identify the 45 nm technology library.
* Figs. 5-8 plot area/PDP/error Pareto fronts without tabulating the individual circuit coordinates.
* The evolved circuits have arbitrary gate-level structures, so the document does not establish multiplier-reduction or adder-family choices for individual outputs.
