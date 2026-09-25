---
handle: muller_2016#s07
parent: muller_2016
citation: J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
chapter: Introduction to Shift-and-Add Algorithms
pdf_pages: 116-144
status: ok
kind: book_chapter
unit_classes: [VEC_SFU]
formats: [radix-2 fixed-point]
authority: textbook
pages_read: 29 / 29
---

## summary
The chapter derives exponential/logarithm evaluation from decompositions over discrete bases and implements each iteration with additions/shifts. It classifies restoring, nonrestoring, redundant signed-digit/carry-save, and Baker predictive variants. It proves convergence/error bounds and shows that redundant selection can inspect only a few residual digits.

## families
### digit_recurrence_exp_log  (role: defines)
mechanism: A residual is decomposed over weights ln(1 + 2^-n). Exponential evaluation maintains E_n = exp(t_n) through E_n+1 = E_n(1 + d_n2^-n), while logarithm evaluation drives E_n toward 1 and accumulates the corresponding logarithmic constants. Restoring variants select digits 0/1 by comparison. Faster variants use digits -1/0/1, redundant residual arithmetic, overlapping selection regions, and truncated residual prefixes. Baker’s variant predicts blocks of digits from the residual’s binary expansion and applies a correction after each block.
choices:
  radix: 2   # p.118
  normalization: multiplicative   # p.123
  digit_set: nonredundant (restoring)   # p.118
  digit_set: signed_redundant (faster variants)   # p.126
  selection: comparison [outside domain] (restoring)   # p.118
  selection: rounding_of_scaled_residual (redundant variants)   # p.129
  selection: table_lookup (selector implementation)   # p.130
  selection: binary_digit_prediction_with_correction [outside domain] (Baker)   # p.137
new_choices:
  residual_representation: {signed_digit, carry_save} — the redundant encoding used to avoid carry propagation   # p.126
  correction_schedule: repeated_last_weight — Baker’s correction reuses the last weight after a predicted block   # p.138
  initialization: table_with_residual_correction — a small table supplies initial digits before predictive blocks begin   # p.140
slots:
  none
parameters: Restoring evaluation takes N steps; redundant exponential evaluation starts at n = 1; Baker prediction starts at n ≥ 2; the worked Baker initializer uses n = 4 and m = 5.   # p.118, p.127, p.135, p.142
results:
| metric | value | unit | technology / device | baseline | condition | page |
| restoring exponential convergence domain | [0, 1.56202...] | input interval | abstract | UNKNOWN | weights ln(1 + 2^-n) | p.122 |
| restoring exponential relative error | ≤ 2^-n+1 | relative error | abstract | e^t | stopped at step n; rounding errors excluded | p.124 |
| restoring exponential precision | roughly n - 1 | significant bits | abstract | e^t | stopped at step n | p.124 |
| restoring logarithm input domain | 1 ≤ x ≤ product from i=0 to infinity of (1 + 2^-i) ≈ 4.768 | input interval | abstract | UNKNOWN | restoring logarithm | p.125 |
| restoring logarithm absolute error | ≤ 2^-n+1 | absolute error | abstract | ln(x) | stopped at step n; rounding errors excluded | p.125 |
| signed-digit exponential selector inspection | 1 | fractional digit | abstract | full-word comparison | scaled residual truncated after the first fractional digit | p.129 |
| signed-digit exponential selector prefix | 4 | digits | abstract | full-word comparison | direct redundant selection | p.130 |
| Takagi exponential selector prefix | 3 | digits | abstract | 4-digit selector | residual rewritten so digit L*n,2 is null | p.131 |
| signed-digit exponential selector table address | 4 | address bits | abstract | UNKNOWN | after conversion with a fast 4-bit adder | p.130 |
| signed-digit exponential direct selector table address | 8 | address bits | abstract | 4-address-bit table | without preliminary addition | p.130 |
| carry-save exponential selector prefix | 4 | digits | abstract | full-word comparison | carry-save residual | p.132 |
| carry-save exponential selector table address | 4 | address bits | abstract | full-word comparison | after conversion with a fast 4-digit adder | p.132 |
| redundant logarithm initial selector precision | 2 | fractional digits | abstract | later iterations | n = 1 with a redundant residual | p.134 |
| redundant logarithm convergence domain | [0.4194..., 3.4627...] | input interval | abstract | UNKNOWN | L1 in [s1 + 1, r1 + 1] | p.135 |
| logarithmic weight approximation error | 0 < 2^-i - ln(1 + 2^-i) < 2^-2i-1 | absolute bound | abstract | binary weight 2^-i | Baker prediction | p.135 |
| Baker logarithmic-weight prediction endpoint | 2n - 1 | iteration index | abstract | one-digit selection | predicted block starts at n | p.138 |
| Baker logarithmic-weight predicted block | n | digits | abstract | one-digit selection | digits d_n through d_2n-1 | p.138 |
| uncorrected initialization table input width | m = 2n + 1 | address bits | abstract | UNKNOWN | observed for 2 ≤ n ≤ 8 | p.140 |
| corrected initialization table input width | m = n + 1 | address bits | abstract | uncorrected initialization | sufficient for 2 ≤ n ≤ 10 | p.140 |
errors_and_checks: Infinite restoring iterations converge to the represented argument/function value. Finite exponential relative error and logarithm absolute error are bounded by 2^-n+1, but both analyses explicitly exclude rounding errors.   # p.123, p.124, p.125
conditions: Shift-and-add evaluation is mainly interesting for hardware because radix-power multiplications become shifts.   # p.118
conditions: Redundant addition avoids carry propagation, but full-word comparison or a huge lookup table would remove that speed advantage.   # p.126
conditions: Overlapping selection regions permit digit selection from a short residual prefix.   # p.128
conditions: Baker prediction requires a separate method for the first iterations, so the chapter uses a small initial table with a correction.   # p.139, p.140
evidence: Sections 6.1-6.4; Algorithms 6-7; Theorems 11-12; Figures 6.6-6.7; Tables 6.2-6.6.   # p.118, p.121, p.122, p.127, p.128, p.133, p.134, p.136, p.143

