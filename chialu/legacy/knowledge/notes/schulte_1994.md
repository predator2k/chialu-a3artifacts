---
handle: schulte_1994
citation: M. J. Schulte, E. E. Swartzlander, "Hardware Designs for Exactly Rounded Elementary Functions", IEEE Transactions on Computers, vol. 43, no. 8, pp. 964-973, 1994
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [floating_point_16bit_significand, floating_point_24bit_significand]
authority: landmark
pages_read: 964-973 / 10
---

## summary
The document presents parallel piecewise-polynomial hardware for exactly rounded reciprocal, square-root, 2^x, and log2(x) with 16- and 24-bit significands. Chebyshev-derived coefficients are adjusted through exhaustive evaluation, and parallel term generation feeds a multi-operand adder or merged carry-save tree. The document compares linear/quadratic/cubic designs and an alternative maximum-error contract of one ulp.

## families
### piecewise_poly  (role: proposes)
mechanism: A k-bit high input part selects coefficients for an equal-size subinterval, while the remaining bits locate the input within that subinterval. Chebyshev-series coefficients are rounded and then adjusted in coefficient-ulp steps until exhaustive evaluation gives exactly rounded results. Polynomial powers/terms are generated in parallel and summed by a two's-complement multi-operand adder; a merged implementation places multiplication partial products and coefficients in one carry-save tree with one terminal carry-lookahead adder. # pp.965-969
choices:
  segments: 256 [outside domain]   # pp.965, 970-971, Figs. 15, 17-18
  degree: 1 | 2 | 3   # p.969
  basis: chebyshev   # pp.965-966
  coefficient_optimization: exhaustive_ulp_adjustment [outside domain]   # pp.966-967, Fig. 4
  rounding_contract: exact   # pp.969, 972
new_choices:
  term_reduction: separate_multioperand_adder | merged_carry_save_tree — selects separate parallel term products or one merged multiplication/addition tree   # pp.967-969, Figs. 6, 11
slots:
  range_reducer: range_reduction [method=function_specific_identity]   # pp.967-968, Fig. 5
  evaluator: parallel_monomial   # p.967, Fig. 6
  segmenter: uniform_high_bit_decode   # pp.965-966
parameters: reciprocal/square-root/2^x/log2(x); 16- or 24-bit significand; degree 1-3; 2^k equal subintervals; Fig. 15 uses an 8-bit subinterval index and a 1024-by-55 coefficient ROM for the exact 16-bit quadratic design.   # pp.965, 969-971
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 80 | ns | 1.0-micron CMOS; result 1994 | none | 24-bit-significand design for all four functions; exact rounding | p.964 |
| area | 98 | mm² | 1.0-micron CMOS; result 1994 | none | 24-bit-significand design for all four functions; exact rounding | p.964 |
| delay reduction | 5% to 30% | percent | 1.0-micron CMOS; result 1994 | exactly rounded designs | maximum error relaxed to one ulp | p.970 |
| area reduction | 33% to 77% | percent | 1.0-micron CMOS; result 1994 | exactly rounded designs | maximum error relaxed to one ulp | p.970 |
| unadjusted quadratic delay | 65 | ns | 1.0-micron CMOS; result 1994 | adjusted 16-bit quadratic; 27% lower | Chebyshev coefficients not adjusted | p.972 |
| unadjusted quadratic area | 39 | mm² | 1.0-micron CMOS; result 1994 | adjusted 16-bit quadratic; 95% lower | Chebyshev coefficients not adjusted | p.972 |
| unadjusted cubic delay | 128 | ns | 1.0-micron CMOS; result 1994 | adjusted 24-bit cubic-2; 24% lower | Chebyshev coefficients not adjusted | p.972 |
| unadjusted cubic area | 165 | mm² | 1.0-micron CMOS; result 1994 | adjusted 24-bit cubic-2; 136% lower | Chebyshev coefficients not adjusted | p.972 |
| reference multiplier delay | 34 | ns | 1.0-micron CMOS; result 1994 | none | 24-by-24-bit multiplier | p.969 |
| reference multiplier area | 16 | mm² | 1.0-micron CMOS; result 1994 | none | 24-by-24-bit multiplier | p.969 |
| reference multiplier delay-area product | 544 | ns·mm² | 1.0-micron CMOS; result 1994 | none | 24-by-24-bit multiplier | p.969 |
errors_and_checks: Exact results use round-to-nearest-even and have maximum error of half an ulp. Exhaustive evaluation verifies every input on the reduced interval; the alternative designs permit maximum error of one ulp. No fault model or concurrent checker is given.   # pp.964, 966-967, 970-972
conditions: The linear design has the lowest delay for 16-bit significands, while the quadratic design has the lowest area. The quadratic design has the lowest delay for 24-bit significands, while cubic-2 has the lowest area and delay-area product. The coefficient-adjustment method is infeasible for large significands because it exhaustively evaluates the input interval. The reported standard-cell estimates exclude argument-reduction delay/area.   # pp.965, 969
evidence: Sections II-III and V-VII; Tables I-IV; Figs. 1-4 and 6-19.

