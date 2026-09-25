---
handle: pineiro_2005
citation: J.-A. Pineiro, S. F. Oberman, J.-M. Muller, J. D. Bruguera, "High-Speed Function Approximation Using a Minimax Quadratic Interpolator", IEEE Transactions on Computers, vol. 54, no. 3, pp. 304-318, 2005
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fp32, fixed16-32]
authority: incremental
pages_read: 15 / 15
---

## summary
The paper proposes a table-driven, piecewise minimax quadratic interpolator for single-precision reciprocal/square root/reciprocal square root/exponential/logarithm/trigonometric/powering/special functions (pp.304-306). A specialized squarer, signed-digit recoding, and fused carry-save accumulation give quadratic interpolation a reported delay near that of linear interpolation while reducing coefficient-table area (pp.311-316).

## families
### piecewise_poly  (role: extends)
mechanism: The significand is split as X = X1 + X2, where X1 selects a subinterval and addresses tables containing C0, C1, and C2. The interpolator evaluates C0 + C1X2 + C2X2². A three-pass minimax procedure successively compensates for finite-wordlength rounding of C1, C2, and C0. Exhaustive single-precision simulation selects coefficient widths and a function-specific bias that is injected before result truncation (pp.306-311).
choices:
  segments: 64; 128 [outside domain]   # pp.307, 311
  degree: 2   # pp.306-307
  basis: minimax_remez   # pp.307-311
  coeff_encoding: per_coeff_width   # pp.307-311
  coefficient_optimization: joint_wordlength_search   # pp.308-311
  rounding_contract: faithful   # p.308
new_choices:
  coefficient_rounding_compensation: three_pass_hybrid — Successive passes account for rounding C1, C2, and C0 to finite wordlengths.   # pp.308-311
  output_rounding_bias: function_specific_exhaustive — Exhaustive simulation selects a bias injected before truncation.   # pp.308, 313-314
slots:
  evaluator: parallel_monomial   # pp.307, 311-314
  segmenter: uniform_high_bit_decode   # pp.306-307
parameters: X1 width m = 6 for square root/exponential and m = 7 for reciprocal/logarithm; 24-bit significand; C0/C1/C2 implementation buses = 27/18/13 bits; target accuracies = 1 ulp, 2 ulps, or 4 ulps   # pp.307, 311, 313, 317
results:
| metric | value | unit | technology / device | baseline | condition | page |
| coefficient tables, four-function unit | about 22.2 | Kbit | technology-independent model (2005) | none | reciprocal/square root/2^X/log2 X, 1 ulp | p.313 |
| reciprocal coefficient table | 6.375 | Kb | technology-independent model (2005) | none | 1 ulp | p.313 |
| logarithm coefficient table | 6.5 | Kb | technology-independent model (2005) | none | 1 ulp | p.313 |
| exponential coefficient table | 3.1875 | Kb | technology-independent model (2005) | none | 1 ulp | p.313 |
| square-root coefficient tables | 2 × 3.0625 | KB | technology-independent model (2005) | none | even/odd exponent tables, 1 ulp | p.313 |
errors_and_checks: Results are guaranteed accurate to 1 ulp, 2 ulps, or 4 ulps according to the selected configuration. The 1 ulp configuration provides faithful rounding for reciprocal/square root/reciprocal square root/exponential. The bias is selected by exhaustive simulation, so the rounding scheme is stated to be unsuitable for higher precision (pp.306, 308).
conditions: The method targets single precision and fixed-point targets from 16 to 32 bits. The method can also produce seeds for higher-precision Newton-Raphson/Goldschmidt computation (pp.305, 317). Range reduction/reconstruction use standard function-specific techniques and are excluded from the evaluated core; their delay and area may be additional (pp.306, 313-315).
evidence: Sections 3.2-3.5; Figs. 2-5; Tables 1-4 (pp.306-313).

### gpu_multifunction_interpolator  (role: instantiates)
mechanism: One unfolded interpolation datapath shares the squarer, recoders, fused accumulation tree, final CPA, and normalization hardware across reciprocal/square root/exponential/logarithm. Per-function coefficient tables are selected by operation bits; square root also uses the exponent LSB. The architecture can be pipelined into three stages (pp.313-314).
choices:
  function_set: full_transcendental_set   # pp.304-305, 317
  interpolation_degree: 2   # pp.306-307
  coefficient_precision_grading: per_function   # pp.311, 313
