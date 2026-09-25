---
handle: muller_2018#s10
parent: muller_2018
citation: J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
chapter: 10 Evaluating Floating-Point Elementary Functions
pdf_pages: 393-452
status: ok
kind: book_chapter
unit_classes: [VEC_SFU]
formats: [binary32, binary64, decimal32, decimal64, binary128, decimal128]
authority: textbook
pages_read: 60 / 60
---

## summary
The chapter classifies elementary-function evaluation into range reduction, local approximation, reconstruction, and final rounding. It defines polynomial/CORDIC methods, Horner/Estrin evaluation, accurate range reduction, and the Table Maker’s Dilemma. It establishes two-step Ziv evaluation as a bounded method for correctly rounded binary64 functions.   # p.393, p.394, p.414, p.416, p.446

## families
### range_reduction  (role: taxonomizes)
mechanism: Additive reduction computes y = x − kC in a bounded interval, while multiplicative reduction uses identities such as ln(x·2^k) = ln(x) + k·ln(2). Cody-Waite splits C into floating-point terms. Payne-Hanek multiplies the significand by a moving window of bits of 1/π. Table-assisted multistage reductions produce smaller arguments for low-degree approximation.
choices:
  method: cody_waite   # p.397
  method: payne_hanek   # p.399
  method: table_augmented   # p.403
  split_constant_terms: 2   # p.397
  split_constant_terms: 3   # p.399
  reduction_type: additive   # p.395
  reduction_type: multiplicative   # p.395
  worst_case_bound_proven: true   # p.400
new_choices:
  reduced_argument_representation: one_word | double_word | triple_word — representation used when one floating-point value is insufficient   # p.403
  reduction_steps: one | two | repeated — number of successive reductions   # p.403, p.406
slots: none
parameters: binary64; C = π/2, π/256, or ln(2); table indices of 6 to 8 bits or two 6-bit indices; reduced arguments may use two or three floating-point values   # p.395, p.399, p.404, p.406
results:
| metric | value | unit | technology / device | baseline | condition | page |
| naive sine reduction significant digits | 2 | decimal digits | abstract | exact reduction | x = 5419351, binary64 | p.396 |
| Cody-Waite exact-product limit | 5340353 | integer multiplier | abstract | UNKNOWN | stated C1, binary64 | p.398 |
| CRlibm two-term range | \|x\| < 6433 | input magnitude | abstract | UNKNOWN | C = π/256 | p.399 |
| CRlibm three-term range | 6433 ≤ \|x\| < 13176794 | input magnitude | abstract | two-term split | binary64 | p.399 |
| smallest binary64 reduced argument | 2^-60.89 | absolute value | abstract | UNKNOWN | C = π/2 | p.401 |
| exponential table size | 2^12 | entries | abstract | UNKNOWN | ℓ = 12 | p.404 |
| logarithm table size | 64 to 256 | entries | abstract | UNKNOWN | index width 6 to 8 | p.406 |
errors_and_checks: Payne-Hanek selects stored 1/π bits from the desired absolute-error bound. Continued fractions bound the smallest reduced argument and convert absolute-error bounds into relative-error bounds.   # p.400, p.401
conditions: Cody-Waite applies while k is small enough for kC1 to remain exact. Payne-Hanek becomes attractive for large arguments and can cover the whole floating-point range. Smaller reduced intervals reduce the required polynomial degree but require tables or repeated reduction.   # p.397, p.399, p.403
evidence: Sections <IP> and 10.2; Tables 10.1 and 10.2

### cordic  (role: defines)
mechanism: CORDIC is a fixed-point shift-and-add method using additions, radix-power shifts, and small tables. Volder’s original method uses radix-2 arithmetic. Walther’s generalization evaluates square roots, trigonometric functions, exponentials, and logarithms.
choices:
  mode: both   # p.396
  coordinate_set: unified   # p.396
  topology: UNKNOWN
  iterations: UNKNOWN
  scale_compensation: UNKNOWN
  angle_recoding: UNKNOWN
new_choices:
  radix: 2 | 10 — arithmetic radix of the CORDIC recurrence   # p.396
slots: none
parameters: fixed-point reduced argument; iteration count UNKNOWN   # p.396
results:
| metric | value | unit | technology / device | baseline | condition | page |
| publication year | 1959 | year | abstract | UNKNOWN | original CORDIC | p.396 |
| generalization year | 1971 | year | abstract | original CORDIC | Walther generalization | p.396 |
errors_and_checks: UNKNOWN
conditions: CORDIC is attractive for versatile special-purpose hardware. FPGA studies cited by the chapter find CORDIC better than polynomial methods for arctangent but worse for sine/cosine.   # p.396, p.397
evidence: Section <IP>

