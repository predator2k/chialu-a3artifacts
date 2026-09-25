---
handle: brisebarre_2006
citation: N. Brisebarre, J.-M. Muller, A. Tisserand, "Computing Machine-Efficient Polynomial Approximations", ACM Transactions on Mathematical Software, vol. 32, no. 2, pp. 236-256, 2006
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fixed_point, fp32, fp64]
authority: landmark
pages_read: 21 / 21
---

## summary
The document finds minimax polynomial approximations whose degree-i coefficient is constrained to a multiple of 2^-mi, which reduces hardware multiplier sizes or permits exact finite-precision coefficients. A rational-polytope search jointly selects the coefficients and supports absolute/relative error, fixed coefficients, and odd/even polynomials. # p.238–247

## families
### single_poly  (role: extends)
mechanism: The method starts from a degree-n minimax polynomial and constructs a bounded rational polytope containing the integer numerators of all coefficient-constrained candidates within error bound K. Inequalities sampled at d+1 rational points capture dependencies among coefficients. Integer points are enumerated, and the supremum norm of each candidate is computed to select the best truncated approximation. A Chebyshev-bound method supplies a simpler but usually larger candidate set for intervals [0,a] or [-a,a]. # p.243–248
choices:
  basis: minimax_remez   # p.237–238
  coeff_encoding: per_coeff_width   # p.238, p.243
new_choices:
  coefficient_optimization: lattice_constrained_minimax_polytope_search — jointly searches coefficients restricted to multiples of 2^-mi # p.243–247
  error_objective: absolute_or_relative_supremum — minimizes absolute or relative worst-case approximation error # p.237, p.247
  coefficient_constraints: fixed_values_or_parity — permits predefined coefficients and odd/even polynomial restrictions # p.239, p.247
slots:
  none
