---
handle: muller_2016#s04
parent: muller_2016
citation: J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
chapter: Polynomial or Rational Approximations
pdf_pages: 42-81
status: ok
kind: book_chapter
unit_classes: [VEC_SFU]
formats: [real, radix-2 signed-digit, IEEE-754 single-precision, IEEE-754 double-precision, double-extended precision]
authority: textbook
pages_read: 40 / 40
---

## summary
The chapter defines least-squares/minimax polynomial approximations, minimax rational approximations, and constrained-coefficient construction. It compares Horner/Estrin/FMA evaluation, coefficient adaptation, and the radix-2 E-method. It also derives interval bounds for finite-precision Horner evaluation with separate multiply/add operations or fused multiply-add instructions.

## families
### single_poly  (role: defines)
mechanism: A continuous function on a closed interval is approximated by one polynomial. Least-squares construction expands the function in orthogonal polynomials, while minimax construction minimizes maximum weighted absolute error and satisfies an alternating-extrema condition. Remez’s algorithm iteratively solves for an equioscillating polynomial and replaces its reference points with the current error extrema.   # p.42-p.60
choices:
  degree: 1-54 [outside domain]   # p.51-p.52, p.55, p.61-p.63, p.65-p.68
  basis: taylor, chebyshev, minimax_remez   # p.44-p.55
  coeff_encoding: plain, per_coeff_width   # p.67-p.69
  guard_bits: UNKNOWN   # p.42
new_choices:
  error_objective: {least_squares, minimax_absolute, minimax_relative} — selects average, worst-case absolute, or weighted relative error   # p.43, p.47, p.66-p.67
  orthogonal_basis: {legendre, chebyshev, jacobi, laguerre} — selects the orthogonal sequence and weight function   # p.44-p.46
  coefficient_constraint: {unconstrained_real, machine_number, multiple_of_2^-mi} — restricts representable coefficients   # p.67-p.69
slots:
  evaluator: horner   # p.70
  evaluator: estrin   # p.73-p.74
  evaluator: fma_based   # p.70, p.79-p.81
parameters: interval [a,b]; degree n; weight w(x); approximation/evaluation precision   # p.42-p.43
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum absolute error | Taylor 0.218; Legendre 0.081; Chebyshev 0.050; minimax 0.045 | absolute error | abstract | four approximation methods | degree-2 approximation to exp(x), [-1,1] | p.52 |
| maximum absolute error | minimax 0.5 × 10−17; Taylor 0.7 × 10−11 | absolute error | abstract | Taylor | degree-11 approximation to sin(x), [0,π/4] | p.52 |
| maximum absolute error | Legendre 0.1875; Chebyshev 0.2122; minimax 0.125 | absolute error | abstract | three approximation methods | degree-2 approximation to \|x\|, [-1,1] | p.54 |
| minimax advantage over Chebyshev | at most one bit | bit | abstract | Chebyshev | elementary functions | p.53 |
| significant bits by degree 2-9 | sin: 7.8,12.7,16.1,21.6,25.5,31.3,35.7,41.9; exp: 6.8,10.8,15.1,19.8,24.6,29.6,34.7,40.1 | −log2(absolute error) | abstract | degree | [0,1] | p.55 |
| significant bits by degree 2-9 | ln(1+x): 8.2,11.1,14.0,16.8,19.6,22.3,25.0,27.7; (x+1)^x: 6.3,8.5,11.9,14.4,18.1,20.0,22.7,25.1 | −log2(absolute error) | abstract | degree | [0,1] | p.55 |
| significant bits by degree 2-9 | arctan: 8.7,9.8,13.2,15.5,17.2,21.2,22.3,24.5; tan: 4.8,6.9,8.9,10.9,12.9,14.9,16.9,19.0 | −log2(absolute error) | abstract | degree | [0,1] | p.55 |
| significant bits by degree 2-9 | sqrt: 3.9,4.4,4.8,5.2,5.4,5.6,5.8,6.0; arcsin: 3.4,4.0,4.4,4.7,4.9,5.1,5.3,5.5 | −log2(absolute error) | abstract | degree | [0,1] | p.55 |
| convergence speed | quadratic | convergence order | abstract | none | Remez’s algorithm | p.56 |
| approximation error | 5.4 × 10−4 | absolute error | Maple / UNKNOWN | none | degree-3 minimax exp(x), [0,1] | p.66 |
| approximation error | less than 2 × 10−11 | relative error | abstract | none | constrained degree-7 sin(x), [0,π/8] | p.67 |
| approximation error | roughly 10−10 | absolute error | IEEE-754 single-precision / UNKNOWN | none | constrained degree-3 2^x, [0,1/32] | p.68 |
errors_and_checks: Final error combines approximation error and finite-precision evaluation error; the chapter treats both as separately bounded quantities.   # p.42, p.74-p.81
conditions: Taylor expansions are local and usually poor for interval-wide approximation, except when arbitrary precision prevents precomputed approximants.   # p.51-p.52
evidence: Sections 3.1-3.5 and 3.7; Tables 3.1-3.3; Figures 3.2-3.7   # p.43-p.60, p.65-p.69

