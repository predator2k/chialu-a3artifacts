---
handle: decaro_2017
citation: D. De Caro, E. Napoli, D. Esposito, G. Castellano, N. Petra, A. G. M. Strollo, "Minimizing Coefficients Wordlength for Piecewise-Polynomial Hardware Function Evaluation With Exact or Faithful Rounding", IEEE Transactions on Circuits and Systems I, vol. 64, no. 5, pp. 1187-1200, 2017
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fixed_point]
authority: incremental
pages_read: 1-14 / 14
---

## summary
The paper proposes an ILP-based method that jointly selects quantized coefficients and arithmetic simplifications for exactly or faithfully rounded piecewise-linear/quadratic function evaluators. The method supports truncated multiplier matrices and approximate squarers while accounting for their errors in the coefficient constraints. Synthesis results cover STM 28 nm and UMC 90 nm CMOS implementations. 

## families
### piecewise_poly  (role: extends)
mechanism: The input interval is divided into T equal-length segments addressed by the s most-significant input bits, with T = 2^s. Each segment evaluates either w = n_j + m_j(x-a_j) or w = n_j + m_j(x-a_j) + p_j(x-a_j)^2. An integer linear program selects quantized coefficients while accounting simultaneously for polynomial approximation, coefficient quantization, arithmetic approximation, and output-rounding errors. Separate linear constraints enforce exact or faithful rounding. Quadratic coefficient minimization uses a two-pass optimization that first fixes one coefficient wordlength and then minimizes the other. # pp.1-7
choices:
  degree: 1 or 2   # pp.1,5
  basis: shifted_monomial [outside domain]   # pp.1,5-6
  coeff_encoding: per_coeff_width   # pp.3,6-7
  coefficient_optimization: joint_wordlength_search   # pp.2-7
  rounding_contract: exact or faithful   # pp.2,4-7
new_choices:
  constraint_formulation: integer_linear_programming — Linear constraints combine every error source and minimize coefficient wordlength.   # pp.2-7
  partial_product_matrix: full or truncated — Low-weight multiplier partial products may be omitted and compensated through the optimized constant coefficient.   # pp.4-5
  squarer_output: exact or rounded or truncated — The quadratic method accepts any known squarer input-output function q(z).   # p.6
  coefficient_priority: linear_then_quadratic or quadratic_then_linear — The two-pass method gives one coefficient type priority before optimizing the other.   # p.7
slots:
  evaluator: parallel_monomial   # pp.1,5-6
  segmenter: uniform_high_bit_decode   # p.1
  range_reducer: UNKNOWN   # p.1
parameters: T = 2^s equal-length segments; degree 1 or 2; input width up to 24 bits; functions include sine, cosine, exponential, logarithm, reciprocal, and square root; optional pipeline after LUTs and squarer; latency/II UNKNOWN.   # pp.1,10-13
results:
| metric | value | unit | technology / device | baseline | condition | page |
| total LUT size | 111 | Kbit | UNKNOWN (2017) | 156 K in [15] | Exactly rounded reciprocal, square root, 2^x, and log2(x); 15-bit input; ulp = 2^-15; linear interpolation | p.8 |
| multiplier size | 13 × 6 | bits | UNKNOWN (2017) | 15 × 5 in [15] | Same four-function exactly rounded linear interpolator | p.8 |
| segment count | 512 for square root; 1024 for each other function | segments | UNKNOWN (2017) | 1024 for all four functions in [15] | Exactly rounded linear interpolation | p.8 |
| segment count | 32 for square root; 64 for each other function | segments | UNKNOWN (2017) | 256 for every function in [15] | Exactly rounded quadratic interpolation with rounded squarer, tout = 5 | pp.9-10 |
| minimum area | about 3400 | μm2 | STM 28 nm, 1.0 V (2017) | none | 18-bit exactly rounded quadratic log2(1+x), no pipeline, delay 3.0 ns | p.11 |
| minimum delay | 1.285 | ns | STM 28 nm, 1.0 V (2017) | none | Same design, area larger than 7300 μm2 | p.11 |
| operating frequency | more than 900 | MHz | STM 28 nm, 1.0 V (2017) | about 650 MHz without pipeline | Exactly rounded quadratic interpolator, ulp = 2^-20, pipeline after LUTs and squarer | p.11 |
| normalized dynamic power | 9.6 | μW/MHz | STM 28 nm, 1.0 V (2017) | 14 μW/MHz without pipeline | Exactly rounded quadratic interpolator, ulp = 2^-20 | p.11 |
| area change | 11% lower | relative area | STM 28 nm, 1.0 V (2017) | exactly rounded linear interpolator | Exactly rounded quadratic interpolator, ulp = 2^-14 | p.11 |
| power change | 23% higher | relative power | STM 28 nm, 1.0 V (2017) | exactly rounded linear interpolator | Exactly rounded quadratic interpolator, ulp = 2^-14 | p.11 |
| exact-rounding area overhead | eight-fold increase | relative area | STM 28 nm, 1.0 V (2017) | faithfully rounded linear interpolator | Linear interpolation, ulp = 2^-18 | p.11 |
| minimum delay | about 1.35 | ns | STM 28 nm, 1.0 V (2017) | about 1.45 ns with rounded squarer | 20-bit faithfully rounded quadratic log2(1+x), truncated squarer, no pipeline | p.12 |
| solver CPU time | less than one minute | time | quad-core i7, 16 GB, Gurobi 6.5 (2017) | none | Worst case among Table I exactly rounded linear approximations | p.8 |
errors_and_checks: Faithful rounding requires the result to be within 1 ulp, with either adjacent representable value accepted; exact rounding requires the result to equal the rounded exact function value and uses a 0.5 ulp accuracy bound. The ILP includes e∞, e_Qcoeff, e_Qarith, and e_round simultaneously. No fault-detection mechanism is reported.   # pp.2-3
conditions: The solver reports an unfeasible problem when T is too small or Nmin is too large; increasing T or reducing Nmin can restore feasibility. # p.5 The exactly rounded linear design is probably ineffective at ulp = 2^-18 or 2^-20 because its LUT is large. # p.8 Partial-product truncation helps low-precision linear interpolators but degrades the ulp = 2^-20 case because the larger LUT dominates. # p.12 Partial-product truncation is more effective for quadratic interpolators because their partial-product matrices are larger and their LUTs are smaller. # p.12 The pipelined quadratic design is faster and uses less power than the linear design above ulp precision 2^-14. # pp.11-12 The ILP method becomes impractical above 24 input bits or for higher-degree polynomials because the unknown/constraint count grows. # p.13
evidence: Sections II-IV; Fig. 1; Algorithms 1-3; Tables I-XIV; Figs. 3-4, pp.1-13.

## new_families
none

## space_gaps
* piecewise_poly lacks a value for the shifted-monomial basis n_j + m_j(x-a_j) + p_j(x-a_j)^2 used by the implemented evaluators. # pp.1,5-6
* piecewise_poly lacks choices for full/truncated partial-product matrices and exact/rounded/truncated squarers. # pp.4,6,9-12
* piecewise_poly lacks an explicit ILP constraint-formulation choice for joint coefficient quantization/arithmetic optimization. # pp.2-7
* piecewise_poly lacks a slot for the specialized squarer used by quadratic evaluators. # pp.1,5-6

## open_questions
* The printed values inside Tables I-XIV are not recoverable from the supplied text extraction for most rows, so only values repeated in surrounding prose are recorded.
* The paper does not identify a vocabulary family for the MADD implementation or state its internal final-adder topology.
* The paper does not specify latency or initiation interval for the combinational and optionally pipelined implementations.
