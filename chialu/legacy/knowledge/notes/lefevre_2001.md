---
handle: lefevre_2001
citation: V. Lefevre, J.-M. Muller, "Worst Cases for Correct Rounding of the Elementary Functions in Double Precision", 15th IEEE Symposium on Computer Arithmetic (ARITH-15), pp. 111-118, 2001
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fp64]
authority: landmark
pages_read: 111-118 / 8
---

## summary
The paper reports an exhaustive search for double-precision elementary-function results closest to rounding breakpoints. The resulting bounds specify sufficient approximation precision for correct rounding in all four IEEE-754 rounding modes, over the full input range for exponential/logarithmic functions and bounded intervals for trigonometric functions.

## families
### correct_rounding_strategy  (role: extends)
mechanism: The strategy computes in advance the minimum nonzero mantissa distance between an elementary-function result and a rounding breakpoint, which permits one fixed approximation precision rather than an unpredictable precision retry. A filter approximates the function by polynomials over subdomains and uses a Euclidean-algorithm variant to discard inputs that cannot approach a breakpoint. Accurate evaluation resolves the remaining candidates. Searching test numbers through either f or f^-1 reduces the search space. # pp.112-114
choices:
  strategy: single_pass_worst_case_precision   # p.112
  worst_case_knowledge: published_exhaustive   # pp.114-118
  rounding_modes_covered: all_ieee_modes   # pp.114-116
new_choices:
  worst_case_search_method: polynomial_filter_plus_euclidean_grid_search — identifies inputs whose function values approach rounding breakpoints   # pp.112-114
slots:
  none
parameters: double precision; 53-bit mantissas; test numbers have 54-bit mantissas; the initial filter generally tests 32 following bits and retains about one argument out of 2^32; first-level intervals contain 2^40 test numbers; polynomial degrees are generally 4 to 20; the search ran for four years using around 100 workstations   # pp.112, 114
results:
| metric | value | unit | technology / device | baseline | condition | page |
| sufficient error bound for exp(x) | 2^-112 | mantissa distance | UNKNOWN; 2001 | none | full fp64 range, \|x\| >= 2^-30, all four rounding modes | p.114 |
| sufficient error bound for exp(x) | 2^-157 | mantissa distance | UNKNOWN; 2001 | none | full fp64 range, \|x\| < 2^-30, all four rounding modes | p.114 |
| sufficient error bound for ln(x) | 2^-117 | mantissa distance | UNKNOWN; 2001 | none | full fp64 range, all four rounding modes | p.115 |
| sufficient error bound for 2^x | 2^-112 | mantissa distance | UNKNOWN; 2001 | none | full fp64 range, all four rounding modes | p.115 |
| sufficient error bound for log2(x) | 2^-108 | mantissa distance | UNKNOWN; 2001 | none | full fp64 range, all four rounding modes | p.115 |
| sufficient error bound for sin(x) | 2^-118 | mantissa distance | UNKNOWN; 2001 | none | 1/32 <= \|x\| <= 2, all four rounding modes | p.116 |
| sufficient error bound for asin(x) | 2^-117 | mantissa distance | UNKNOWN; 2001 | none | sin(1/32) <= x <= 1, all four rounding modes | p.116 |
| sufficient error bound for cos(x) | 2^-108 | mantissa distance | UNKNOWN; 2001 | none | 1/64 <= x <= 12867/8192, all four rounding modes | p.116 |
| sufficient error bound for acos(x) | 2^-115 | mantissa distance | UNKNOWN; 2001 | none | cos(12867/8192) <= x <= cos(1/64), all four rounding modes | p.116 |
| sufficient error bound for tan(x) | 2^-110 | mantissa distance | UNKNOWN; 2001 | none | 1/32 <= x <= arctan(2), all four rounding modes | p.116 |
| sufficient error bound for atan(x) | 2^-108 | mantissa distance | UNKNOWN; 2001 | none | tan(1/32) <= x <= 2, all four rounding modes | p.116 |
| inverse-function search speedup | approximately 53 | times faster | workstations; 2001 | testing 2^x test numbers over the corresponding domain | search log2(y) over [1/2,2] instead of 2^x over [-1,1] | p.113 |
| inverse-function search speedup | 27 | times faster | workstations; 2001 | separately checking all FP numbers in both domains | search log2(y) test numbers over [1/2,2] | p.113 |
errors_and_checks: The contract is correct rounding in each of the four IEEE-754 modes when the approximation's mantissa-distance error does not exceed the reported bound. The listed worst cases also serve as tests for libraries claiming correct rounding. # pp.111, 114-116
conditions: Full-range exhaustive results apply to exp, ln, 2^x, and log2. # pp.114-117 Trigonometric results apply only to the intervals reported in Tables 6-11. # pp.116-118 Exact breakpoint cases such as log(1), sin(0), and integer inputs to 2^x or 10^x require separate handling. # p.112 The search assumes normalized inputs/outputs, with potential denormal outputs checked separately. # p.113 Extending the method to quadruple precision requires an algorithmic breakthrough according to the paper. # p.117
evidence: §1; §§2.1-2.4; §§3.1-3.2; Properties 1-5; Tables 2-11, pp.111-118

## new_families
none

## space_gaps
* The correct_rounding_strategy family lacks a choice for the offline worst-case search method; this paper uses polynomial filtering followed by a Euclidean grid-distance test and accurate candidate evaluation. # pp.112-114

## open_questions
* The paper does not establish full-range worst-case bounds for the trigonometric functions. # pp.116-117
* The paper does not specify a hardware architecture, area, delay, power, or implementation technology for an elementary-function unit.