### horner  (role: defines)
mechanism: Horner’s scheme evaluates a degree-n polynomial as a nested sequence of multiply-add steps. Conventional execution rounds the multiplication and addition separately; interval recurrences bound every intermediate result and propagate local rounding errors to a final error bound.   # p.70, p.74-p.79
choices:
  none
new_choices:
  arithmetic_step: {separate_multiply_add, fused_multiply_add} — determines whether each nested step rounds once or twice   # p.75, p.79
slots:
  none
parameters: degree n; interval [xmin,xmax]; round-to-nearest; exactly representable coefficients   # p.74-p.76
results:
| metric | value | unit | technology / device | baseline | condition | page |
| evaluation-error bound | 2 × ulp(1) × n × Σ\|ai xi\| + O(ulp(1)^2) | absolute error | abstract | none | Horner evaluation | p.74 |
| evaluation-error bound | 1.128 × 10−16 = 0.508 | absolute error; ulps | IEEE-754 double-precision / UNKNOWN | sampled maximum 1.114 × 10−16 | degree-5 exp polynomial, [0,1/128] | p.78 |
| evaluation-error bound | 0.50025 | ulps | double-extended then double / UNKNOWN | double evaluation | same polynomial | p.78 |
| evaluation-error bound | 4.025 × 10−16 = 3.625 | absolute error; ulps | IEEE-754 double-precision / UNKNOWN | sampled value around 1.495 ulps | degree-4 Γ(x+1) polynomial, [0,1] | p.78 |
| refined bound | 2.93 × 10−16 = around 2.64 | absolute error; ulps | IEEE-754 double-precision / UNKNOWN | unpartitioned interval | 64 subintervals | p.79 |
errors_and_checks: Interval subdivision tightens bounds when repeated uses of the same x create dependency lost by ordinary interval arithmetic.   # p.78-p.79
conditions: Horner’s scheme is advised when coefficients lack an exploitable factorization; a shallow FMA pipeline favors Horner, while a deep pipeline can favor Estrin.   # p.70
evidence: Sections 3.8 and 3.9.1; Theorem 10   # p.70-p.79

### estrin  (role: defines)
mechanism: Estrin’s method recursively groups coefficients and evaluates independent multiply-accumulate expressions and powers of x in parallel. The degree-7 construction uses three dependency levels and can be extended to any degree.   # p.73-p.74
choices:
  none
new_choices:
  none
slots:
  none
parameters: degree 7 example; parallel or pipelined multiplication/accumulation   # p.73
results:
| metric | value | unit | technology / device | baseline | condition | page |
| dependency levels | 3 | steps | abstract | Horner | degree-7 example | p.73 |
errors_and_checks: none
conditions: Estrin becomes attractive when parallel/pipelined multiply-accumulate hardware is available or the FMA pipeline is deep.   # p.70, p.73-p.74
evidence: Section 3.8.2; Algorithm 5   # p.73-p.74

