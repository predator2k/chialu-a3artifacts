---
handle: wallace1964
citation: Wallace, "A Suggestion for a Fast Multiplier", IEEE Transactions on Electronic Computers, 1964
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary40]
authority: landmark
pages_read: 14-17 / 4
---

## summary
The paper proposes a fully combinational binary multiplier that reduces simultaneously generated partial products through a tree of carry-free three-input pseudoadders. A local radix-4 recoding halves the partial-product count, and the same multiplier supports quadratically convergent reciprocal/division and reciprocal-root iterations. The evaluated 40-bit diode-transistor design multiplies in 750 nsec and divides in about 3 μsec.

## families
### booth_recoded_parallel  (role: proposes)
mechanism: The multiplier is recoded locally into base-four digits from {+2,+1,0,-1,-2}. Each recoded digit depends on three adjacent binary multiplier digits, so all summands can be generated simultaneously. Required multiplicand multiples use only shifting and complementing. Negative digits in two's-complement arithmetic introduce correction digits, after which a pseudo-adder tree reduces the summands to two numbers for a final carry-propagating addition.
choices:
  booth_radix: 4   # p.15
  hard_multiple_gen: none   # p.15
  negative_pp_encoding: ones_complement_plus_neg_bit   # p.15
new_choices:
  local_recoding_window: 3 binary digits — number of adjacent original multiplier digits determining each recoded digit   # p.15
slots:
  reduction: csa_reduction_tree   # pp.14-15
parameters: 40-bit operands; 20 simultaneously generated summands; recoded digit set {+2,+1,0,-1,-2}; one final carry-propagating adder   # pp.15-16
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplication time | 750 | nsec | saturating complementary diode-transistor AND-OR-NOT circuits; 1964 | UNKNOWN | 40-bit complete multiplier; assumed 30 nsec logic-stage delay, 100 nsec drivers, 100 nsec final adder and 100 nsec result-register settling | p.16 |
| total semiconductor count | 4591 | transistors | saturating complementary diode-transistor AND-OR-NOT circuits; 1964 | conventional arithmetic unit | excludes final carry-propagating adder and operand/result registers | p.17 |
| total semiconductor count | 33,083 | diodes | saturating complementary diode-transistor AND-OR-NOT circuits; 1964 | conventional arithmetic unit | excludes final carry-propagating adder and operand/result registers | p.17 |
| unit cost | about 10 | per cent of computer cost | saturating complementary diode-transistor circuits; 1964 | modern large-scale computer | multiplication-division unit | p.17 |
| speed improvement | at least four | factor | saturating complementary diode-transistor circuits; 1964 | conventional units | multiplication/division speeds | p.17 |
errors_and_checks: none
conditions: Recoding beyond radix 4 appears to require multiples not obtainable by shifting (p.15). Hardware grows as the square of word length, while multiplication time grows logarithmically (p.17).
evidence: Addition and Generation of Summands; Fig. 1; Speed and Cost; Discussion, pp.14-17.

### newton_raphson  (role: instantiates)
mechanism: For division, simple logic derives an initial reciprocal approximation p from the first six digits of normalized x, with |1-px| < 1/32. The recurrence updates a and b by multiplication with 2-a and converges quadratically toward 1 and 1/x. Iteration-specific approximate multipliers reduce the recoded summands to 4, 7 and 12 while preserving the correct answer. Shorter early operands allow two multiplications to share separate sections of the tree.
choices:
  iterations: 3   # p.16
  dedicated_multiplier: false   # pp.15-16
new_choices:
  iteration_specific_multiplier_precision: {4_summands, 7_summands, 12_summands} — successive approximate multipliers omit unnecessary digits while preserving the final answer   # p.16
  concurrent_split_tree_multiplication: true — the first two iterations perform both multiplications simultaneously in shorter tree sections   # p.16
slots:
  iter_mult: booth_recoded_parallel [booth_radix=4]   # pp.15-16
