---
handle: doran1988
citation: R. W. Doran, "Variants of an Improved Carry Look-Ahead Adder", IEEE Transactions on Computers, vol. 37, no. 9, pp. 1110-1113, 1988.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary]
authority: incremental
pages_read: 1110-1113 / 4
---

## summary
Doran reformulates Ling’s adder as the propagation of a composite term instead of the conventional carry, then derives 32 carry-lookahead variants that permit local sum recovery (pp.1110-1112). Four variants share Ling’s desirable recurrence properties (p.1113).

## families
### ling_prefix  (role: analyzes)
mechanism: Ling propagates \(H_i=G_i+G_{i+1}\), which is true when either a carry out or a carry in occurs at bit \(i\). The recurrence is \(H_i=g_i+t_{i+1}H_{i+1}\), where \(g_i=a_ib_i\) and \(t_i=a_i+b_i\). Local expressions recover the conventional carry and sum from the propagated composite term (pp.1110-1111).
choices:
  pseudo_carry_group: 2   # p.1110
  order: 1   # p.1110
new_choices:
  propagated_composite: H_i=G_i+G_{i+1} — identifies the logical function propagated instead of G_i   # p.1110
slots:
  none
parameters: binary operands of unspecified width; four recurrence levels are expanded for comparison   # p.1111
results:
| metric | value | unit | technology / device | baseline | condition | page |
| recurrence-expansion gate count | 3 | gates | UNKNOWN / 1988 | conventional G_0 expansion: 4 gates | four-level H_0 expansion | p.1111 |
| recurrence-expansion gate inputs | 7 | inputs | UNKNOWN / 1988 | conventional G_0 expansion: 10 inputs | four-level H_0 expansion | p.1111 |
| maximum recurrence gate width | 3 | inputs | UNKNOWN / 1988 | conventional G_0 expansion: 4 inputs | four-level H_0 expansion | p.1111 |
errors_and_checks: none
conditions: Ling’s simpler carry propagation is offset partly by more complex sum generation, and its advantage depends on how well the equations fit the available circuit elements (p.1111).
evidence: Section II, Section III, equations (3)-(6), and the four-level expansions on pp.1110-1111.

### carry_lookahead  (role: compares)
mechanism: The conventional adder forms \(p_i=a_i\oplus b_i\) and \(g_i=a_ib_i\), propagates \(G_i=g_i+p_iG_{i+1}\) with a ripple or tree circuit, and forms \(S_i=p_i\oplus G_{i+1}\) locally (p.1110).
choices:
  none
new_choices:
  none
slots:
  none
parameters: binary operands of unspecified width; four recurrence levels are expanded for comparison   # pp.1110-1111
results:
| metric | value | unit | technology / device | baseline | condition | page |
| recurrence-expansion gate count | 4 | gates | UNKNOWN / 1988 | Ling H_0 expansion: 3 gates | four-level G_0 expansion | p.1111 |
| recurrence-expansion gate inputs | 10 | inputs | UNKNOWN / 1988 | Ling H_0 expansion: 7 inputs | four-level G_0 expansion | p.1111 |
| maximum recurrence gate width | 4 | inputs | UNKNOWN / 1988 | Ling H_0 expansion: 3 inputs | four-level G_0 expansion | p.1111 |
errors_and_checks: none
conditions: The paper treats ripple and tree propagation as alternatives but does not specify a topology, group size, circuit technology, or complete implementation (p.1110).
evidence: Section II and Section III on pp.1110-1111.

## new_families
### composite_function_lookahead  (domain: adder, closest: ling_prefix, why_not: The propagated function may be any locally sum-recoverable symmetric function rather than Ling’s fixed pseudo-carry H_i.)
mechanism: The construction replaces \(G_i\) with a normalized logical function \(X_i\) of \(a_i\), \(b_i\), and \(G_{i+1}\). Symmetry in \(a_i\) and \(b_i\) bounds the search to 64 functions. Thirty-two functions retain enough information to derive \(G_i\), and therefore \(S_i\), locally. Four variants also have Ling’s three properties: only one polarity of the next composite term occurs, its coefficient uses only bit \(i+1\) terms, and the relation between \(G_i\) and \(X_i\) is simple (pp.1111-1113).
choices:
  propagated_function: symmetric Boolean function of a_i, b_i, and G_{i+1}   # p.1111
  recurrence_subset: {all_32_locally_recoverable, four_ling_type}   # pp.1112-1113
  direct_output_polarity: {sum, inverse_sum}   # p.1113
results:
| metric | value | unit | technology / device | baseline | condition | page |
| locally sum-recoverable variants | 32 | adders | UNKNOWN / 1988 | 64 candidate symmetric functions | normalized-function enumeration | pp.1111-1112 |
| variants with Ling’s three recurrence properties | 4 | adders | UNKNOWN / 1988 | 32 locally sum-recoverable variants | Table I subset | p.1113 |
evidence: Section IV on pp.1111-1112 and Section V/Table I on pp.1112-1113.

## space_gaps
* `composite_function_lookahead` needs a `function_variant` choice that enumerates the four Table I recurrence equations (p.1113).
* `direct_output_polarity` is needed because two of the four Ling-type variants obtain the inverse of the sum more directly than the sum (p.1113).

## open_questions
* The paper does not report delay, area, or gate counts for the four generalized Ling-type variants, so their relative implementation cost remains UNKNOWN (p.1113).
* The paper does not specify a prefix topology, technology, device, or operand width for any implementation (pp.1110-1113).
