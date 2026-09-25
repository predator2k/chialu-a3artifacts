---
handle: danysh1998
citation: A. N. Danysh, E. E. Swartzlander, "A Recursive Fast Multiplier", 32nd Asilomar Conference on Signals, Systems and Computers, 1998
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [unsigned_binary]
authority: incremental
pages_read: 197-201 / 5
---

## summary
The paper proposes an exact unsigned multiplier that recursively forms four half-width products and reduces their shifted carry-save outputs. The architecture provides O(log n) delay with regular/hierarchical layout, but its reported gate complexity is O(log n * n²). # p.197-201

## families
### carry_save_datapath  (role: instantiates)
mechanism: Each recursive sub-multiplier returns a carry-save pair `(C,S)`. A three-stage full-adder network reduces the four shifted subproducts to two summands at every recursion level, and carry propagation is deferred until the final `2n`-bit addition. # p.198-200
choices:
  compressor: 3_2   # p.199
  assimilation_point: end_of_chain   # p.198-200
new_choices:
  none
slots:
  assimilator: UNKNOWN   # p.200
parameters: three full-adder reduction stages per recursion level; final `2n`-bit carry-propagating conversion; 4-bit Dadda base case in the implemented architecture   # p.198-200
results:
| metric | value | unit | technology / device | baseline | condition | page |
| avoided carry-propagation delay | `3log2(n+1)` | gate delay | UNKNOWN / 1998 | carry-propagating addition of three numbers | carry-save reduction of recursive partial results | p.199 |
errors_and_checks: Exact unsigned multiplication was checked by a C model using randomly generated 16-bit operands; the number of tests and coverage are not reported.   # p.200
conditions: Carry-save output is required from each sub-multiplier. Signed 2's-complement recursion requires cumbersome correction additions, so the evaluated design assumes unsigned operands.   # p.198
evidence: Equation (1), Figures 1-3, “Implementation,” “Algorithm Validation,” and “Results,” p.197-200.

## new_families
### recursive_four_quadrant_multiplier  (domain: mul: integer multipliers, closest: recursive_karatsuba, why_not: The mechanism computes four half-width products rather than the three products that define `recursive_karatsuba`.)
mechanism: Each operand is split into upper/lower halves. Four half-width products are computed in parallel, shifted into their output positions, and reduced in carry-save form through three full-adder stages per recursion level. The decomposition repeats to a selected base multiplier. The built design uses a 4-bit Dadda base and performs one final carry-propagating addition. The resulting hierarchy is regular, modular, scalable, and suitable for exposing packed byte/word products before the full product completes. # p.197-201
choices:
  subproducts_per_level: {4}   # p.197-198
  base_case_multiplier: {4_bit_dadda, larger_dadda, booth, other_reused_design}   # p.198, p.201
  intermediate_representation: {carry_save}   # p.198-200
  signed_handling: {unsigned_only, input_output_twos_complement}   # p.198
  reduction_network_organization: {per_level, shared_iterative_proposed}   # p.199, p.201
parameters: n-bit operands split into n/2-bit halves; 4-bit Dadda base case; 8-bit one-level example; 16-bit randomized validation; `log2 n` addition steps; three reduction stages per recursive level   # p.197-200
results:
| metric | value | unit | technology / device | baseline | condition | page |
| gate complexity | 96 | gates | UNKNOWN / 1998 | 4-bit array: 100 gates; 4-bit Dadda: 64 gates | 4-bit recursive multiplier with 2-bit base case, final carry-propagating addition deferred | p.198 |
| delay | 6 | gate delays | UNKNOWN / 1998 | 4-bit Dadda: 7 gate delays | 4-bit recursive multiplier with 2-bit base case, final carry-propagating addition deferred | p.198 |
| delay complexity | `O(log n)` | asymptotic order | UNKNOWN / 1998 | array multiplier: `O(n)` | n-bit recursive multiplier | p.197, p.200 |
| gate complexity | `O(log n * n²)` | asymptotic order | UNKNOWN / 1998 | array multiplier: `O(n²)` | final `2n`-bit carry-propagating adder excluded | p.200 |
errors_and_checks: The algorithm is exact for unsigned operands. A C model checks randomly generated 16-bit products against the expected result, but the paper reports no test count. # p.200
conditions: The recursive multiplier is reported as slightly slower than Dadda and much faster than an array multiplier. The design trades an order-log increase in gate complexity for an order-log reduction in delay. Signed 2's-complement operands require extra corrections or external complementation. # p.198, p.200-201
evidence: Equation (1), Figures 1-5, “Recursive Fast Multiplication Algorithm,” “Implementation,” “Algorithm Validation,” “Results,” and “Conclusion,” p.197-201.

## space_gaps
* The integer-multiplier vocabulary lacks a family for recursive four-quadrant decomposition with four parallel half-width products and carry-save reduction. # p.197-200
* A base-case multiplier choice or slot should admit Dadda/array/Booth implementations because base-case selection controls delay and gate complexity. # p.198, p.201

## open_questions
* The paper does not specify the topology of the final `2n`-bit carry-propagating adder. # p.200
* The paper does not report how many randomized 16-bit cases were tested. # p.200
* The proposed shared reduction-network/recursive-Booth variant is future work rather than an evaluated implementation. # p.201
