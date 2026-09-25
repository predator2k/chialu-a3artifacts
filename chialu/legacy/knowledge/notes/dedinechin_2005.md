---
handle: dedinechin_2005
citation: de Dinechin, Tisserand, "Multipartite Table Methods", IEEE Transactions on Computers, 2005
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fixed_point]
authority: landmark
pages_read: 319-330 / 12
---

## summary
The paper unifies STAM and Muller-style multipartite tables into a searchable table-lookup-and-addition architecture for fixed-point elementary functions. The method computes exact approximation-error bounds, selects guard bits for faithful rounding, and generates synthesizable VHDL for Virtex FPGAs. The reported design space offers the best area/speed tradeoff for precisions from 8 to 16 bits. # p.319, p.323-326, p.330

## families
### multipartite  (role: proposes)
mechanism: The input word is split into an MSB subword A, which addresses a Table of Initial Values, and an LSB subword B, which is partitioned into m subwords Bi. Each Bi and a possibly different-width subword Ci of A address a symmetric Table of Offsets TOi. An adder tree sums the TIV and TOi outputs. Enumeration selects the decomposition D, per-table slope precision, and guard-bit count that minimize stored bits while satisfying faithful rounding. # p.323-326
choices:
  tables: 2, 3, 4, or 5   # p.323, p.327-328
  accuracy_target: faithful_1ulp   # p.323-324
new_choices:
  input_decomposition: D = {α, β, m, (γi, pi, βi)i=0...m-1} — controls the TIV/TO address partitions and slope precision   # p.323
  table_guard_bits: g — extra output bits selected from the approximation and rounding-error budget   # p.324-325
  slope_selection: minimax_border_average — equalizes the four endpoint errors for each constant-slope interval   # p.324-325
  output_representation: carry_propagated_or_redundant — the final carry-propagate stage may be omitted when a multiplier consumes the result   # p.323
slots:
  none
parameters: fixed-point inputs/outputs; demonstrated at 16-bit and 24-bit precision; m ≥ 1 offset tables plus one TIV; g guard bits; generated VHDL; faithful result is one of the two fixed-point values closest to f(x)   # p.319, p.323-328
results:
| metric | value | unit | technology / device | baseline | condition | page |
| table-storage reduction | up to 50 | percent | technology-independent / 2005 | best Schulte-Stine results | best 16-bit and selected 24-bit decompositions | p.326-327 |
| useful precision range | 8 to 16 | bits | Virtex FPGA study / 2005 | multiplier-based methods | area/speed tradeoff | p.330 |
| practical precision limit | 24 | bits | Xilinx Virtex-II XC2V1000-fg456-5 / 2005 | none | FPGA capacity | p.328 |
| economical precision limit | less than 20 | bits | Xilinx Virtex-II XC2V1000-fg456-5 / 2005 | none | inferred from synthesized sine operators | p.328 |
| approximation-bound agreement | 10^-7 | absolute numerical agreement | software exhaustive check / 2005 | predicted approximation bound | tested generated tables | p.326 |
errors_and_checks: The required contract is faithful rounding, defined as total error below one ulp so the result is one of the two closest fixed-point values. Exhaustive checks measure the actual approximation and final errors. Interval-boundary nonmonotonicities may occur, although faithful rounding bounds them by one ulp. # p.323-326, p.329
conditions: The method assumes a monotonic function with monotonic derivative after range reduction. # p.324 The method excludes input-discretization error from its analysis. # p.320, p.324 Increasing m reduces table storage but adds adder inputs/XOR/sign-extension hardware, so gains diminish and may reverse. # p.321, p.328 Infinite derivatives, including sqrt(x) at zero, require interval splitting or another method. # p.329 Multipartite designs are preferred below about 15-bit precision, while multiplier-based designs become preferable above about 20 bits. # p.329
evidence: Sections 4.1-4.7, equations (2)-(24), Figures 6-9, Tables 2-8, Sections 5.1-5.6, p.323-330

### bipartite  (role: analyzes)
mechanism: The method divides the function into 2^α affine segments. Subword A addresses a TIV containing one initial value per segment, while the concatenation CB addresses a TO containing an offset derived from a slope shared across a larger interval. The symmetric variant stores midpoint values and only half of each offset segment, reconstructing the other half with XOR logic. # p.320-321
choices:
  symmetric: false or true   # p.320-321
new_choices:
  none
slots:
  none