### single_poly  (role: defines)
mechanism: A polynomial approximates the reduced function on a bounded interval. L2 approximations arise by projection on an orthogonal basis. Minimax approximations minimize the maximum error and exhibit alternating extrema. Constrained approximations require representable/fixed/zero coefficients rather than rounding an unconstrained polynomial afterward.
choices:
  degree: 5   # p.407, p.413
  degree: 21 [outside domain]   # p.412
  basis: taylor   # p.407
  basis: chebyshev   # p.409
  basis: minimax_remez   # p.410
  coeff_encoding: plain   # p.407
  coeff_encoding: per_coeff_width   # p.412, p.413
  guard_bits: UNKNOWN
new_choices:
  objective_norm: L2 | Linfinity | relative_minimax — optimized approximation error measure   # p.407, p.411
  coefficient_constraints: representable | fixed_taylor | forced_zero | multiword — restrictions imposed during approximation generation   # p.412
slots:
  range_reducer: range_reduction   # p.394
  evaluator: horner   # p.414
  evaluator: estrin   # p.415
parameters: degree 4, 5, or 21 examples; binary32/binary64 coefficients; double-word coefficients when required   # p.407, p.412, p.413
results:
| metric | value | unit | technology / device | baseline | condition | page |
| minimax degree | 19 | degree | abstract | UNKNOWN | arctan on [0,10], error < 10^-5 | p.403 |
| minimax degree | 1 | degree | abstract | UNKNOWN | arctan/exp/ln(1+x) on [0,0.01], error < 10^-5 | p.403 |
| constrained degree-21 error | around 8 × 10^-37 | absolute error | abstract | rounded Remez | arcsin reduction | p.412 |
| rounded degree-21 Remez error | around 8 × 10^-32 | absolute error | abstract | constrained approximation | arcsin reduction | p.412 |
| degree-5 relative error upper bound | 3.6893478416416410981673936895704588881070517625342e-15 | relative error | abstract | UNKNOWN | exp on [0,1/32], binary32 coefficients | p.413 |
| degree-4 relative error upper bound | 1.8740107698479070733041648772262498873278743779056e-16 | relative error | abstract | UNKNOWN | cos on [-0.0122719,0.0122719] | p.414 |
errors_and_checks: Sollya supplies certified supremum-norm bounds rather than estimates. Total error combines approximation error with floating-point evaluation error.   # p.413, p.415
conditions: Minimax approximation is better than the same-degree Taylor example. Constraints must be included during synthesis because rounding an unconstrained minimax polynomial can increase error substantially.   # p.407, p.412
evidence: Sections 10.3 and 10.4; Figures 10.1–10.4; Table 10.2

### lut_plus_poly  (role: instantiates)
mechanism: A table-assisted reduction uses high argument bits to select reciprocal and reconstruction constants. A small polynomial evaluates the residual function, after which table values and scale factors reconstruct the result.
choices:
  degree: UNKNOWN
  index_bits: 6 to 8   # p.406
  basis: UNKNOWN
  coeff_encoding: UNKNOWN
  guard_bits: UNKNOWN
  breakpoint_placement: uniform   # p.406
  multiplier_shape: UNKNOWN
new_choices:
  table_count: 1 | 2 — number of indexed reconstruction tables   # p.404, p.406
slots:
  range_reducer: range_reduction [method=table_augmented]   # p.404, p.406
  evaluator: horner   # p.449
  segmenter: uniform_high_bit_decode   # p.406
parameters: exponential example uses ℓ = 12 and w1 = w2 = 6; logarithm example uses 64 to 256 entries   # p.404, p.406
results:
| metric | value | unit | technology / device | baseline | condition | page |
| reduced exponential argument | \|y\| ≤ ln(2)/2^ℓ < 2^-ℓ | absolute magnitude | abstract | first reduction | two-table reduction | p.405 |
| logarithm residual magnitude | roughly \|z\| < 2^-ℓ | absolute magnitude | abstract | first reduction | reciprocal table | p.406 |
errors_and_checks: The logarithm residual product can be exact if a slightly wider format or a two-word result is used.   # p.406
conditions: Table-assisted reduction trades table storage for a smaller argument and a lower polynomial degree.   # p.403, p.406
evidence: Sections <IP> and <IP>

