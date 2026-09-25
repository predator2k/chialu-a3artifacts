---
handle: muller_2018#s07
parent: muller_2018
citation: J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
chapter: 7 Algorithms for the Basic Operations
pdf_pages: 251-284
status: ok
kind: book_chapter
unit_classes: [other]
formats: [binary basic formats, decimal basic formats, binary16, binary32, binary64, binary128, decimal64]
authority: textbook
pages_read: 34 / 34
---

## summary
The chapter defines correctly rounded addition/subtraction, multiplication, division, square root, and FMA for radix 2 or 10 basic formats. It classifies division and square-root algorithms, derives alignment/normalization bounds, and treats subnormals/decimal cohorts/nonhomogeneous operations. It also specifies a mixed-precision FMA with narrow products and wider accumulation.

## families
### single_path  (role: defines)
mechanism: Compare exponents, align the smaller significand, perform an exact effective addition or subtraction, normalize after a carry or cancellation, and round from the round/guard/sticky information. Close cases permit cancellation and need leading-zero counting; far cases need the large alignment shift but at most one normalization digit.
choices:
  pipeline_depth: UNKNOWN   # p.260
  post_round_renorm: UNKNOWN   # p.261
new_choices:
  case_partition: close_or_far — distinguishes cancellation from large-alignment cases   # p.261
slots:
  sig_adder: UNKNOWN   # p.260
  round: UNKNOWN   # p.261
  exp: exponent_path   # p.260
  subnormal: full_hardware   # p.263
  align: full_align   # p.260
  norm: coarse_fine   # p.260
parameters: precision p; alignment shift at most p + 1 digits; effective significand addition at most p digits   # p.261
results:
| metric | value | unit | technology / device | baseline | condition | page |
| effective addition width | p | digits | abstract | UNKNOWN | addition/subtraction | p.261 |
| maximum alignment shift | p + 1 | digits | abstract | UNKNOWN | larger exponent difference contributes only to sticky | p.261 |
| cancellation alignment shift | 0 or 1 | digits | abstract | UNKNOWN | close case | p.261 |
errors_and_checks: Correct rounding uses round/guard/sticky information; invalid, overflow, underflow, and inexact are the possible exceptions.   # p.259, p.261
conditions: Close and far cases make the two large shifts mutually exclusive; sticky computation can largely run in parallel with significand addition.   # p.261
evidence: Section 7.3; Tables 7.1-7.3

### decimal_fp_addition  (role: analyzes)
mechanism: Decimal addition preserves the preferred exponent for exact results. The implementation normalizes to determine exactness, then may shift the exact result back toward the smaller input exponent. POWER6 separates equal-exponent, align-to-smaller-exponent, and general two-operand-shift cases.
choices:
  alignment: full_shifter   # p.262
  rounding: UNKNOWN   # p.262
  leading_zero_anticipation: UNKNOWN   # p.262
  format: decimal64   # p.262
new_choices:
  alignment_case: equal_exponents | align_to_smaller_exponent | shift_both — POWER6 case partition   # p.262
slots:
  significand_adder: UNKNOWN   # p.262
parameters: decimal64; 9 to 17 cycles   # p.262
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 9 to 17 | cycles | IBM POWER6 | UNKNOWN | decimal64 addition | p.262 |
errors_and_checks: Exactness is determined from carry-out/sticky bits and round/guard digits.   # p.262
conditions: Equal exponents form the common and simplest accounting case; binary-encoded decimal replaces alignment by multiplication with a tabulated 10^k for 0 ≤ k ≤ p.   # p.262, p.263
evidence: Sections 7.3.1-7.3.2

### sig_mul_then_round  (role: defines)
mechanism: Multiply the fixed-point significands exactly, add exponents, normalize the product by at most one digit for normal inputs, and round using guard/round/sticky information. Subnormal handling adds leading-zero counting, normalization, an extended exponent, and a right shift before rounding.
choices:
new_choices:
  subnormal_normalization_position: input | product — normalize the subnormal operand before multiplication or normalize the product afterward   # p.265
slots:
  sig_mul: UNKNOWN   # p.264
  round: UNKNOWN   # p.264
  exp: exponent_path   # p.264
  subnormal: full_hardware   # p.265
parameters: p-digit operands; 2p-digit product; partial sticky over p − 1 digits; internal exponent one bit wider for subnormal handling   # p.264, p.265
results:
| metric | value | unit | technology / device | baseline | condition | page |
| product width | 2p | digits | abstract | UNKNOWN | two p-digit significands | p.264 |
| normalization shift | at most 1 | digit | abstract | UNKNOWN | normal inputs | p.264 |
| partial sticky width | p − 1 | digits | abstract | UNKNOWN | normal product | p.264 |
errors_and_checks: Invalid, overflow, underflow, and inexact are the possible exceptions.   # p.264
conditions: Product normalization after multiplication permits leading-zero counting in parallel with multiplication. Decimal products are fast and exact when the input leading-zero counts sum to more than p.   # p.265, p.266
evidence: Sections 7.4.1-7.4.3; Table 7.4