### fma_based  (role: analyzes)
mechanism: An FMA-based Horner evaluator computes each expression S[i]x+ai−1 with one final round-to-nearest operation. The error recurrence therefore adds one rounding term per coefficient rather than separate multiplication/addition terms.   # p.70, p.79-p.80
choices:
  none
new_choices:
  none
slots:
  none
parameters: degree n; interval [xmin,xmax]; round-to-nearest   # p.79-p.80
results:
| metric | value | unit | technology / device | baseline | condition | page |
| evaluation-error bound | 1.119 × 10−16 = 0.504 | absolute error; ulps | IEEE-754 double-precision FMA / UNKNOWN | separate multiply/add | degree-5 exp polynomial, [0,1/128] | p.81 |
| evaluation-error bound | 1.110770 × 10−16 ≈ 0.50027 | absolute error; ulps | double-extended FMA then double / UNKNOWN | double FMA | same polynomial | p.81 |
| evaluation-error bound | 2.498 × 10−16 = 2.25 | absolute error; ulps | IEEE-754 double-precision FMA / UNKNOWN | sampled maximum 1.567 ulps | degree-4 Γ(x+1) polynomial, [0,1] | p.81 |
| refined bound | 1.752 | ulps | IEEE-754 double-precision FMA / UNKNOWN | 2.25 ulps | 256 subintervals | p.81 |
errors_and_checks: Gappa automatically computes roundoff bounds and generates formal proofs for computations of this kind.   # p.81
conditions: FMA evaluation supplies one instruction and one rounding for ±a×x+b.   # p.70
evidence: Sections 3.9.2 and 3.10   # p.79-p.81

## taxonomy
* Function approximation   # p.42-p.43
  * Polynomial approximation
    * Least-squares approximation
      * Legendre basis -> single_poly   # p.44
      * Chebyshev basis -> single_poly   # p.44-p.45
      * Jacobi basis -> single_poly   # p.46
      * Laguerre basis -> single_poly   # p.46
    * Least-maximum/minimax approximation
      * Alternation characterization -> single_poly   # p.47
      * Remez iteration -> single_poly   # p.56-p.60
    * Taylor expansion -> single_poly   # p.51-p.52
    * Constrained-coefficient minimax approximation -> single_poly   # p.66-p.69
  * Rational approximation
    * Minimax rational approximation -> rational_function_approximation   # p.61-p.63
    * Padé approximation -> rational_function_approximation   # p.62
    * Orthogonal rational approximation -> rational_function_approximation   # p.62
* Polynomial evaluation   # p.69-p.74
  * Horner’s scheme -> horner   # p.70
  * Horner’s scheme with FMA -> fma_based   # p.70, p.79-p.81
  * Adaptation of coefficients -> coefficient_adaptation_evaluator   # p.70-p.71
  * E-method -> e_method   # p.72-p.73
  * Estrin’s method -> estrin   # p.73-p.74

## primary_sources
* Weierstrass, 1885 — existence of arbitrarily accurate polynomial approximations for continuous functions   # p.47
* Chebyshev, UNKNOWN — alternating-extrema characterization of polynomial and rational minimax approximations   # p.47, p.62
* Remez, UNKNOWN — iterative computation of minimax approximations   # p.47, p.56
* Newton, UNKNOWN — use of the nested evaluation method later attributed to Horner   # p.70
* Knuth, UNKNOWN — adaptation of coefficients for fewer multiplications   # p.70
* Ercegovac, UNKNOWN — E-method for polynomial and rational evaluation   # p.72
* Estrin, UNKNOWN — parallel polynomial evaluation algorithm   # p.73
* Cody, UNKNOWN — rearranging equivalent rational expressions to reduce roundoff error   # p.64
* Brisebarre, Muller and Tisserand, UNKNOWN — search for best coefficient-constrained approximations   # p.68-p.69
* Melquiond, UNKNOWN — Gappa roundoff-bound computation and formal proofs   # p.81

