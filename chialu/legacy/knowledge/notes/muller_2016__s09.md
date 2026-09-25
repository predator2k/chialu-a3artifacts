---
handle: muller_2016#s09
parent: muller_2016
citation: J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
chapter: Some Other Shift-and-Add Algorithms
pdf_pages: 169-182
status: ok
kind: book_chapter
unit_classes: [VEC_SFU]
formats: [real, complex, radix-16 signed-digit, radix-2 conventional, radix-2 signed-digit, binary carry-save]
authority: textbook
pages_read: 14 / 14
---

## summary
The chapter defines a radix-16 digit-recurrence exponential algorithm and the scale-free complex BKM shift-and-add algorithm. It establishes digit-selection rules, convergence domains, iteration/error expressions, function coverage, and the scaling problem of redundant CORDIC.   # p.169, p.174-p.181

## families
### digit_recurrence_exp_log  (role: defines)
mechanism: The exponential iteration updates a logarithmic residual by subtracting ln(1 + dn 16^-n) and updates the exponential state by multiplying by 1 + dn 16^-n. Digits are selected so that the residual remains inside shrinking convergence intervals. A scaled residual L*n = 16^n Ln permits selection by rounding a truncated binary or carry-save representation.
choices:
  radix: 16   # p.169
  normalization: multiplicative   # p.169
  digit_set: signed_redundant   # p.169
  selection: rounding_of_scaled_residual   # p.171
new_choices:
  digit_magnitude: 10 — dn belongs to {-10, ..., 10}   # p.169
  first_step_strategy: {start_at_n_2, special_correction} — the ordinary selection intervals do not cover the first iteration   # p.171-p.173
slots:
  none
parameters: An n-bit approximation requires roughly n/k iterations in radix 2^k; radix 16 uses dn in {-10, ..., 10}; ordinary selection examines five fractional binary digits or six fractional carry-save digits.   # p.169, p.171
results:
| metric | value | unit | technology / device | baseline | condition | page |
| normalized minimum selection overlap | -1.13244, 0.29479, 0.33101, 0.33319, 1/3 | 16^n × interval width | abstract | UNKNOWN | n = 1, 2, 3, 4, infinity | p.171 |
| normalized maximum selection overlap | 0.70644, 0.36911, 0.33565, 0.33348, 1/3 | 16^n × interval width | abstract | UNKNOWN | n = 1, 2, 3, 4, infinity | p.171 |
| convergence domain when starting at n = 2 | approximately [-0.03435, 0.03337] | input interval | abstract | UNKNOWN | [T2^-8, U2^8] | p.172 |
| iteration count | n/k | iterations | abstract | radix-2 shift-and-add | radix-2^k algorithm producing an n-bit approximation | p.169 |
errors_and_checks: The chapter states an n-bit approximation target but gives no final-rounding contract or fault-detection mechanism.   # p.169
conditions: The standard digit-selection condition fails for some digits at n = 1, so the first step must differ.   # p.171
conditions: Nearest-integer selection from a truncated residual is valid for n >= 3, or for n = 2 when T2^-8 <= L2 <= U2^8.   # p.171
conditions: Starting at n = 2 gives a small convergence domain; a special first step can instead use a correction factor implemented as a small-integer multiplication and a shift.   # p.172-p.173
evidence: Section 8.1.1; Equations 8.1-8.4; Figure 8.1; Tables 8.1-8.3.   # p.169-p.173

### redundant_high_radix_cordic  (role: analyzes)
mechanism: Redundant CORDIC can use carry-save or signed-digit arithmetic to simplify digit evaluation. Allowing dn = 0 then makes the scale factor nonconstant unless the implementation uses more iterations, more complicated iterations, or Dawid and Meyr’s method.
choices:
  residual_arithmetic: carry_save or signed_digit   # p.174
  radix: 2   # p.174
  scale_handling: UNKNOWN   # p.174
  coarse_fine_hybrid: UNKNOWN   # p.174
new_choices:
  zero_digit_allowed: true — dn = 0 simplifies digit evaluation but makes the scale factor nonconstant   # p.174
slots:
  none
parameters: radix-2 conventional or redundant representation; dn includes zero.   # p.174
results:
| metric | value | unit | technology / device | baseline | condition | page |
| additional work for constant scaling | more iterations or more complicated iterations | abstract iteration cost | abstract | conventional CORDIC | redundant digit evaluation with dn = 0 | p.174 |
errors_and_checks: none
conditions: The scaling drawback applies when redundant arithmetic requires dn = 0 for easier digit evaluation.   # p.174
conditions: A constant scale requires additional iterations, more complicated iterations, or Dawid and Meyr’s method.   # p.174
evidence: Section 8.2 introductory comparison with CORDIC.   # p.174