### classic_fma  (role: defines)
mechanism: Form the unrounded 2p-digit product, align it with the p-digit addend, perform one effective addition or subtraction, normalize, and round once. The single-path binary algorithm superimposes product-anchored, addend-anchored, cancellation, and subnormal cases.
choices:
  subsume_fp_add: UNKNOWN   # p.272
  negation_handling: complement_recode   # p.272, p.273
  pipeline_depth: UNKNOWN   # p.272
new_choices:
  case_organization: single_path — one path handles all alignment/cancellation cases   # p.272
slots:
  align: full_align   # p.272
  lza: lzc_after_add   # p.273
  cpa: UNKNOWN   # p.273
  round: UNKNOWN   # p.274
  multiplier: UNKNOWN   # p.272
parameters: product-anchored shift at most 2p − 1 digits for normal inputs; cancellation addition and normalization width 2p + 1 digits; single-path sum width 3p + 5 digits   # p.267, p.269, p.272
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum addend shift | 2p − 1 | digits | abstract | UNKNOWN | normal product-anchored case | p.267 |
| cancellation width | 2p + 1 | digits | abstract | UNKNOWN | −1 ≤ d ≤ 2 and effective subtraction | p.269 |
| maximum cancellation | 2p − 1 | bits | abstract | UNKNOWN | Example 7.2 | p.269 |
| single-path computation width | 3p + 5 | digits | abstract | UNKNOWN | binary FMA | p.272 |
| maximum binary64 shift | 163 | bits | abstract | UNKNOWN | shifting c in the single-path algorithm | p.272 |
errors_and_checks: The final normalized significand is rounded once; two extra exponent bits suffice to handle overflow at that point.   # p.274
conditions: Product-anchored cases have d ≤ −2; addend-anchored cases have d ≥ 3 or d ≥ −1 with effective addition; cancellation requires −1 ≤ d ≤ 2 with effective subtraction.   # p.267-p.269
evidence: Sections 7.5.1-7.5.4; Figures 7.2-7.6

### decimal_fma  (role: analyzes)
mechanism: Decimal FMA uses the same alignment cases as binary FMA but must preserve cohorts. Inexact results use the least possible exponent; exact results target min(Q(a) + Q(b), Q(c)) and avoid normalization when possible.
choices:
  structure: UNKNOWN   # p.271
  internal_encoding: bcd [outside domain evidence incomplete]   # p.271
  binary_decimal_combined: UNKNOWN   # p.271
new_choices:
  preferred_quantum_exponent: min(Q(a) + Q(b), Q(c)) — exponent required for exact results   # p.271
slots:
  multiplier_tree: UNKNOWN   # p.271
parameters: addend-anchored leading-zero count up to p + 4 digits   # p.271
results:
| metric | value | unit | technology / device | baseline | condition | page |
| leading-zero count width | p + 4 | digits | abstract | p | decimal addend-anchored case | p.271 |
errors_and_checks: Correct rounding and cohort selection apply after the case-specific exact computation.   # p.271
conditions: The chapter reports one software decimal FMA and refers hardware evaluation to Vázquez’s dissertation.   # p.272
evidence: Section 7.5.3

### sig_div_then_round  (role: taxonomizes)
mechanism: Normalize operands, compute mx/my with a possible one-digit normalization, then obtain enough quotient/remainder information to round correctly. Digit recurrence retains an exact quotient/remainder identity; functional iteration and polynomial approximation require method-specific rounding proofs or remainder computation.
choices:
new_choices:
  significand_algorithm: digit_recurrence | functional_iteration | polynomial_approximation — three principal algorithm families   # p.275, p.276
slots:
  sig_div: UNKNOWN   # p.275, p.276
  round: UNKNOWN   # p.276
  exp: exponent_path   # p.275
  subnormal: full_hardware   # p.276
parameters: p iterations for digit recurrence; O(log p) functional iterations; at least twice target precision for the last functional iteration   # p.276
results:
| metric | value | unit | technology / device | baseline | condition | page |
| digit-recurrence iterations | p | iterations | abstract | UNKNOWN | quotient rounded to precision p | p.276 |
| digit-recurrence iteration count | O(p) | iterations | abstract | UNKNOWN | compared with functional iteration | p.276 |
| functional iteration count | O(log p) | iterations | abstract | O(p) | compared with digit recurrence | p.276 |
| final functional precision | at least twice p | digits | abstract | p | correct rounding via exclusion lemma | p.276 |
| multiplier size | 76 × 76 | bits | AMD processor | UNKNOWN | supports p = 64 without FMA | p.276 |
errors_and_checks: Digit recurrence detects exactness from a null remainder; polynomial methods compute a remainder; suitable FMA iterations can transfer exact inexact-flag behavior to the final FMA.   # p.277
conditions: Digit recurrence suits integer-add hardware and is exact; functional iteration suits multiplier-equipped processors but rounds intermediates; subnormal digit recurrence may stop after the needed digits.   # p.275-p.277
evidence: Sections 7.6.1-7.6.5; Table 7.5