parameters: input decomposition wI = α + γ; TIV addressed by α bits; TO addressed by β + γ bits; storage is 2^α + 2^(β+γ) values instead of 2^wI values   # p.320
results:
| metric | value | unit | technology / device | baseline | condition | page |
| direct-table storage | 2^α + 2^(β+γ) | values | technology-independent / 2005 | 2^wI-value direct LUT | piecewise-affine approximation | p.320 |
| symmetric TO reduction | one half | TO storage | technology-independent / 2005 | nonsymmetric bipartite TO | midpoint storage and symmetric offsets | p.320-321 |
errors_and_checks: Previous Taylor analyses provide upper bounds rather than the exact approximation error developed by this paper. # p.320
conditions: The method targets low-accuracy fixed-point elementary functions. # p.319 Its error depends on the evaluated function. # p.320
evidence: Sections 3.1-3.2 and Figures 1-3, p.320-321

### stam  (role: extends)
mechanism: STAM decomposes the bipartite offset word B into m subwords and distributes the linear offset into m symmetric TOi tables. The architecture replaces one large offset table with smaller tables and m-1 additional additions. All TOi tables use the same slope-address subword C, which the proposed multipartite generalization relaxes. # p.321, p.323
choices:
  tables: m + 1 [outside domain]   # p.321, p.323
new_choices:
  slope_addressing: shared_C — every TOi uses the same slope-address subword   # p.321, p.323
slots:
  none
parameters: m TOi tables plus one TIV; m-1 additional additions; each TOi has a separate rounding error   # p.321
results:
| metric | value | unit | technology / device | baseline | condition | page |
| added arithmetic | m-1 | additions | technology-independent / 2005 | bipartite method | B decomposed into m subwords | p.321 |
errors_and_checks: Additional table-rounding errors require greater output precision in the smaller TOi tables. # p.321
conditions: Smaller tables trade against additional adders and accumulated discretization errors. # p.321 Shared slope precision wastes accuracy in lower-weight TOi tables, which motivates the generalized multipartite decomposition. # p.321
evidence: Section 3.3 and Section 4.1, p.321, p.323

## new_families
### addition_table_addition  (domain: sfu, closest: multipartite, why_not: additions occur both before and after lookup, so the mechanism is not a multipartite decomposition into parallel offset tables)
mechanism: A first-order ATA evaluator splits X into A and B, computes A+B, looks up f(A) and f(A+B), subtracts the lookup results, shifts the difference, and adds it to f(A). A second-order form looks up f(A), f(A+B), and f(A-B) and applies centered-difference formulas. Table ports or sequential accesses expose area/throughput tradeoffs. # p.321-322
choices: order: {1, 2}; table_access: {parallel_tables, dual_port, sequential_pipelined}; offset_partitioning: {none, split_subwords}; symmetry: Bool
results:
| metric | value | unit | technology / device | baseline | condition | page |
| first-order lookup count | 2 | lookups | technology-independent / 2005 | none | ATA first-order evaluation | p.321-322 |
| second-order arithmetic | 3 lookups and 7 additions | operations | technology-independent / 2005 | first-order ATA | centered-difference form | p.322 |
| Wong-Goto storage | 868,352 | bits | UNKNOWN / 2005 | proposed multipartite results | 24-bit precision, six tables and nine additions | p.328 |
| sequential Wong-Goto storage | about 16K | bits | UNKNOWN / 2005 | six-table parallel ATA | one reused table | p.328 |
| sequential Wong-Goto slowdown | 5 | times | UNKNOWN / 2005 | six-table parallel ATA | sequential table access | p.328 |
evidence: Sections 3.4 and 5.5, Figures 4-5, p.321-322, p.328

## space_gaps
* The sfu `multipartite` family lacks choices for the input decomposition D, guard-bit count g, and per-TO slope-address width γi. # p.323-325
* The sfu `multipartite` family lacks an adder-tree/output-form slot covering carry-propagated and redundant outputs. # p.323
* The sfu `multipartite` family lacks a monotonicity-enforcement choice for right-edge slopes and increased table precision. # p.329
* The `stam.tables` domain does not express the paper's symbolic m TOi tables plus one TIV. # p.321

## open_questions
* The vocabulary does not specify whether `multipartite.tables` counts only TOi tables or the TIV plus all TOi tables.
* The paper excludes input quantization from the error model, so faithful rounding does not settle behavior under alternative input mappings. # p.320, p.324
* The paper leaves systematic monotonicity optimization and its hardware cost for future work. # p.329