parameters: 6 inspected input digits; initial error below 1/32; 3 iterative steps; 40-bit reciprocal; 4 multiplier passes   # pp.15-16
results:
| metric | value | unit | technology / device | baseline | condition | page |
| reciprocal-generating time | 2220 | nsec | saturating complementary diode-transistor AND-OR-NOT circuits; 1964 | UNKNOWN | excludes prenormalization; 40-bit design | p.16 |
| complete division time | about 3 | μsec | saturating complementary diode-transistor AND-OR-NOT circuits; 1964 | UNKNOWN | reciprocal followed by multiplication | p.16 |
| reciprocal-root time | 6 | μsec | saturating complementary diode-transistor AND-OR-NOT circuits; 1964 | customary Newton method using repeated divisions | assumes no simultaneous multiplications | p.16 |
errors_and_checks: The iteration-specific approximate multipliers produce the correct answer, but the paper gives no final rounding or numerical-error bound (p.16).
conditions: Only three iterative steps are required for a 40-bit reciprocal (p.16). At least the first three of four multiplier passes are faster than a full multiplication (p.16). A half-sized two-step tree does not increase reciprocal time because it remains large enough for the iteration multiplications (p.17).
evidence: Division; Square Root; Speed and Cost; Discussion, pp.15-17.

## new_families
### csa_reduction_tree  (domain: mul: integer multipliers, closest: carry_save_array, why_not: the paper uses a logarithmic-depth tree of separately instantiated 3-to-2 stages rather than a regular two-dimensional array)
mechanism: Each pseudo-adder accepts three summands and emits two numbers with the same total, without carry propagation between bit positions. Every level groups the available summands into threes, so the summand count falls by approximately a factor of 1.5 per level. Separate pseudoadders implement every level without intermediate storage, producing a purely combinational tree. A final carry-propagating adder assimilates the last two numbers.
choices: reduction_cell: {full_adder_3_to_2}; level_implementation: {fully_combinational, time_reused}; final_assimilation: {carry_propagating_adder}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| pseudo-adder stage delay | about 60 | nsec | transistor-diode circuitry; 1964 | conventional carry-propagating adder | three-transistor pseudo-adder stage | p.15 |
| reused-stage pass interval | about 150 | nsec | transistor-diode circuitry; 1964 | fully combinational tree | includes gating-signal distribution and flip-flop recovery limits | p.15 |
| tree size | 750 | full-adder circuits | saturating complementary diode-transistor AND-OR-NOT circuits; 1964 | UNKNOWN | 40-bit multiplication-division unit | p.16 |
| alternative equipment cost | almost halved | relative | saturating complementary diode-transistor circuits; 1964 | full combinational tree | half as many adders; multiplication performed in two steps | p.17 |
| alternative multiplication time | almost doubled | relative | saturating complementary diode-transistor circuits; 1964 | full combinational tree | half as many adders; multiplication performed in two steps | p.17 |
evidence: Addition and Fig. 1, pp.14-15; Speed and Cost, p.16; Discussion, p.17.

## space_gaps
* `csa_reduction_tree` appears as a slot value in the vocabulary but lacks a declared family; the paper establishes its 3-to-2 cell, logarithmic-level reduction and combinational/time-reused implementation choice (pp.14-15).
* `newton_raphson` lacks choices for iteration-specific approximate multipliers and simultaneous use of split reduction-tree sections (p.16).

## open_questions
* The paper does not specify the topology of the final carry-propagating adder beyond citing approximately 100 nsec contemporary designs (pp.15-16).
* The paper does not state the final rounding rule or retained guard-bit count for reciprocal/division results (pp.15-16).
* The reciprocal-root recurrence is described as a variant of the reciprocal iteration and contrasted with the customary Newton method, so its exact mapping to the vocabulary's SFU `newton_raphson` family remains ambiguous (p.16).
