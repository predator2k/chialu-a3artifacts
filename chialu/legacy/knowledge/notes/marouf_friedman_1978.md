---
handle: marouf_friedman_1978
citation: M. A. Marouf, A. D. Friedman, "Efficient Design of Self-Checking Checker for any m-Out-of-n Code", IEEE Transactions on Computers, vol. C-27, pp. 482-490, 1978
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [m_out_of_n]
authority: incremental
pages_read: 482-490 / 9
---

## summary
The paper gives procedures for constructing totally self-checking checkers for arbitrary m-out-of-n codes except n = 2m and m = 1. The constructions use positive-unate majority-function networks, code translation, and recursive balanced partitioning to reduce logic/testing complexity by as much as 97 percent against earlier checkers. # p.482, p.484, p.489

## families
none

## new_families
### m_out_of_n_checker  (domain: checker: two-rail / self-checking, closest: two_rail_tree, why_not: the checker uses separately realized majority-function networks and code translators rather than a morphic-cell tree)
mechanism: The input bits are partitioned into balanced sets. Positive-unate majority functions classify valid words into a 1-out-of-Z code, which a totally self-checking translator maps to a 2-out-of-4 code for a final checker. Separate procedures cover (2m + 2) < n < 4m, n = 2m + 1, n > 4m, and m + 2 < n < 2m. The n > 4m construction recursively partitions the inputs. The m > n/2 construction dualizes the checker for the complementary (n-m)-out-of-n code. # p.484-p.489
choices:
  input_code: m_out_of_n — valid words contain exactly m ones among n bits # p.483
  partitioning: {balanced, balanced_recursive, complement_dual} — selects the input decomposition procedure # p.485, p.487-p.489
  majority_realization: {two_level_and_or, multilevel_unate} — realizes the positive majority functions # p.483, p.489
  intermediate_code: {one_out_of_4, one_out_of_5, one_out_of_6, one_out_of_E} — records the code emitted before translation # p.484-p.485, p.487-p.488
  output_translation: one_out_of_Z_to_two_out_of_4 — maps the intermediate outputs to the final checker code # p.484-p.485
  deep_case_delay_style: {recursive, flattened_nine_level} — selects the n > 4m organization # p.488
  gate_polarity: {positive_unate_and_or, inverting_nand_nor} — determines whether multiple unidirectional-fault coverage is retained # p.486, p.489
results:
| metric | value | unit | technology / device | baseline | condition | page |
| logic-complexity saving | 58 | % | UNKNOWN / 1978 | Anderson [8] | m = 3, n = 8; gate count | p.487 |
| logic-complexity saving | 46 | % | UNKNOWN / 1978 | Anderson [8] | m = 3, n = 10; gate count | p.487 |
| logic-complexity saving | 54 | % | UNKNOWN / 1978 | Anderson [8] | m = 3, n = 12; gate count | p.487 |
| logic-complexity saving | 67 | % | UNKNOWN / 1978 | Anderson [8] | m = 4, n = 10; gate count | p.487 |
| logic-complexity saving | 88 | % | UNKNOWN / 1978 | Anderson [8] | m = 5, n = 14; gate count | p.487 |
| logic-complexity saving | 97 | % | UNKNOWN / 1978 | Anderson [8] | m = 6, n = 24; gate count | p.487 |
| gate-input saving | 75 | % | UNKNOWN / 1978 | Anderson [8] | m = 3, n = 8 | p.487 |
| gate-input saving | 80 | % | UNKNOWN / 1978 | Anderson [8] | m = 4, n = 10 | p.487 |
| gate-input saving | 92 | % | UNKNOWN / 1978 | Anderson [8] | m = 5, n = 14 | p.487 |
| gate-input saving | 97 | % | UNKNOWN / 1978 | Anderson [8] | m = 6, n = 24 | p.487 |
| test-set size | 172 | code words | UNKNOWN / 1978 | all 1820 code words | m = 4, n = 16 | p.486 |
| maximum delay | 4 + 3k | gate levels | UNKNOWN / 1978 | UNKNOWN | n > 4m; k = ⌈log2(n/m)⌉ - 1 | p.488 |
| maximum delay | 9 | gate levels | UNKNOWN / 1978 | recursive Procedure 4 | modified n > 4m construction | p.488 |
| logic-complexity saving | 70 to 97 | percent | UNKNOWN / 1978 | previously known realizations | all covered cases except n = 2m and m = 1 | p.482, p.489 |
evidence: Definitions and fault model on p.483; general composition/Theorems 1-2 on p.484; Procedures 2-3 and Theorems 3-5 on p.485-p.487; Procedure 4 and Figs. 7-9 on p.487-p.489; Procedure 5/limitations on p.489.

## space_gaps
* The vocabulary lacks a family for arbitrary m-out-of-n totally self-checking checkers built from positive-unate majority networks and code translators. # p.484-p.489
* The checker vocabulary lacks `m_out_of_n` as an explicit checker input-code value outside the morphic-cell-specific `two_rail_tree` mechanism. # p.483-p.484
* The vocabulary lacks a choice distinguishing single-fault total self-checking from single-and-unidirectional-multiple-fault total self-checking. # p.486, p.489

## open_questions
* The paper does not reproduce the internal constructions of the referenced 1-out-of-Z translators and 2-out-of-4 checker, so their gate structures must not be inferred. # p.484-p.485
* The exact multilevel majority-function realization remains implementation-dependent. # p.489
* No improved realization is established for n = 2m or m = 1. # p.483, p.489