## taxonomy
* Some Other Shift-and-Add Algorithms
  * High-Radix Algorithms
    * Ercegovac’s radix-16 exponential algorithm -> digit_recurrence_exp_log   # p.169
      * Start iterations at n = 2 -> digit_recurrence_exp_log   # p.172
      * Special first step with M = exp((2k+1)/32) -> digit_recurrence_exp_log   # p.172-p.173
      * Special first step using exp(ε) = 1 + k/32 -> digit_recurrence_exp_log   # p.173
  * Redundant CORDIC scaling alternatives
    * More iterations -> redundant_high_radix_cordic   # p.174
    * More complicated iterations -> redundant_high_radix_cordic   # p.174
    * Dawid and Meyr’s method -> redundant_high_radix_cordic   # p.174
  * BKM Algorithm
    * E-mode: choose dn so Ln converges to 0 and En converges to E1 exp(L1) -> unmapped   # p.174-p.178
    * L-mode: choose dn so En converges to 1 and Ln converges to L1 + ln(E1) -> unmapped   # p.178-p.179
    * Functions using one mode
      * Real sine and cosine -> unmapped   # p.180
      * Real exponential -> unmapped   # p.180
      * Real logarithm -> unmapped   # p.180
      * 2-D rotations -> unmapped   # p.180
      * Real arctangent and ln(x^2+y^2)/2 -> unmapped   # p.180
    * Functions using two consecutive modes
      * Complex multiplication and division -> unmapped   # p.180
      * Parallel x√a and y√a, or x/√a and y/√a -> unmapped   # p.180
      * 2-D vector lengths and normalization -> unmapped   # p.181
    * Radix-10 generalization -> unmapped   # p.181
    * High-Radix BKM -> unmapped   # p.181

## primary_sources
* Ercegovac, UNKNOWN — radix-16 exponential algorithms and their higher-radix generalization   # p.169
* Xavier Merrheim, UNKNOWN — variants of Ercegovac’s methods   # p.169
* Dawid and Meyr, UNKNOWN — a method avoiding the redundant-CORDIC scaling alternatives   # p.174
* Bajard et al., UNKNOWN — the BKM algorithm, Robertson diagrams, and convergence proof   # p.174-p.179
* Imbert, Muller and Rico, UNKNOWN — radix-10 generalization of BKM   # p.181
* Didier and Rico, UNKNOWN — High-Radix BKM   # p.181

## new_families
### bkm_complex_shift_add  (domain: sfu: elementary-function units, closest: digit_recurrence_exp_log, why_not: BKM uses complex states/digits to provide scale-free rotations and a larger function set that the real exp/log recurrence does not represent.)
mechanism: BKM maintains complex states En and Ln with En+1 = En(1 + dn 2^-n) and Ln+1 = Ln - ln(1 + dn 2^-n). Its nine-value complex digit alphabet makes multiplication by dn reducible to a few additions. E-mode drives Ln to zero; L-mode drives En to one. Real and imaginary digit components are selected independently from truncated residual digits.
choices:
  mode: {E_mode, L_mode}   # p.174, p.178
  number_system: {radix2_conventional, radix2_signed_digit, binary_carry_save}   # p.174
  digit_alphabet: {-1, 0, 1, -i, i, 1-i, 1+i, -1-i, -1+i}   # p.174
  selection_fractional_bits: {3_real_4_imag_E_mode, 4_both_L_mode}   # p.177-p.179
  first_step: {standard_E_mode, special_L_mode}   # p.178-p.179
  radix_generalization: {2, 10, high_radix}   # p.174, p.181
results:
| metric | value | unit | technology / device | baseline | condition | page |
| E-mode relative error | approximately 2^-n | relative error | abstract | UNKNOWN | after n iterations | p.178 |
| E-mode real convergence domain | [-0.8298023738..., 0.8688766517...] | residual interval | abstract | UNKNOWN | real part of L1 | p.177 |
| E-mode imaginary convergence domain | [-0.749780302..., 0.749780302...] | residual interval | abstract | UNKNOWN | imaginary part of L1 | p.177 |
| L-mode proven convergence domain | x = 1/2, x = 1.3, y = x/2, y = -x/2 | trapezoid boundaries | abstract | UNKNOWN | E1 belongs to T | p.178 |
| sine/cosine error | ± 2^-n | absolute error | abstract | UNKNOWN | E-mode with L1 = iθ | p.180 |
| real exponential error | ± 2^-n | absolute error | abstract | UNKNOWN | L1 in [-0.8298023738, +0.8688766517] | p.180 |
| real logarithm error | ± 2^-n | absolute error | abstract | UNKNOWN | E1 in [0.5, 1.3] | p.180 |
evidence: Sections 8.2.1-8.2.4; Equations 8.5-8.10; Figures 8.2-8.4.   # p.174-p.181

## space_gaps
* digit_recurrence_exp_log lacks a digit-magnitude choice for the radix-16 set {-10, ..., 10}.   # p.169
* digit_recurrence_exp_log lacks a first-iteration strategy choice for start-at-n = 2 versus special correction.   # p.171-p.173
* digit_recurrence_exp_log permits radix 16 but lacks the unspecified radices above 16 to which the method is said to generalize.   # p.169
* No existing family represents BKM’s complex digit alphabet, E/L modes, scale-free rotations, and two-mode function composition.   # p.174-p.181

## open_questions
* The bibliographic years for references [18], [114], [127], [175], and [229] are absent from the supplied chapter text.
* The chapter cites radix-10 and High-Radix BKM variants without defining their recurrences, digit sets, or selection rules.   # p.181
* The real-logarithm bullet calls its computation “E-mode,” although the result variable Ln and the preceding L-mode definition indicate an unresolved wording inconsistency.   # p.178-p.180