### mixed_precision_cascade_fma  (role: analyzes)
mechanism: Compute a narrow-format product and add it without intermediate rounding to a wider-format addend, returning the correctly rounded wider-format result. The intermediate path is sized between a narrow homogeneous FMA and a wide homogeneous FMA.
choices:
  exact_product_preserved: true   # p.282
  two_term_expansion_output: UNKNOWN   # p.282
new_choices:
  operand_precision_relation: q ≥ 2p + 2 — relation for the format pairs discussed   # p.284
slots:
  align: full_align   # p.284
  lza: lzc_after_add   # p.284
  cpa: UNKNOWN   # p.284
  round: UNKNOWN   # p.282
  multiplier: UNKNOWN   # p.282
parameters: multiplier precision p; addend/result precision q; intermediate width q + 2p + 5 bits   # p.284
results:
| metric | value | unit | technology / device | baseline | condition | page |
| cost overhead | one third more | cost | abstract | classical FMA in smaller format | mixed-precision FMA | p.283 |
| intermediate width | q + 2p + 5 | bits | abstract | 3p + 5 / 3q + 5 | mixed-precision FMA | p.284 |
| subnormal-product normalization shift | up to 2p | bits | abstract | UNKNOWN | either or both narrow operands subnormal | p.284 |
errors_and_checks: The operation returns one correctly rounded wider-format result and avoids the loss from narrow accumulation.   # p.282, p.283
conditions: The chapter identifies binary32 products into binary64, binary64 products into binary128, and binary16 products into binary32 as use cases. A subnormal wider addend needs no added handling overhead.   # p.283, p.284
evidence: Sections 7.8.2-7.8.4

## taxonomy
* Basic-operation result computation   # p.252, p.253
  * Finite exact intermediate result
    * addition/subtraction -> single_path   # p.252
    * multiplication -> sig_mul_then_round   # p.252
    * FMA -> classic_fma   # p.252
  * Potentially infinite exact result
    * division -> sig_div_then_round   # p.253
    * square root -> unmapped   # p.253
* Addition cases   # p.261, p.262
  * close case -> single_path
  * far case -> single_path
  * decimal equal exponents -> decimal_fp_addition
  * decimal align to smaller exponent -> decimal_fp_addition
  * decimal shift both operands -> decimal_fp_addition
* FMA alignment cases   # p.267-p.269
  * product-anchored -> classic_fma
  * addend-anchored -> classic_fma
  * cancellation -> classic_fma
* Division algorithms   # p.275, p.276
  * digit recurrence
    * binary recurrence -> restoring_nonrestoring
    * higher-radix SRT -> srt_high_radix
  * functional iteration -> newton_raphson
  * polynomial inverse approximation -> unmapped
* Square-root algorithms   # p.278
  * digit recurrence -> digit_recurrence_sqrt_combined
  * functional iteration -> newton_raphson
  * polynomial approximation -> unmapped
* Nonhomogeneous operations   # p.281-p.284
  * software double-rounding correction -> unmapped
  * narrow product/wide accumulation -> mixed_precision_cascade_fma

## primary_sources
* Sweeney, Robertson, and Tocher, year not given — SRT digit-recurrence algorithms   # p.275
* Cornea et al., year not given — binary-encoded decimal rounding/addition algorithms   # p.258, p.263
* Lutz and Burgess, year not given — software implementation of heterogeneous operations around double rounding   # p.280, p.281

## new_families
### fp_significand_sqrt_then_round  (domain: fp, closest: sig_div_then_round, why_not: the vocabulary has an FP division wrapper but no corresponding square-root wrapper)
mechanism: Normalize the input, adjust the exponent to even parity, compute the significand square root by digit recurrence/functional iteration/polynomial approximation, and round correctly. A finite positive square root cannot produce underflow or overflow.
choices: significand_algorithm: {digit_recurrence, functional_iteration, polynomial_approximation}; subnormal_input_normalization: {pre_normalize}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| exponent exceptions | neither underflow nor overflow | exception classes | abstract | UNKNOWN | finite positive input | p.279 |
evidence: p.277-p.279

### polynomial_significand_approximation  (domain: div, closest: newton_raphson, why_not: direct polynomial approximation is distinct from an iterative reciprocal refinement)
mechanism: Approximate 1/y, x/y, or sqrt(x) sufficiently accurately with a polynomial, optionally combined with functional iteration, then compute a remainder or equivalent evidence for correct rounding.
choices: target: {reciprocal, ratio, square_root}; composition: {polynomial_only, combined_with_iteration}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| accuracy requirement | required accuracy | UNKNOWN | abstract | UNKNOWN | correctly rounded basic operation | p.276, p.278 |
evidence: p.276, p.278

## space_gaps
* The FP family vocabulary lacks a square-root wrapper corresponding to sig_div_then_round.   # p.277-p.279
* The vocabulary lacks the chapter’s direct polynomial division/square-root algorithm family.   # p.276, p.278
* decimal_fma lacks a choice for preferred quantum-exponent handling.   # p.271

## open_questions
* The chapter does not identify the concrete significand adder, multiplier-tree, CPA, or rounding-cell families used by the abstract algorithms.
* The publication years for several cited primary sources are not present in the supplied chapter text.
