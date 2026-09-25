---
handle: walters2005
citation: E. G. Walters, M. J. Schulte, "Efficient Function Approximation Using Truncated Multipliers and Squarers", 17th IEEE Symposium on Computer Arithmetic (ARITH-17), 2005
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fixed12, fixed16, fixed20, fixed24]
authority: incremental
pages_read: 8 / 8
---

## summary
The document presents linear and quadratic piecewise-polynomial reciprocal interpolators that use truncated multipliers and squarers. Exhaustive coefficient adjustment compensates for finite-precision/reduction errors and permits 8.3 % to 31.1 % fewer partial products while satisfying a ±1 ulp error specification. # p.1, p.7, p.8

## families
### piecewise_poly  (role: extends)
mechanism: The input is divided into 2^m uniform subintervals, with xm selecting stored coefficients and xl driving the arithmetic datapath. Linear interpolation evaluates a0+a1xl. Quadratic interpolation evaluates a0+a1xl+a2xl² with a specialized squarer/two multipliers feeding a multi-operand adder. Chebyshev coefficients are quantized, shortened, and adjusted by exhaustive bit-accurate simulation to minimize maximum absolute error and lookup-table size. # p.3–p.6
choices:
  segments: 16, 32, 64, 128 [outside domain], 1024 [outside domain]   # p.7–p.8
  degree: 1, 2   # p.4, p.7–p.8
  basis: chebyshev   # p.3
  coefficient_optimization: exhaustive_coefficient_adjustment [outside domain]   # p.5–p.6
  rounding_contract: maximum_absolute_error_below_1_ulp [outside domain]   # p.6–p.8
new_choices:
  coefficient_length_search: one_bit_trial_and_error — coefficient widths are reduced individually and restored when optimization cannot meet the error bound   # p.6
slots:
  evaluator: parallel_monomial   # p.4
  segmenter: uniform_high_bit_decode   # p.3
parameters: Linear designs use 12-/16-/20-bit inputs with (n,m)=(11,5)/(15,7)/(19,10); quadratic designs use 16-/20-/24-bit inputs with (n,m)=(15,4)/(19,6)/(23,7). Lookup tables contain 704/3072/30720 bits for linear designs and 672/2880/7040 bits for quadratic designs. # p.7–p.8
results:
| metric | value | unit | technology / device | baseline | condition | page |
| error range / variance / partial products / reduction | −0.832 to 0.757 / 0.101 / 66 / n/a | ulps / ulps / pp's / % | UNKNOWN / 2005 | n/a | 12-bit linear, Standard | p.7 |
| error range / variance / partial products / reduction | −0.832 to 0.871 / 0.105 / 51 / 22.7 % | ulps / ulps / pp's / % | UNKNOWN / 2005 | Standard | 12-bit linear, Constant | p.7 |
| error range / variance / partial products / reduction | −0.832 to 0.921 / 0.102 / 56 / 15.2 % | ulps / ulps / pp's / % | UNKNOWN / 2005 | Standard | 12-bit linear, Variable | p.7 |
| error range / variance / partial products / reduction | −0.892 to 0.964 / 0.113 / 72 / n/a | ulps / ulps / pp's / % | UNKNOWN / 2005 | n/a | 16-bit linear, Standard | p.7 |
| error range / variance / partial products / reduction | −0.961 to 0.921 / 0.114 / 62 / 13.9 % | ulps / ulps / pp's / % | UNKNOWN / 2005 | Standard | 16-bit linear, Constant | p.7 |
| error range / variance / partial products / reduction | −0.958 to 0.932 / 0.112 / 66 / 8.3 % | ulps / ulps / pp's / % | UNKNOWN / 2005 | Standard | 16-bit linear, Variable | p.7 |
| error range / variance / partial products / reduction | −0.961 to 0.978 / 0.114 / 99 / n/a | ulps / ulps / pp's / % | UNKNOWN / 2005 | n/a | 20-bit linear, Standard | p.7 |
| error range / variance / partial products / reduction | −0.996 to 0.987 / 0.114 / 89 / 10.1 % | ulps / ulps / pp's / % | UNKNOWN / 2005 | Standard | 20-bit linear, Constant | p.7 |
| error range / variance / partial products / reduction | −0.962 to 0.968 / 0.113 / 89 / 10.1 % | ulps / ulps / pp's / % | UNKNOWN / 2005 | Standard | 20-bit linear, Variable | p.7 |
| error range / variance / partial products / reduction | −0.926 to 0.993 / 0.102 / 375 / n/a | ulps / ulps / pp's / % | UNKNOWN / 2005 | n/a | 16-bit quadratic, Standard | p.8 |
| error range / variance / partial products / reduction | −0.906 to 0.993 / 0.104 / 314 / 16.8 % | ulps / ulps / pp's / % | UNKNOWN / 2005 | Standard | 16-bit quadratic, Constant | p.8 |
| error range / variance / partial products / reduction | −0.967 to 0.972 / 0.103 / 268 / 29.5 % | ulps / ulps / pp's / % | UNKNOWN / 2005 | Standard | 16-bit quadratic, Variable | p.8 |
| error range / variance / partial products / reduction | −0.869 to 0.854 / 0.098 / 419 / n/a | ulps / ulps / pp's / % | UNKNOWN / 2005 | n/a | 20-bit quadratic, Standard | p.8 |
| error range / variance / partial products / reduction | −0.945 to 0.952 / 0.100 / 292 / 31.1 % | ulps / ulps / pp's / % | UNKNOWN / 2005 | Standard | 20-bit quadratic, Constant | p.8 |
| error range / variance / partial products / reduction | −0.934 to 0.972 / 0.102 / 292 / 31.1 % | ulps / ulps / pp's / % | UNKNOWN / 2005 | Standard | 20-bit quadratic, Variable | p.8 |
| error range / variance / partial products / reduction | −0.951 to 0.967 / 0.099 / 622 / n/a | ulps / ulps / pp's / % | UNKNOWN / 2005 | n/a | 24-bit quadratic, Standard | p.8 |
| error range / variance / partial products / reduction | −0.951 to 0.967 / 0.099 / 475 / 24.1 % | ulps / ulps / pp's / % | UNKNOWN / 2005 | Standard | 24-bit quadratic, Constant | p.8 |
| error range / variance / partial products / reduction | −0.997 to 0.947 / 0.099 / 486 / 22.3 % | ulps / ulps / pp's / % | UNKNOWN / 2005 | Standard | 24-bit quadratic, Variable | p.8 |
errors_and_checks: The design target is maximum absolute error below 2^-q; evaluated reciprocal designs set q=n+1, giving a ±1 ulp specification. Exhaustive simulation covers every input and models coefficient quantization, arithmetic rounding, reduction error, and correction. # p.4–p.6
conditions: The demonstrated input is reduced to [1,2), and range reduction/reconstruction are excluded from the implementation. Precision is practically limited by exhaustive-simulation time; 24-bit coefficient optimization takes about one hour on a 2.4 GHz Pentium 4. # p.3, p.5–p.6
evidence: §3–§6; Figures 4–5; Tables 1–2, p.3–p.8