### horner  (role: compares)
mechanism: Horner’s rule evaluates a polynomial through nested multiply-add stages, minimizing operation count and exposing a serial dependency chain.
choices: none
new_choices: none
slots: none
parameters: degree n   # p.414
results:
| metric | value | unit | technology / device | baseline | condition | page |
| naive evaluation cost | n(n + 3)/2 | floating-point operations | abstract | Horner/Estrin | degree n | p.414 |
| naive multiplication count | n(n + 1)/2 | multiplications | abstract | Horner/Estrin | degree n | p.414 |
conditions: Horner generally favors throughput. Target FMA availability/pipeline depth and error analysis determine the final choice.   # p.415
evidence: Sections 10.4.1, <IP>

### estrin  (role: compares)
mechanism: Estrin’s method splits a polynomial into lower and upper halves and evaluates the resulting subexpressions with a binary tree.
choices: none
new_choices: none
slots: none
parameters: h = (n + 1)/2, assumed to be a power of 2   # p.415
results:
| metric | value | unit | technology / device | baseline | condition | page |
| evaluation depth | binary tree | structure | abstract | Horner | degree n | p.415 |
conditions: Estrin generally favors latency. Target FMA availability/pipeline depth and error analysis determine the final choice.   # p.415
evidence: Sections 10.4.1 and 10.4.2

### correct_rounding_strategy  (role: defines)
mechanism: A confidence interval surrounds an approximate result. A Ziv step returns only when the interval excludes every rounding breakpoint; otherwise, evaluation repeats at higher accuracy. Known hardest-to-round points allow a fast first step and a statically bounded accurate second step.
choices:
  strategy: ziv_two_phase_retry   # p.416, p.446
  strategy: single_pass_worst_case_precision   # p.447
  worst_case_knowledge: published_exhaustive   # p.422, p.437
  worst_case_knowledge: filtered_search   # p.423, p.445
  worst_case_knowledge: conservative_unknown   # p.445
  rounding_modes_covered: all_ieee_modes   # p.437
new_choices:
  hardness_search: exhaustive | L_algorithm | SLZ_polynomial — method used to determine hardest-to-round inputs or bounds   # p.422, p.423
slots: none
parameters: binary32 exhaustive search; binary64 L/SLZ search; binary128/decimal128 currently out of reach; two Ziv steps in CRlibm   # p.422, p.423, p.445, p.446
results:
| metric | value | unit | technology / device | baseline | condition | page |
| correct-rounding error bound | 0.5 | ulp | abstract | looser profiles | ideal result | p.394 |
| permissive profile error bound | up to 8192 | ulp | abstract | correct rounding | OpenCL SPIR-V profile | p.394 |
| tighter profile error bound | 2 to 4 | ulp | abstract | correct rounding | OpenCL SPIR-V profiles | p.394 |
| binary64 exp required distance | 2^-113 | significand distance | abstract | UNKNOWN | \|x\| ≥ 2^-30 | p.437 |
| binary64 exp required distance | 2^-158 | significand distance | abstract | UNKNOWN | 2^-54 ≤ \|x\| < 2^-30 | p.437 |
| binary64 ln required distance | 2^-118 | significand distance | abstract | UNKNOWN | all four rounding modes | p.437 |
| first-step accuracy | between 2^-60 and 2^-80 | error | abstract | accurate step | CRlibm | p.446 |
| second-step accuracy | 2^-120 to 2^-150 | error | abstract | fast step | function-dependent | p.447 |
| CRlibm accurate-step time | T2 ≈ 10T1 | execution-time ratio | abstract | fast step | triple-binary64 | p.448 |
| integer logarithm accurate-step time | T2 ≈ 2T1 | execution-time ratio | abstract | fast step | 64/128-bit integer implementation | p.448 |
errors_and_checks: The rounding test returns a value only when correct rounding is proven. Otherwise, it launches the accurate phase. Correctness requires proven error bounds for both phases and comparison with the known hardness-to-round bound.   # p.446, p.448
conditions: Exhaustive search is feasible for binary32. Binary64 search requires L/SLZ methods and substantial parallel computation. Wider binary128/decimal128 formats lack practical tight searches with current techniques.   # p.422, p.423, p.445
evidence: Sections 10.5 and 10.6; Tables 10.3–10.24; Theorems 10.2–10.4

## taxonomy
* Elementary-function evaluation   # p.393
  * Polynomial approximation -> single_poly   # p.397
  * Rational approximation -> unmapped   # p.393, p.410
  * Shift-and-add methods   # p.396
    * CORDIC -> cordic   # p.396
  * Table-based methods -> unmapped   # p.393
