---
handle: trivedi_1977
citation: Trivedi, Ercegovac, "On-Line Algorithms for Division and Multiplication", IEEE Transactions on Computers, 1977
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: ["radix-2 redundant signed-digit", "radix-10 redundant signed-digit"]
authority: landmark
pages_read: 7 / 7
---

## summary
The paper develops compatible MSDF digit-serial division and multiplication algorithms whose operands and results can overlap across a pipeline. Redundant result digits bound carry propagation and permit binary division with a 4-bit on-line delay, decimal division with a 4-digit delay, and multiplication with a one-digit delay. # pp.681-687

## families
### online_msdf  (role: proposes)
mechanism: Algorithm D2 receives dividend and divisor digits most significant first. The first quotient digit follows after δ leading operand digits, and each later operand digit produces one quotient digit. The partial-remainder recurrence incorporates newly arriving dividend/divisor digits. Redundant quotient digits create overlapping selection regions, so quotient selection uses truncated estimates rather than full-precision comparisons. Redundant operands also permit carry-free partial-remainder updates. # pp.681-685
choices:
  online_delay: 4  # pp.683,685
  radix: 2; 10 [outside domain]  # pp.683,685
new_choices:
  operand_representation: {nonredundant, symmetric_redundant} — selects the binary restricted case or the carry-free generalized recurrence  # pp.682,684
  quotient_digit_set: symmetric_redundant_Dp — controls selection-region overlap and admissible estimates  # pp.683-685
slots: none
parameters: Binary division uses qi ∈ {0,1,-1}, δ=4, and m=24 in the worked example; decimal division uses r=10, p=6, K=2/3, and δ=4. # pp.683,685
results:
| metric | value | unit | technology / device | baseline | condition | page |
| on-line delay | 4 | bit | UNKNOWN; year 1977 | UNKNOWN | r=2; nonredundant dividend/divisor; redundant quotient | p.683 |
| on-line delay | 4 | digit | UNKNOWN; year 1977 | UNKNOWN | r=10, p=6, K=2/3 | p.685 |
errors_and_checks: The quotient converges to m-digit precision when the partial remainder remains within the stated divisor-scaled range; the binary proof uses -D < Pj < D, while the redundant proof uses -KD < Pj < KD. # pp.682-684
conditions: On-line operation requires a redundant result representation because a nonredundant representation cannot avoid full carry propagation. # pp.681-682 The binary derivation assumes a normalized fractional divisor with 1/2 < D < 1. # p.683 The generalized division construction excludes K=1/2 and K=1. # p.685
evidence: Section II; Algorithms D1/D2; equations (2.1)-(2.18); Figs. 1-2; binary example. # pp.682-685

### online_arithmetic_unit  (role: proposes)
mechanism: Incremental multiplication forms scaled partial products from the MSDF prefixes Xj and Yj. The recurrence wj = r(wj-1-dj-1) + Xj·yj + Yj-1·xj emits dj by signed nearest-integer selection. A symmetric redundant digit set bounds wj-dj, which permits carry-propagation-free recurrence evaluation and produces product digits from left to right. # pp.685-686
choices:
  radix: 2  # p.686
  online_delay: 1  # p.681
  digit_set: {minimally_redundant, maximally_redundant}  # p.686
  residual_form: signed_digit  # p.686
new_choices:
  digit_selection: sign(wj)·floor(|wj|+1/2) — rounding rule used to select each product digit  # p.686
slots: none
parameters: The algorithm accepts m-digit radix-r positive operands and Dp={-p,…,p}, with r/2 ≤ p ≤ r-1; the worked example uses r=2 and 8 input digits. # pp.685-686
results:
| metric | value | unit | technology / device | baseline | condition | page |
| on-line delay | 1 | digit | UNKNOWN; year 1977 | UNKNOWN | compatible MSDF multiplication | p.681 |
errors_and_checks: The selection rule guarantees |wm-dm| < 1/2, so the emitted digits represent the most significant half of X·Y with the final residual term retained in the convergence expression. # p.686
conditions: The recurrence requires operand-magnitude bounds to keep |wj| < p+1/2. # p.686 A maximally redundant system uses |X|,|Y| < 1/4, while closer analysis permits |X|,|Y| < 1/2 for r=2. # p.686
evidence: Section III; equations (3.1)-(3.11); radix-2 worked example. # pp.685-686

### generalized_signed_digit  (role: instantiates)
mechanism: Symmetric redundant digits provide multiple representations of a value, which limits carry propagation and creates overlapping digit-selection regions. Division uses the representation for quotient digits and optionally for operands/partial remainders. Multiplication uses it for the partial product and emitted product digits, allowing recurrence time independent of operand precision. # pp.681,684-686
choices:
  radix: 2; 10 [outside domain]  # pp.683,685-686
  redundancy: {minimal, intermediate, maximal}  # pp.684-686
  addition_scheme: carry_free  # pp.684,686
new_choices: none
slots: none
parameters: The symmetric digit set is Dp={-p,…,-1,0,1,…,p}; K=p/(r-1) is the degree of redundancy. # p.684
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry-propagation bound | 1 | digital position | UNKNOWN; year 1977 | nonredundant representation: δ=m | signed-digit addition/subtraction | p.681 |
errors_and_checks: none
conditions: Division requires intermediate redundancy rather than K=1/2 or K=1. # p.685 Multiplication permits r/2 ≤ p ≤ r-1. # p.686
evidence: Introduction; Sections II-B and III. # pp.681,684-686

## new_families
none

## space_gaps
* `online_msdf.radix` excludes radix 10 and the arbitrary-radix derivation established by the paper. # pp.684-685
* `online_msdf` lacks choices for operand representation and quotient-digit redundancy, although both determine selection feasibility and carry-free implementation. # pp.682-685
* `online_arithmetic_unit` lacks a digit-selection choice for the signed rounding function used by the multiplier. # p.686

## open_questions
* The decimal quotient-selection rules are omitted, so the exact comparator thresholds and estimate widths must not be inferred. # p.685
* The paper gives inequalities for general β/δ selection but does not tabulate concrete implementations beyond the binary and decimal examples. # pp.684-685
* Circuit technology, area, clock period, power, and pipeline register placement are not reported. # pp.681-687