### truncated_fixed_width  (role: extends)
mechanism: Several least-significant partial-product columns are not formed. Constant correction adds the inverse midpoint of the reduction-error range, while variable correction adds the most-significant unformed column into the next column. Increasing r while decreasing k preserves output weight; exhaustive simulation finds the largest acceptable truncation. # p.1–p.2, p.6
choices:
  extra_columns_kept: 0, 1, 2, 3, 4   # p.7–p.8
  correction_scheme: constant, data_dependent   # p.2, p.7–p.8
  output_rounding: round_to_nearest   # p.4
new_choices:
  unformed_columns_r: Int[4..13:1] — number of least-significant partial-product columns not formed in reported truncated designs   # p.7–p.8
slots:
  kept_tree: csa_reduction_tree   # p.4
parameters: Reported multiplier settings span k=0 to 4 and r=4 to 11; r=0 denotes a standard multiplier. # p.6–p.8
results:
| metric | value | unit | technology / device | baseline | condition | page |
| partial-product reduction | 8.3 % to 22.7 % | % | UNKNOWN / 2005 | optimized standard interpolator | linear reciprocal interpolators | p.7 |
| partial-product reduction | 16.8 % to 31.1 % | % | UNKNOWN / 2005 | optimized standard interpolator | quadratic reciprocal interpolators | p.7–p.8 |
errors_and_checks: Multiplier reduction error is always nonpositive and ranges from −((r−1)·2^r+1)·2^(−r−k) ulps to 0 ulps. # p.1–p.2
conditions: Constant correction is often easier for tree reduction because variable correction can increase matrix height; variable correction is readily implemented in an array and may improve accuracy. # p.7
evidence: §2, §5.3, §6; Figures 1 and 3; Tables 1–2, p.1–p.2, p.6–p.8

### squarer  (role: extends)
mechanism: A specialized squarer omits least-significant partial-product columns and applies constant or variable correction. The quadratic interpolator may also truncate t least-significant xl bits before squaring. # p.2, p.4–p.5
choices:
  folding_scheme: basic_symmetry   # p.2
new_choices:
  truncation_columns: r — number of unformed squarer columns   # p.2
  correction: {constant, variable} — offset applied to the squarer reduction error   # p.2
  input_truncation_bits: t — least-significant xl bits removed before squaring   # p.5
slots:
  reduction: csa_reduction_tree   # p.4
parameters: Reported quadratic designs use tsq=0/0/1 and truncated-squarer r values from 7 to 13. # p.8
results:
| metric | value | unit | technology / device | baseline | condition | page |
| reduction-error range | −1.000 to 0 | ulps | UNKNOWN / 2005 | full squarer | 12-bit squarer, k=2, r=10 | p.2 |
errors_and_checks: The squarer reduction-error lower bound differs for even and odd r because all unformed partial-product bits cannot simultaneously equal one. # p.2
conditions: Input truncation is allowed only when its propagated error remains within the allocated error budget; t≤0 prohibits truncation. # p.5
evidence: §2, §4.3; Figures 2–3; Table 2, p.2, p.4–p.5, p.8

## new_families
none

## space_gaps
* `piecewise_poly.segments` excludes the demonstrated 128- and 1024-subinterval designs. # p.7–p.8
* `piecewise_poly.coefficient_optimization` lacks exhaustive discrete coefficient adjustment and iterative coefficient-width reduction. # p.5–p.6
* `squarer` lacks truncation/correction/input-truncation choices needed for the reported architecture. # p.2, p.5
* `truncated_fixed_width` lacks an explicit `unformed_columns_r` choice distinct from formed-but-discarded columns k. # p.1–p.2

## open_questions
* The paper estimates area savings through partial-product counts rather than reporting synthesized area/delay/power or a technology node. # p.7