* Evaluation pipeline   # p.394
  * Special-case filtering -> unmapped   # p.394
  * Range reduction -> range_reduction   # p.394
    * Additive reduction -> range_reduction   # p.395
      * Cody-Waite split constant -> range_reduction   # p.397
      * Payne-Hanek moving bit window -> range_reduction   # p.399
      * Multistage/table-assisted reduction -> range_reduction   # p.403
    * Multiplicative reduction -> range_reduction   # p.395
  * Local approximation -> single_poly | lut_plus_poly | cordic   # p.396, p.397
  * Reconstruction -> lut_plus_poly   # p.404, p.406
* Polynomial approximation   # p.407
  * L2 projection/orthogonal basis -> single_poly   # p.408
  * Linfinity minimax/Remez -> single_poly   # p.410
  * Constrained coefficients -> single_poly   # p.412
* Polynomial evaluation   # p.414
  * Horner rule -> horner   # p.414
  * Estrin tree -> estrin   # p.415
  * Dorn/generalized schemes -> unmapped   # p.415
* Correct rounding   # p.415
  * Small-argument analytic replacement -> correct_rounding_strategy   # p.418
  * Ziv multilevel strategy -> correct_rounding_strategy   # p.416
  * Exhaustive hardest-point search -> correct_rounding_strategy   # p.422
  * L-algorithm piecewise-linear search -> correct_rounding_strategy   # p.423
  * SLZ piecewise-polynomial search -> correct_rounding_strategy   # p.423, p.445

## primary_sources
* Volder, 1959 — original CORDIC algorithm   # p.396
* Walther, 1971 — generalized CORDIC across elementary functions   # p.396
* Cody and Waite, year UNKNOWN — split-constant range reduction   # p.397
* Boldo, Daumas, and Li, year UNKNOWN — FMA-based Cody-Waite generalization   # p.399
* Payne and Hanek, year UNKNOWN — large-argument trigonometric range reduction   # p.399
* Kahan, year UNKNOWN — continued-fraction method for worst-case range reduction and the term Table Maker’s Dilemma   # p.394, p.401
* Tang, year UNKNOWN — table-based multistage elementary-function methods   # p.401
* Wong and Goto, year UNKNOWN — table-assisted logarithm reduction   # p.405
* Remez, year UNKNOWN — iterative minimax approximation algorithm   # p.410
* Brisebarre, Chevillard, and Hanrot, year UNKNOWN — constrained polynomial approximation algorithms   # p.412
* Ziv, year UNKNOWN — multilevel retry strategy for correct rounding   # p.416
* Lefèvre, year UNKNOWN — L-algorithm for hardest-to-round searches   # p.423
* Stehlé, Lefèvre, and Zimmermann, year UNKNOWN — SLZ polynomial hardest-to-round search   # p.423

## new_families
### rational_approximation  (domain: sfu, closest: single_poly, why_not: A quotient of polynomials has denominator structure and evaluation choices absent from single_poly.)
mechanism: A rational function approximates a continuous elementary function on a bounded interval. The chapter states that minimax rational approximations have an alternation result analogous to polynomial minimax approximation but does not detail their evaluation structure.
choices: numerator_degree: Int; denominator_degree: Int; objective_norm: {absolute_minimax, relative_minimax}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| detailed implementation results | UNKNOWN | UNKNOWN | abstract | single_poly | rational approximation | p.410 |
evidence: p.393, p.410

## space_gaps
* `cordic` lacks a radix choice for the radix-2 and radix-10 variants stated by the chapter.   # p.396
* `single_poly.degree` excludes the degree-21 constrained approximation used for correct rounding.   # p.412
* `range_reduction` lacks reduced-argument representation and repeated-reduction choices.   # p.403, p.406
* `correct_rounding_strategy` lacks exhaustive/L-algorithm/SLZ hardness-search choices.   # p.422, p.423
* The vocabulary lacks rational approximation as an SFU family.   # p.393, p.410

## open_questions
* The chapter does not specify CORDIC iteration counts/topology/scale compensation for a concrete implementation.
* The chapter mentions table-based methods without defining a full-value direct-LUT architecture.   # p.393
* The binary64 trigonometric hardest-to-round tables cover restricted domains rather than every full input domain.   # p.443
* The chapter does not provide practical hardness-to-round bounds for binary128 or decimal128.   # p.445