## new_families
### rational_function_approximation  (domain: sfu: elementary-function units, closest: single_poly, why_not: rational approximation requires separate numerator/denominator polynomials and division)
mechanism: A function is approximated by P(x)/Q(x). Minimax rational approximants satisfy an alternating-extrema theorem and can be constructed by a Remez variant; algebraically equivalent forms can have different finite-precision errors.   # p.61-p.65
choices: numerator_degree: Int; denominator_degree: Int; construction: {minimax_remez, pade, orthogonal}; expression_form: {direct_fraction, decomposed, factored}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| approximation error | 0.28 × 10−15 | absolute error | abstract | degree-25 polynomial: 0.13 × 10−14 | degree-5/5 rational sqrt(x), [1/4,1] | p.61 |
| approximation error | 7 × 10−9 | absolute error | abstract | degree-13 polynomial: 8 × 10−9 | degree-3/4 tan(x), [−π/4,+π/4] | p.63 |
| arithmetic operations | 8 | operations | abstract | polynomial: 14 | tan(x) approximants | p.63 |
| worst-case error | frac1 0.3110887e−14; frac2 0.1227446e−14; frac3 0.1486132e−14 | absolute error | IEEE-754 double-precision / UNKNOWN | equivalent forms | 500000 points, [0,1] | p.64 |
| average error | frac1 0.3378607e−15; frac2 0.1847124e−15; frac3 0.2050626e−15 | absolute error | IEEE-754 double-precision / UNKNOWN | equivalent forms | 500000 points, [0,1] | p.64 |
evidence: Sections 3.6-3.7   # p.61-p.69

### coefficient_adaptation_evaluator  (domain: sfu: polynomial datapaths, closest: horner, why_not: it transforms coefficients and evaluates a different nested quadratic structure)
mechanism: A polynomial is transformed once into parameters c, αi, and βi, then evaluated through y=x+c, w=y², and a nested sequence using w−αi. The transformation reduces multiplications for sufficiently high degrees but requires solving nonlinear coefficient equations.   # p.70-p.71
choices: shift_c: real; transformed_factor_count: Int
results:
| metric | value | unit | technology / device | baseline | condition | page |
| operation count | at most ceil(n/2)+2 multiplications and n additions | operations | abstract | Horner | degree-n polynomial | p.70 |
| multiplications | 6 | multiplications | abstract | Horner: 8 | degree 8 example | p.71 |
evidence: Theorem 9 and example   # p.70-p.71

### e_method  (domain: sfu: polynomial datapaths, closest: horner, why_not: it solves a linear system by signed-digit recurrence rather than nested coefficient evaluation)
mechanism: The radix-2 E-method expresses polynomial evaluation as a linear system and solves it through w(j)=2(w(j−1)−Ad(j−1)). Selection emits signed digits from exact or truncated residual estimates, and bounded residual sequences converge to the polynomial value.   # p.72-p.73
choices: digit_selection: {exact_residual, approximated_residual}; approximation: {round_to_nearest, truncation}; radix: {2}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| admissible bounds | ξ=1/2(1+Δ), 0<Δ<1, α≤1/4(1−Δ) | bound | abstract | none | correctness | p.73 |
| example domain | x≤1/8; max\|pi\|≤3/4 | bound | abstract | none | Δ=1/2 | p.73 |
evidence: Section 3.8.1, equations 3.8-3.11   # p.72-p.73

## space_gaps
* single_poly lacks least_squares and minimax_relative basis/objective choices.   # p.43, p.66-p.67
* single_poly.degree excludes reported degrees 1, 9, 11, 12, 13, 25, and 54.   # p.55, p.61-p.63, p.65-p.68
* single_poly lacks coefficient constraints for machine numbers and per-coefficient multiples of 2−mi.   # p.67-p.69
* The polynomial-datapath vocabulary lacks coefficient_adaptation_evaluator and e_method.   # p.70-p.73
* The elementary-function vocabulary lacks rational_function_approximation.   # p.61-p.65

## open_questions
* Table 3.3 contains degree columns 2 through 9, while its caption says degrees 2 through 8.   # p.55
* Table 3.5 does not print a unit for processor instruction latencies.   # p.63
* The cited-source years are absent from the supplied chapter text except for Weierstrass 1885.   # p.47-p.81
