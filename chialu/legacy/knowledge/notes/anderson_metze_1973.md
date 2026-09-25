---
handle: anderson_metze_1973
citation: D. A. Anderson, G. Metze, "Design of Totally Self-Checking Check Circuits for m-Out-of-n Codes", IEEE Transactions on Computers, vol. C-22, no. 3, pp. 263-269, 1973
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [m-out-of-n code]
authority: landmark
pages_read: 263-269 / 7
---

## summary
The paper constructs totally self-checking m-out-of-n code checkers from majority-detection circuits with two-rail outputs. Direct construction requires a k-out-of-2k input divided into equal k-bit groups, while arbitrary m-out-of-n codes require a totally self-checking, code-disjoint translator. The checker is proved self-testing/fault-secure for single faults and unidirectional faults under the stated line stuck-at fault model.

## families
### two_rail_tree  (role: proposes)
mechanism: The checker maps code inputs to (0,1) or (1,0) and noncode inputs to (0,0) or (1,1). Two independent subcircuits compute output functions from majority predicates over equal input groups A and B. The predicates can use two-level or recursively decomposed multilevel AND-OR/OR-AND realizations. Alternating AND-OR and OR-AND level pairs can be merged by increasing gate fan-in. Arbitrary m-out-of-n inputs are first translated through a totally self-checking, code-disjoint translator to a k-out-of-2k code. # p.264-268
choices:
  input_code: m_out_of_n   # p.263-268
new_choices:
  realization_form: {sum_of_products, product_of_sums, merged_alternating_levels} — selects the majority-function gate organization   # p.265-267
  input_partition: {equal_halves} — divides a k-out-of-2k input into two independent k-bit groups   # p.265-266
  translator_front_end: {none, code_disjoint} — permits direct k-out-of-2k checking or translated arbitrary m-out-of-n checking   # p.268
slots:
  none
parameters: 2k inputs arranged as two k-bit groups; 2 outputs; 2^k diagnostic code inputs; 3-out-of-6 worked example; 1-out-of-8 to 3-out-of-6 translator example   # p.266-268
results:
| metric | value | unit | technology / device | baseline | condition | page |
| diagnostic test set | 2^k | code inputs | UNKNOWN | all C(2k,k) code words | majority functions remain explicit in the multilevel or merged realization | p.266-267 |
| diagnostic test set | C(2k,k) | code inputs | UNKNOWN | 2^k code inputs | majority functions are multiplied out into a two-level circuit | p.267 |
| minimum merged-checker depth | 3 | gate levels | UNKNOWN | unmerged alternating-level realization | level merging increases gate input count | p.267 |
| worked input code size | 3-out-of-6 | code | UNKNOWN | UNKNOWN | equal groups A and B contain 3 bits each | p.266-267 |
| translator mapping | 1-out-of-8 to 3-out-of-6 | code mapping | UNKNOWN | UNKNOWN | translator output uses 8 of the 20 possible 3-out-of-6 code words | p.268 |
errors_and_checks: The fault model permits one or more lines stuck at 0 or 1 while gate operations remain unchanged. The prescribed set covers single faults and unidirectional multiple faults. Self-testing requires every prescribed fault to produce a noncode output for at least one code input; fault security forbids an incorrect code output for any code input. The combined properties provide total self-checking without periodic test access. Detection coverage/false-alarm rate/alias rate are not quantified. # p.263-264
conditions: A direct sum-of-products or product-of-sums checker is self-testing for single faults only when n=2m and both input groups contain m bits. # p.265-266 A noninverting AND/OR realization is totally self-checking for single and unidirectional faults because faults cannot create erroneous 1 and 0 outputs simultaneously. # p.266 NAND/NOR realizations do not detect every unidirectional fault using only code inputs, although they detect all single faults, all faults confined to one gate level, and other faults equivalent to unidirectional faults in the AND/OR tree. # p.266 Level merging reduces gates/levels at the cost of increased gate fan-in. # p.267 The complementary-pair test set bi=not(ai) supplies the 2^k diagnostic code words. # p.267 A code-disjoint translator extends the construction to arbitrary m-out-of-n codes. # p.268 The presented 1-out-of-n translator construction works for every n except 3 and 7; totally self-checking 1-out-of-3 and 1-out-of-7 checkers remain unsolved. # p.268
evidence: Definitions and fault model on pp.263-264; construction restrictions on pp.265-266; sum-of-products/product-of-sums/merged implementations and tests on pp.266-267; translator constructions on p.268.

## new_families
none

## space_gaps
* `two_rail_tree` lacks a `realization_form` choice for sum-of-products/product-of-sums/merged alternating-level majority implementations. # p.265-267
* `two_rail_tree` lacks an `input_partition` choice that records the necessary equal-halves partition for direct k-out-of-2k checking. # p.265-266
* `two_rail_tree` lacks a translator slot for totally self-checking, code-disjoint conversion from arbitrary m-out-of-n codes. # p.268

## open_questions
* The paper does not fix a gate/tree arity because majority predicates may use two-level or recursively decomposed multilevel realizations.
* The paper gives a concrete translator for the m=1 case but does not give a comparably direct translator construction for every arbitrary m-out-of-n code.
