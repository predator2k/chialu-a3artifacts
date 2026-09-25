---
handle: ercegovac_2000
citation: M. D. Ercegovac, T. Lang, J.-M. Muller, A. Tisserand, "Reciprocation, Square Root, Inverse Square Root, and Some Elementary Functions Using Small Multipliers", IEEE Transactions on Computers, vol. 49, no. 7, pp. 628-637, 2000
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fp32, fp64]
authority: incremental
pages_read: pp. 628-637 / 10 pages
---

## summary
The document proposes one argument-reduction/Taylor-series architecture for reciprocal, square root, inverse square root, logarithm, and exponential evaluation using tables, small multipliers, and at most one almost-full-length multiplication. The architecture targets approximately m-bit accuracy for m-bit significands and evaluates single-precision and double-precision operations with faithful rounding. The analytical comparison reports similar reciprocal delay and lower square-root/inverse-square-root delay than the compared Newton-Raphson, Wong-Goto, and Ito-Takagi-Yajima methods.

## families
### single_poly  (role: proposes)
mechanism: The method reduces the input to |A| < 2^-k and evaluates a Taylor series after writing A = A2 z2 + A3 z3 + A4 z4, where z = 2^-k and n = 4k. Terms no larger than 2^-4k are discarded, which leaves C0 + C1A + C2A2²z4 + 2C2A2A3z5 + C3A2³z6. Three k by k multiplications, or one k by 2k multiplication followed by one k by k multiplication, form the nonlinear terms. Function-specific shifts/additions apply the coefficients, and multiplication or addition with a table-derived M reconstructs the result. # pp.629-632,635
choices:
  degree: 3   # pp.629-630
  basis: taylor   # pp.628-630
new_choices:
  argument_decomposition: radix_2k_blocks [outside domain] — A is partitioned into k-bit A2/A3/A4 blocks so the retained polynomial terms use small multipliers.   # pp.629-631
  postprocessing: function_specific_table_factor [outside domain] — M = h(R̂) reconstructs reciprocal/square-root/inverse-square-root results; logarithm uses M + B and exponential uses a table-derived multiplicative M.   # pp.629,631-632,635
  rounding_contract: faithful [outside domain] — the evaluated single-precision and double-precision configurations target faithful rather than correctly rounded results.   # pp.629-630,632,635
slots:
  range_reducer: range_reduction [method=table_augmented, reduction_type=multiplicative, worst_case_bound_proven=true]   # pp.629,636
  evaluator: parallel_monomial   # pp.631-632
parameters: m-bit input/result significands; n-bit internal datapath with n > m; n = 4k; k = n/4; k >= 5 for the error theorem; double-precision reciprocal example k = 15; double-precision square root/inverse square root k = 14 and n = 56; three k by k multiplications or two multiplications of k by 2k and k by k; optional postprocessing multiplier of (3k + 1) by (3k + 2) bits with t = 2.   # pp.629-633
results:
| metric | value | unit | technology / device | baseline | condition | page |
| series/decomposition error upper bound | 8.31 × 2^-4k | absolute error | UNKNOWN (2000) | exact function value | reciprocal; exact decomposed A before datapath/output rounding | p.630 |
| series/decomposition error upper bound | 0.94 × 2^-4k | absolute error | UNKNOWN (2000) | exact function value | square root; exact decomposed A before datapath/output rounding | p.630 |
| series/decomposition error upper bound | 2.93 × 2^-4k | absolute error | UNKNOWN (2000) | exact function value | inverse square root; exact decomposed A before datapath/output rounding | p.630 |
| postprocessing truncation error upper bound | 0.5 × 2^-4k | absolute error | UNKNOWN (2000) | full-width M × B̂ | t = 2 and a (3k + 1) by (3k + 2)-bit multiplier | p.632 |
| critical-path delay | trb + tm3k×k + 2tmk×k + ta4k + tm3k×3k | symbolic delay | UNKNOWN (2000) | none | proposed reciprocal/square-root/inverse-square-root architecture | p.632 |
errors_and_checks: The implemented target is error below 2^-m for m-bit operands and faithful rounding. Direct rounding to nearest is not generally guaranteed. The document states that reciprocal/square-root rounding to m bits requires error below 2^-2m, inverse-square-root rounding requires error below 2^-3m, and a remainder test can settle reciprocal/division and square root but not transcendental functions.   # pp.629-630,635
conditions: The method is intended for high precision through IEEE-754 double precision. The analytical delay model reports reciprocal delay close to related methods and significantly lower delay for square root/inverse square root, while Wong-Goto uses smaller tables. The comparison assumes multiplier delays formed from radix-4 recoding, signed-digit reduction stages, and an optional final CPA, so physical delay depends on technology/implementation.   # pp.628,634-635
evidence: Sections 2-4 and 6; Theorem 1; Figs. 1-5; Tables 1-7 and 10; Appendix, pp.629-636.

### range_reduction  (role: instantiates)
mechanism: A k-bit table addressed by Y truncated through bit k returns R̂, defined as 1/Y(k) rounded down to k + 1 bits. The reduction computes A = Y × R̂ - 1 and proves -2^-k < A < 2^-k. A second function-specific table supplies M = R̂ for reciprocal, 1/sqrt(R̂) for square root, or sqrt(R̂) for inverse square root. Logarithm uses M = -ln(R̂), while exponential separates the leading input block and obtains its exponential from a k-bit table. # pp.629,631,635
choices:
  method: table_augmented   # pp.629,631,635
  reduction_type: multiplicative   # pp.629,635
  worst_case_bound_proven: true   # pp.629,636
new_choices:
  table_rounding: truncate_down [outside domain] — the reciprocal reduction-table entry R̂ is 1/Y(k) truncated to k + 1 bits.   # p.629
slots:
  none
parameters: normalized significand 1 <= Y < 2; k-bit table address; k + 1-bit R̂; reduced argument |A| < 2^-k; n = 4k; one separate M table for each implemented function.   # pp.629-631
results:
| metric | value | unit | technology / device | baseline | condition | page |
| reduced-argument bound | -2^-k < A < 2^-k | numerical interval | UNKNOWN (2000) | unreduced Y | A = Y × R̂ - 1 and 1 <= Y < 2 | p.629 |
errors_and_checks: The reduction bound follows from inequalities for Y(k), the downward-rounded R̂, and normalized Y; no runtime checker is specified.   # p.629
conditions: The reciprocal/square-root/inverse-square-root derivation assumes normalized m-bit significands with 1 <= Y < 2 and excludes exponent computation as straightforward. Logarithm omits reduction when its argument is close to 1, which avoids cancellation.   # pp.629,635
evidence: Section 2 reduction derivation and (1)-(4), Fig. 2, Sections 6.1-6.2, pp.629,631,635.

## new_families
none

## space_gaps
* `single_poly` lacks a choice for radix-2^k operand-block decomposition that turns a high-precision polynomial into two or three small-multiplier operations.   # pp.629-631
* `single_poly` lacks a postprocessing slot for function-specific table factors or additive reconstruction after argument reduction.   # pp.629,631-632,635
* `single_poly` lacks a rounding-contract choice that distinguishes faithful evaluation from correctly rounded evaluation.   # pp.629-630,635

## open_questions
* The numeric cells of Tables 1, 2, 5, 6, 8, 9, and 10 are not legible in the supplied document text, so table-only error totals, table sizes, operation counts, and comparative delay values remain UNKNOWN.