parameters: degree n; per-coefficient fractional widths [m0,...,mn]; compact interval [a,b]; bound K; d+1 rational sample points with d>=n; examples use degree 2–4 and d=4, 15, or 20 # p.243–248
results:
| metric | value | unit | technology / device | baseline | condition | page |
| candidate count | 330 | candidates | 2.53GHz Pentium 4; year UNKNOWN | none | E1, Chebyshev | p.248 |
| candidate count | 1 | candidates | 2.53GHz Pentium 4; year UNKNOWN | 330 Chebyshev candidates | E1, polytope d=4 | p.248 |
| candidate generation T1 | 0.62 | seconds | 2.53GHz Pentium 4; year UNKNOWN | none | E1 | p.248 |
| norm computation T2 | 0.26 | seconds | 2.53GHz Pentium 4; year UNKNOWN | none | E1 | p.248 |
| accuracy gain | ≈1.5 | bits | 2.53GHz Pentium 4; year UNKNOWN | rounded minimax coefficients | E1 | p.248 |
| candidate count | 84357 | candidates | 2.53GHz Pentium 4; year UNKNOWN | none | E2, Chebyshev | p.248 |
| candidate count | 9 | candidates | 2.53GHz Pentium 4; year UNKNOWN | 84357 Chebyshev candidates | E2, polytope d=20 | p.248 |
| candidate generation T1 | 0.51 | seconds | 2.53GHz Pentium 4; year UNKNOWN | none | E2 | p.248 |
| norm computation T2 | 2.18 | seconds | 2.53GHz Pentium 4; year UNKNOWN | none | E2 | p.248 |
| accuracy gain | ≈0.375 | bits | 2.53GHz Pentium 4; year UNKNOWN | rounded minimax coefficients | E2 | p.248 |
| candidate count | 9346920 | candidates | 2.53GHz Pentium 4; year UNKNOWN | none | E3, Chebyshev | p.248 |
| candidate count | 15 | candidates | 2.53GHz Pentium 4; year UNKNOWN | 9346920 Chebyshev candidates | E3, polytope d=20 | p.248 |
| candidate generation T1 | 0.99 | seconds | 2.53GHz Pentium 4; year UNKNOWN | none | E3 | p.248 |
| norm computation T2 | 1.77 | seconds | 2.53GHz Pentium 4; year UNKNOWN | none | E3 | p.248 |
| accuracy gain | ≈0.22 | bits | 2.53GHz Pentium 4; year UNKNOWN | rounded minimax coefficients | E3 | p.248 |
| candidate count | 192346275 | candidates | 2.53GHz Pentium 4; year UNKNOWN | none | E4, Chebyshev | p.248 |
| candidate count | 1 | candidates | 2.53GHz Pentium 4; year UNKNOWN | 192346275 Chebyshev candidates | E4, polytope d=20 | p.248 |
| candidate generation T1 | 0.15 | seconds | 2.53GHz Pentium 4; year UNKNOWN | none | E4 | p.248 |
| norm computation T2 | 0.55 | seconds | 2.53GHz Pentium 4; year UNKNOWN | none | E4 | p.248 |
| accuracy gain | ≈0.08 | bits | 2.53GHz Pentium 4; year UNKNOWN | rounded minimax coefficients | E4 | p.248 |
| candidate count | 1 | candidates | 2.53GHz Pentium 4; year UNKNOWN | none | E5, Chebyshev | p.248 |
| candidate count | 0 | candidates | 2.53GHz Pentium 4; year UNKNOWN | 1 Chebyshev candidate | E5, polytope d=4 | p.248 |
| candidate generation T1 | 0.05 | seconds | 2.53GHz Pentium 4; year UNKNOWN | none | E5 | p.248 |
| norm computation T2 | 0 | seconds | 2.53GHz Pentium 4; year UNKNOWN | none | E5 | p.248 |
| accuracy gain | 0 | bits | 2.53GHz Pentium 4; year UNKNOWN | rounded minimax coefficients | E5 | p.248 |
| candidate count | 4 | candidates | 2.53GHz Pentium 4; year UNKNOWN | none | E6, Chebyshev | p.248 |
| candidate count | 1 | candidates | 2.53GHz Pentium 4; year UNKNOWN | 4 Chebyshev candidates | E6, polytope d=4 | p.248 |
| candidate generation T1 | 0.03 | seconds | 2.53GHz Pentium 4; year UNKNOWN | none | E6 | p.248 |
| norm computation T2 | 0.10 | seconds | 2.53GHz Pentium 4; year UNKNOWN | none | E6 | p.248 |
| accuracy gain | ≈0.41 | bits | 2.53GHz Pentium 4; year UNKNOWN | rounded minimax coefficients | E6 | p.248 |
| candidate count | 38016 | candidates | 2.53GHz Pentium 4; year UNKNOWN | none | E7, Chebyshev | p.248 |
| candidate count | 2 | candidates | 2.53GHz Pentium 4; year UNKNOWN | 38016 Chebyshev candidates | E7, polytope d=15 | p.248 |
| candidate generation T1 | 0.13 | seconds | 2.53GHz Pentium 4; year UNKNOWN | none | E7 | p.248 |
| norm computation T2 | 0.69 | seconds | 2.53GHz Pentium 4; year UNKNOWN | none | E7 | p.248 |
| accuracy gain | ≈0.06 | bits | 2.53GHz Pentium 4; year UNKNOWN | rounded minimax coefficients | E7 | p.248 |
| candidate count | 12 | candidates | 2.53GHz Pentium 4; year UNKNOWN | UNKNOWN | E8, polytope d=20 | p.248 |
| candidate generation T1 | 0.59 | seconds | 2.53GHz Pentium 4; year UNKNOWN | none | E8 | p.248 |
| norm computation T2 | 5.16 | seconds | 2.53GHz Pentium 4; year UNKNOWN | none | E8 | p.248 |
| accuracy gain | ≈0.26 | bits | 2.53GHz Pentium 4; year UNKNOWN | rounded minimax coefficients | E8 | p.248 |
| approximation error | 0.0002441406250 | absolute supremum error | 2.53GHz Pentium 4; year UNKNOWN | 0.0006939707 for rounded minimax coefficients | cos on [0,π/4], p*=(4095,6,-34,1) | p.254–255 |
| candidate count | 7 | polynomials | 2.53GHz Pentium 4; year UNKNOWN | none | E1, d=9, K=7.00 10^-4 | p.255 |
| candidate count | 4 | polynomials | 2.53GHz Pentium 4; year UNKNOWN | none | E1, d=9, K=5.00 10^-4 | p.255 |
| candidate count | 1 | polynomial | 2.53GHz Pentium 4; year UNKNOWN | none | E1, d=9, K=2.50 10^-4 | p.255 |
| candidate count | 6 | polynomials | 2.53GHz Pentium 4; year UNKNOWN | none | E1, d=9, K=6.93 10^-4 | p.255 |
| candidate count | 6 | polynomials | 2.53GHz Pentium 4; year UNKNOWN | none | E1, d=18, K=6.93 10^-4 | p.255 |
| candidate count | 6 | polynomials | 2.53GHz Pentium 4; year UNKNOWN | none | E1, d=36, K=6.93 10^-4 | p.255 |
| candidate count | 6 | polynomials | 2.53GHz Pentium 4; year UNKNOWN | none | E1, d=72, K=6.93 10^-4 | p.255 |
errors_and_checks: The selected polynomial minimizes the absolute supremum error over the coefficient lattice subject to bound K; the method also supports relative supremum error. Evaluation roundoff is excluded, and the authors provide no proof that minimizing approximation error also minimizes total approximation-plus-roundoff error. Maple infnorm supplies the reported norms without certified bounds. # p.239–240, p.247–248
conditions: The hardware-oriented target uses low-degree polynomials with small mi values to reduce multiplier delay/area at about 24-bit precision; the software target uses single/double precision with table-driven range reduction. The sampled system is bounded only when d>=n for unrestricted degree-n polynomials. Increasing d does not necessarily reduce the candidate set unless the new d is a positive integer multiple of the previous value. # p.238, p.246–247
evidence: Sections 1, 3.1, 3.2, and 4; Tables II–IV; Figure 3; Appendix 3, p.237–255

## new_families
none

## space_gaps
* single_poly lacks a coefficient_optimization choice for joint lattice-constrained minimax/polytope search. # p.243–248
* single_poly lacks an error_objective choice distinguishing absolute and relative supremum error. # p.237, p.247
* single_poly lacks choices for fixed coefficients and odd/even symmetry constraints. # p.239, p.247

## open_questions
* The document leaves total approximation-plus-evaluation-roundoff optimization unresolved because the result depends on the evaluation algorithm, architecture, and internal precision. # p.239–240
* The document does not provide certified supremum-norm bounds for the reported examples. # p.239, p.248
