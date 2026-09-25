---
handle: stelling1998
citation: P. F. Stelling, C. U. Martel, V. G. Oklobdzija, R. Ravi, "Optimal Circuits for Parallel Multipliers", IEEE Transactions on Computers, vol. 47, no. 3, 1998
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary_integer]
authority: incremental
pages_read: 273-285 / 13
---

## summary
The paper characterizes delay-optimal partial-product reduction trees built from full adders and one parity-correcting half adder per applicable column. Its search programs find optimal Mini-max delays and undominated column-delay profiles under a normalized full-adder delay model, with exact Mini-max results through 59-bit multiplication.

## families
none

## new_families
### globally_optimized_full_adder_pprt  (domain: mul: integer multipliers, closest: carry_save_array, why_not: `carry_save_array` specifies a regular 2-D CSA array, while TDM globally optimizes distinct column circuits and their intercolumn carry vectors.)
mechanism: TDM reduces each partial-product column to two sum bits using the minimum number of full adders and, for an odd input count, one half adder on the earliest two inputs. Each column circuit receives the preceding column’s carry vector. Regular two-greedy circuits suffice to represent every undominated result under the standard delay model. Mini-max search minimizes the latest PPRT sum output, while Profile search retains undominated vectors of per-column sum delays and outgoing carries.   # p.275-282
choices:
  reduction_cell: {full_adder_3_2}   # p.273-276
  odd_column_parity: {half_adder_on_earliest_inputs}   # p.275-276
  construction_strategy: {three_greedy, two_greedy_regular_search}   # p.277-279
  optimization_objective: {mini_max_delay, undominated_delay_profile}   # p.280-282
  delay_model: {technology_parameterized, standard_normalized_xor}   # p.274, p.280
  profile_selection: {latest_earliest, super_optimal_reference}   # p.282-283
slots:
  none
parameters: n-by-n and asymmetric binary multiplication; n² partial products; 2n-1 columns; full-adder sum s = max(b + 2, d + 1) and carry c = d + 1 in the standard model; half-adder sum delay 1 and carry delay 0.5; exact Mini-max search through 57 bits and optimal tabulated results through 59 bits; all-undominated-profile search through 30 bits, with profile-pruned derived designs through 48 bits   # p.274-276, p.282-284
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum PPRT delay | 5 | Normalized XOR Delays | UNKNOWN / 1998 | 5, three-greedy | 7-8-bit multiplication | p.282 |
| maximum PPRT delay | 6 | Normalized XOR Delays | UNKNOWN / 1998 | 6, three-greedy | 9-10-bit multiplication | p.282 |
| maximum PPRT delay | 7 | Normalized XOR Delays | UNKNOWN / 1998 | 7, three-greedy | 11-12-bit multiplication | p.282 |
| maximum PPRT delay | 7 | Normalized XOR Delays | UNKNOWN / 1998 | 7.5, three-greedy | 13-bit multiplication | p.282 |
| maximum PPRT delay | 8 | Normalized XOR Delays | UNKNOWN / 1998 | 8, three-greedy | 14-16-bit multiplication | p.282 |
| maximum PPRT delay | 8 | Normalized XOR Delays | UNKNOWN / 1998 | 9, three-greedy | 17-bit multiplication | p.282 |
| maximum PPRT delay | 9 | Normalized XOR Delays | UNKNOWN / 1998 | 9, three-greedy | 18-20-bit multiplication | p.282 |
| maximum PPRT delay | 9 | Normalized XOR Delays | UNKNOWN / 1998 | 9.5, three-greedy | 21-bit multiplication | p.282 |
| maximum PPRT delay | 9 | Normalized XOR Delays | UNKNOWN / 1998 | 10, three-greedy | 22-bit multiplication | p.282 |
| maximum PPRT delay | 10 | Normalized XOR Delays | UNKNOWN / 1998 | 10, three-greedy | 23-26-bit multiplication | p.282 |
| maximum PPRT delay | 10 | Normalized XOR Delays | UNKNOWN / 1998 | 11, three-greedy | 27-28-bit multiplication | p.282 |
| maximum PPRT delay | 11 | Normalized XOR Delays | UNKNOWN / 1998 | 11, three-greedy | 29-35-bit multiplication | p.282 |
| maximum PPRT delay | 11 | Normalized XOR Delays | UNKNOWN / 1998 | 12, three-greedy | 36-bit multiplication | p.282 |
| maximum PPRT delay | 12 | Normalized XOR Delays | UNKNOWN / 1998 | 12, three-greedy | 37-44-bit multiplication | p.282 |
| maximum PPRT delay | 12 | Normalized XOR Delays | UNKNOWN / 1998 | 13, three-greedy | 45-47-bit multiplication | p.282 |
| maximum PPRT delay | 13 | Normalized XOR Delays | UNKNOWN / 1998 | 13, three-greedy | 48-57-bit multiplication | p.282 |
| maximum PPRT delay | 13 | Normalized XOR Delays | UNKNOWN / 1998 | 13.5, three-greedy | 58-bit multiplication | p.282 |
| maximum PPRT delay | 13 | Normalized XOR Delays | UNKNOWN / 1998 | 14, three-greedy | 59-bit multiplication | p.282 |
| columns at maximum delay | 4 | columns | UNKNOWN / 1998 | 8 columns, three-greedy | 24-by-24 multiplier; maximum delay 10 | p.283 |
| maximum PPRT delay | 12 | Normalized XOR Delays | UNKNOWN / 1998 | 13, three-greedy | 45-bit derived profile; heuristic result | p.283 |
errors_and_checks: The reduction computes exact binary products; no arithmetic-error rate, fault model, detection coverage, false-alarm behavior, or alias rate is reported.   # p.273-275
conditions: All partial-product bits are assumed available at time 0. The standard model assumes XOR delay 1, NAND delay about 0.5, x2 = 2, x3 = 1, and y3 = 1. Regular-circuit optimality requires x2 ≤ 2x3. Three-greedy is within one equivalent XOR delay of optimal in the reported Mini-max cases, but its delay profile is strictly dominated for every problem size at least 6. Derived latest-earliest profiles above size 30 are believed rather than proved optimal.   # p.274-275, p.279, p.282-284
evidence: §2 definition and delay model; §3 Lemmas 3.1-3.7 and Corollary 3.8; §4 canonical-circuit bounds and Theorem 4.6; §5 relaxed-problem lower bound; §6 search procedures; Table 2; Figs. 6-8; §7 conclusions.

## space_gaps
* The multiplier vocabulary lacks a defined PPRT reduction family for globally optimized 3:2 full-adder trees, even though `csa_reduction_tree` appears as a slot value elsewhere.   # p.273-275
* A reduction-family choice is needed for nonuniform per-column arrival-profile optimization, because the paper treats the complete delay profile rather than only tree depth or maximum delay.   # p.275, p.281-283
* A final-CPA slot should admit an arrival-profile-optimized hybrid of Ripple-Carry/Carry-Skip/Carry-Select/Conditional Sum blocks.   # p.284

## open_questions
* The optimal final carry-propagate adder for a given PPRT delay profile is not fully characterized.   # p.282
* The derived latest-earliest solutions above size 30 are not proved optimal.   # p.283
* The effect of applying the parity-correcting half adder to later inputs is left open.   # p.276
* The reported exact limits differ between Mini-max delay search, complete Profile search, and profile-pruned heuristic search, so the merge pass must preserve those scopes separately.   # p.282-284