### correct_rounding_strategy  (role: proposes)
mechanism: The strategy computes a fixed-precision approximation in one hardware pass. Exhaustive simulation finds each input's distance from the nearest rounding boundary and adjusts stored coefficients until the prerounded result rounds to the exact round-to-nearest-even value. The sufficient condition requires the prerounded error to be smaller than Q(x), the distance between the exact function value and its nearest rounding boundary. # pp.966-967, 971-972
choices:
  strategy: single_pass_worst_case_precision   # pp.965, 971-972
  worst_case_knowledge: published_exhaustive   # pp.966-967, 971-972
  rounding_modes_covered: nearest_only   # pp.964, 969, 971
new_choices:
  coefficient_tuning: exhaustive_per_subinterval_ulp_adjustment — uses exact-result knowledge to reduce required internal accuracy   # pp.966-967, 972
slots:
  none
parameters: At least 2^p function evaluations for p-bit significands; tested at p=16 and p=24; coefficient selection/adjustment takes under 1 hr for p=24 on a 50-MFLOPS processor.   # pp.967, 969
results:
| metric | value | unit | technology / device | baseline | condition | page |
| coefficient-adjustment runtime | under 1 | hr | 50-MFLOPS processor; result 1994 | none | 24-bit significands | p.967 |
errors_and_checks: Exact rounding is guaranteed when the prerounded error is below Q(x) and the result is rounded to nearest. The paper notes that this condition is sufficient rather than necessary.   # pp.971-972
conditions: Exhaustive search makes the strategy unsuitable for double precision or other large word lengths. The strategy covers reciprocal/square-root/2^x/log2(x), but not trigonometric or inverse-trigonometric functions whose argument reduction can prevent exact rounding.   # p.965
evidence: Sections III, VI, and VII; Fig. 4; Tables III-IV; Fig. 19.

### range_reduction  (role: proposes)
mechanism: Function-specific input transformations map normalized IEEE operands to a polynomial input interval, and corresponding output transformations restore the exponent/sign and normalize the result. Reciprocal, square-root, and 2^x transformations preserve significand bits. The log2(x) path uses separate handling when the transformed exponent is zero to avoid precision loss from leading zeros. # pp.967-968, Fig. 5
choices:
  method: function_specific_identity [outside domain]   # pp.967-968
  worst_case_bound_proven: true   # pp.967-968
new_choices:
  supported_transform: reciprocal | square_root | exp2 | log2 — selects the exact-preserving input/output identity   # pp.967-968, Fig. 5
slots:
  none
parameters: normalized IEEE floating-point inputs; polynomial interval commonly [1, 2).   # pp.965, 967
results: none
errors_and_checks: The transformations maintain exact rounding for the four supported functions when the reduced-interval approximation is exactly rounded.   # pp.967-968
conditions: The method does not extend to trigonometric/inverse-trigonometric functions because their argument reduction can introduce errors that prevent exact rounding.   # p.965
evidence: Section IV and Fig. 5.

## new_families
none

## space_gaps
* `piecewise_poly.coefficient_optimization` lacks `exhaustive_ulp_adjustment`, which is the paper's central coefficient-selection mechanism. # pp.966-967
* `piecewise_poly.segments` ends at 64, while the illustrated 8-bit subinterval index gives 256 equal subintervals per function. # pp.965, 970-971
* `piecewise_poly` lacks a term-reduction choice for separate multi-operand addition versus a merged carry-save tree. # pp.967-969
* `range_reduction.method` lacks the function-specific exact-preserving identities used for reciprocal/square-root/2^x/log2(x). # pp.967-968

## open_questions
* The supplied rendering does not expose the numeric entries of Table III or all entries of Tables I-II clearly enough to transcribe them without guessing.
* Section VI says its estimates exclude argument-reduction delay/area, while the abstract calls 98 mm² the total chip area; the merge pass must preserve that qualification.