new_choices:
  coefficient_storage: replicated_per_function_or_single_rom — Function tables may be replicated or combined in one addressed ROM.   # p.313
slots:
  quadratic_core: parallel_monomial   # pp.311-314
parameters: four implemented functions; unfolded architecture; straightforward three-stage pipeline; two operation-select bits; 24-bit significand   # pp.313-314
results:
| metric | value | unit | technology / device | baseline | condition | page |
| cycle time | 14.5 | τ | technology-independent full-adder model (2005) | none | critical path B | p.314 |
| total area | 1,291 | fa | technology-independent full-adder model (2005) | none | four-function architecture | p.314 |
| table area | 776 | fa | technology-independent full-adder model (2005) | none | 22.2Kbit tables | p.314 |
| combinational-logic area | 515 | fa | technology-independent full-adder model (2005) | none | excludes exponent/sign/range reduction | p.314 |
| linear-method hardware requirement | 2 to 3 | times higher per function | technology-independent full-adder model (2005) | minimax quadratic interpolator | reciprocal, 1 ulp | p.315 |
| competing quadratic execution time | over two | times longer | technology-independent full-adder model (2005) | proposed interpolator | four operations, 1 ulp | p.316 |
errors_and_checks: The implemented reciprocal/square root/exponential/logarithm architecture targets 1 ulp accuracy (pp.313-316).
conditions: The estimates exclude exponent/sign/exception logic and range reduction. The comparisons use a common technology-independent model rather than fabricated-silicon measurements (pp.314-316).
evidence: Section 4, Fig. 6, Tables 5-7 (pp.313-316).

### carry_save_datapath  (role: instantiates)
mechanism: SD radix-4 recoding halves the partial products for C1X2 and C2X2². A fused tree accumulates both products, C0, and the rounding bias without intermediate assimilation. For m = 6, a preliminary 3:2 level reduces nine C1X2 products while X2² is formed; three 4:2 levels then feed one final CPA (pp.311-314).
choices:
  compressor: 4_2   # pp.312-314
  assimilation_point: end_of_chain   # pp.307, 312-314
  accumulator_redundant: true   # pp.307, 311-314
new_choices:
  multiplier_digit_recoding: signed_digit_radix_4 — X2 and carry-save X2² are recoded to SD-4 before partial-product generation.   # pp.307, 311-314
slots:
  assimilator: UNKNOWN
parameters: 18 initial operands for m = 6; 16 initial operands for m = 7; one 3:2 preprocessing level and three effective 4:2 levels; one terminal CPA   # p.312
results:
| metric | value | unit | technology / device | baseline | condition | page |
| fused-tree delay penalty | about 0.5 | τ slower | technology-independent full-adder model (2005) | standard 24 × 24-bit multiplier | final CPA excluded from both expressions | p.312 |
| fused accumulation-tree area | 400 | fa | technology-independent full-adder model (2005) | none | m = 6 shared architecture | p.314 |
errors_and_checks: The injected bias compensates in some cases for squarer truncation and approximation error before the final truncation (pp.308, 313).
conditions: SD radix-8 can reduce the number of products, but storing 3× coefficient multiples can increase table size. The selected SD radix-4 organization minimizes table storage while scheduling one 3:2 level outside the critical path (p.312).
evidence: Sections 3.5.2 and 4; Figs. 5-6; Tables 4-5 (pp.312-314).

## new_families
none

## space_gaps
* `piecewise_poly.segments` stops at 64, while the m = 7 configurations use 2^7 = 128 coefficient-table entries (pp.307, 311).
* `piecewise_poly` lacks a choice for successive minimax passes that compensate for finite coefficient wordlengths (pp.308-311).
* `piecewise_poly` lacks a choice for function-specific bias injection before truncation (pp.308, 313).

## open_questions
* The exact per-function coefficient widths/implicit-bit patterns and reported approximation errors in Tables 1-3 are not recoverable from the supplied table images.
* The final CPA topology is not identified, so the `carry_save_datapath.assimilator` slot remains `UNKNOWN`.
* The paper reports model-based area/delay estimates rather than a technology node, clock frequency, or fabricated implementation.