## taxonomy
* Shift-and-add decomposition   # p.118
  * Restoring decomposition with digits 0/1 -> digit_recurrence_exp_log   # p.121
  * Nonrestoring decomposition with digits -1/+1 -> digit_recurrence_exp_log   # p.122
* Simple exponential/logarithm algorithms   # p.122
  * Restoring exponential -> digit_recurrence_exp_log   # p.122
  * Restoring logarithm -> digit_recurrence_exp_log   # p.125
* Faster redundant algorithms   # p.126
  * Redundant exponential
    * Signed-digit implementation -> digit_recurrence_exp_log   # p.129
    * Carry-save implementation -> digit_recurrence_exp_log   # p.131
  * Redundant logarithm
    * Signed-digit implementation -> digit_recurrence_exp_log   # p.134
* Baker’s predictive algorithm   # p.135
  * Weights ln(1 + 2^-i), prediction through 2n - 1, then correction -> digit_recurrence_exp_log   # p.138
  * Weights arctan(2^-i), prediction through 3n - 1, then correction -> unmapped; the function application is deferred to the CORDIC chapter   # p.138
  * Initial table without correction -> digit_recurrence_exp_log   # p.140
  * Initial table with residual correction -> digit_recurrence_exp_log   # p.140

## primary_sources
* Briggs, 1624 — first convenient logarithm algorithms and 15-digit accurate tables in Arithmetica Logarithmica   # p.117
* Meggitt, UNKNOWN — shift-and-add iterations interpreted as pseudomultiplication and pseudodivision   # p.121
* Sarkar and Krishnamurthy, UNKNOWN — other pseudodivision algorithms   # p.121
* Chen, UNKNOWN — an algorithm very similar to the restoring exponential algorithm   # p.122
* Takagi, UNKNOWN — faster redundant algorithms adapted in Section 6.3   # p.126
* Baker, UNKNOWN — predictive digit selection originally designed for trigonometric functions and generalized here to exponentials/logarithms   # p.135
* Specker, 1965 — basic iterations for logarithms/exponentials and related elementary functions   # p.144
* Linhardt and Miller, UNKNOWN — similar shift-and-add algorithms   # p.144
* DeLugish, 1970 — analysis of shift-and-add algorithms for elementary functions   # p.144

## new_families
none

## space_gaps
* The `selection` domain lacks restoring full-residual comparison.   # p.118
* The `selection` domain lacks Baker’s binary-digit prediction followed by correction.   # p.137
* The family lacks a residual-representation choice for signed-digit versus carry-save implementations.   # p.126
* The family lacks selector-prefix/table-width choices, although the chapter compares three-digit/four-digit selectors and 4-address-bit/8-address-bit tables.   # p.130, p.131
* The family lacks a repeated-weight correction choice, which can also be viewed as permitting d_i = 2 at selected positions.   # p.138

## open_questions
* The finite-precision error after including arithmetic rounding remains UNKNOWN because the stated bounds exclude rounding errors.   # p.124, p.125
* The publication years for Meggitt, Sarkar and Krishnamurthy, Chen, Takagi, Baker, and Linhardt and Miller are not printed in the chapter text.
* The vocabulary does not determine whether Baker prediction is a new `selection` value or a distinct family.   # p.137
