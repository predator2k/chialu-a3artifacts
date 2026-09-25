---
handle: strollo_2011
citation: A. G. M. Strollo, D. De Caro, N. Petra, "Elementary Functions Hardware Implementation Using Constrained Piecewise-Polynomial Approximations", IEEE Transactions on Computers, vol. 60, no. 3, pp. 418-432, 2011
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fixed_point]
authority: incremental
pages_read: 418-432 / 15
---

## summary
The paper pairs adjacent uniform segments and shares selected polynomial coefficients by imposing continuity constraints at each pair midpoint, which reduces coefficient-ROM size for fixed-point elementary-function units (p.418-p.420). Mixed-integer optimization selects quantized coefficients and per-coefficient fractional widths, while direct and Horner evaluators implement degree-1/2/3 approximations in 90 nm CMOS (p.423-p.430).

## families
### piecewise_poly  (role: extends)
mechanism: The reduced interval is divided into M=2^m equal segments, and adjacent segments form pairs. Each segment uses a degree-N polynomial centered at the pair midpoint. Equality constraints between corresponding left/right coefficients impose continuity of the function or selected derivatives, so each constraint removes one stored coefficient per pair. A linear program computes real min-max coefficients, and a mixed-integer program computes finite-word-length coefficients under the same constraints. Direct evaluators form powers in parallel before a fused accumulation, while Horner evaluators use cascaded MAC stages.
choices:
  segments: {16, 32, 64, 128, 256, 512, 1,024, 2,048, 8,192} [outside domain]   # p.426-p.430
  degree: {1, 2, 3} [outside domain]   # p.418, p.427-p.430
  basis: minimax_remez   # p.421-p.423
  coeff_encoding: per_coeff_width   # p.424-p.427
  coefficient_optimization: joint_wordlength_search   # p.425-p.427
  rounding_contract: faithful   # p.419, p.426
new_choices:
  segment_pairing: adjacent_pairs — two adjacent uniform segments share constrained coefficients at their midpoint   # p.419-p.420
  continuity_orders: {0}, {1}, {2}, {0,1}, {0,1,2} — derivative orders constrained to be continuous at a segment-pair midpoint   # p.420-p.422, p.426-p.428
  coefficient_quantization_solver: mixed_integer_programming — integer coefficient values minimize sampled maximum error under continuity constraints   # p.423-p.425
slots:
  segmenter: uniform_high_bit_decode   # p.419-p.420
  evaluator: horner [degree=1|2|3]; parallel_monomial [architecture=direct, degree=1|2|3]   # p.419, p.427-p.428
parameters: target precision 12 to 42 bits; M=2^m uniform segments; two segments per pair; degree N=1, 2, or 3; P=80 sampling points in most coefficient optimizations; one pipeline level for direct implementations, and one/two/three pipeline levels for degree-1/2/3 Horner implementations   # p.418, p.423, p.427-p.428
results:
| metric | value | unit | technology / device | baseline | condition | page |
| lookup-table size reduction | 30 to 50 | percent | UNKNOWN (2011) | unconstrained piecewise-polynomial approximation with the same accuracy | elementary functions, target precision 12 to 42 bits | p.419, p.431 |
| ROM size reduction | 29 to more than 50 | percent | UNKNOWN (2011) | unconstrained degree-1 approximation | function continuity at pair midpoint, e1+eQcoeff=0.4 ulp | p.426 |
| ROM size reduction | larger than 38 | percent | UNKNOWN (2011) | unconstrained degree-2 approximation | function and first derivative continuous at pair midpoint | p.426 |
| ROM size reduction | larger than 40 | percent | UNKNOWN (2011) | unconstrained degree-3 approximation | function/first derivative/second derivative continuous at pair midpoint | p.427-p.428 |
| maximum clock frequency | larger than 1 | GHz | UMC 90 nm CMOS (2011) | none | degree-1, ulp=2^-12, high-speed implementation | p.430 |
| dynamic power | lower than 2.7 | mW@700 MHz | UMC 90 nm CMOS (2011) | none | degree-1, ulp=2^-12, low-power implementation | p.430 |
| maximum clock frequency | larger than 850 | MHz | UMC 90 nm CMOS (2011) | none | degree-1, ulp=2^-18, high-speed implementation | p.430 |
| dynamic power | 8.2 | mW@800 MHz | UMC 90 nm CMOS (2011) | none | degree-1, ulp=2^-18, high-speed implementation | p.430 |
| maximum clock frequency | 760 | MHz | UMC 90 nm CMOS (2011) | none | degree-2 direct architecture | p.430 |
| dynamic power | 17 | mW@800 MHz | UMC 90 nm CMOS (2011) | none | degree-2 direct architecture | p.430 |
| maximum clock frequency | 805 | MHz | UMC 90 nm CMOS (2011) | none | degree-2 Horner architecture | p.430 |
| dynamic power | 22 | mW@800 MHz | UMC 90 nm CMOS (2011) | none | degree-2 Horner architecture | p.430 |
errors_and_checks: The target is faithful rounding, defined as a result within 1 ulp. The sufficient budget is e1+eQcoeff+eQarith<0.5 ulp because final rounding contributes at most 0.5 ulp. Implemented coefficient designs generally allocate e1+eQcoeff=0.3-0.45 ulp, with 0.4 or 0.45 ulp used in reported ROM comparisons.   # p.419, p.425-p.427
conditions: The approximation stage assumes that f(x) and all derivatives are continuous and monotonic on the reduced interval; range reduction and reconstruction are outside the implementation studied (p.419). Function continuity does not increase maximum inherent error for odd N, while even N can incur an increase (p.421-p.422). Continuity of derivative order k has the smallest error increase when k is odd and N is even or when k is even and N is odd (p.422). Uniform segmentation simplifies addressing but can be less effective than nonuniform segmentation for highly nonlinear functions (p.418-p.419). Direct evaluation is preferred for degree 2, while Horner evaluation is preferred for degree 3 because the direct cuber has substantial overhead (p.430-p.431).
evidence: Sections 2-7; Figs. 1-14; Tables 2-9; pp.418-431.

## new_families
none

## space_gaps
* `piecewise_poly` lacks choices for adjacent-segment coefficient sharing, constrained derivative orders, and mixed-integer coefficient quantization, which are the paper's defining mechanisms (p.420-p.425).
* `truncated_fixed_width.target` lacks `cuber`, although the degree-3 direct evaluator uses a specialized truncated cuber (p.427-p.428).
* The evaluator vocabulary has no explicit `direct` value; `parallel_monomial` is the closest existing value for the paper's specialized power-generation/fused-accumulation architecture (p.419, p.427-p.428).

## open_questions
* Tables 2-9 are present as images without extracted cell contents, so the note records only numerical results repeated in the surrounding prose.
* The paper does not report the named topology of the parallel-prefix adders used for final additions in MACs/squarers/cubers (p.429).
