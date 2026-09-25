---
handle: juang_2009
citation: T.-B. Juang, S.-H. Chen, H.-J. Cheng, "A Lower Error and ROM-Free Logarithmic Converter for Digital Signal Processing Applications", IEEE Transactions on Circuits and Systems II, vol. 56, no. 12, pp. 931-935, 2009
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [binary_fixed_point]
authority: incremental
pages_read: 931-935 / 5
---

## summary
The document proposes a ROM-free binary-to-logarithmic converter that partitions log2(1+x) into two symmetric linear-approximation regions with inverse slopes (pp. 931-933). A 32-bit implementation in 0.13-µm TSMC CMOS reports 2.8 ns latency, 5586 µm2 area, a 0.045 error range, and a 3.339% percent-error range (pp. 931, 934-935).

## families
### logarithmic_converters  (role: proposes)
mechanism: The converter writes N = 2^k(1+x), approximates log2(1+x), and adds k. The range 0 ≤ x < 1 is divided at x = 0.5 into two symmetric regions. The implemented equations use additions/subtractions, shifts, and constants decomposed into pairs of powers of two, so no ROM or multiplier is required. The first region uses x+(2^-3+2^-4)x4MSBits. The second uses x-(2^-3+2^-5)x4MSBits+(2^-3+2^-5). (pp. 932-933)
choices:
  correction: rom_free_shift_add   # pp. 931, 933
  regions: 2   # p.933
new_choices:
  region_symmetry: symmetric_inverse_slopes — the two approximation lines are symmetric and their slopes are inverses   # p.933
  approximated_fraction_bits: 9 — x-1 through x-9 are converted while x-10 through x-26 pass through unchanged   # pp.934-935
slots:
  none
parameters: 32-bit input; 6 integer bits; 26 fraction bits; 9 fraction bits used for conversion; 17 low fraction bits passed through; two regions; latency 2.8 ns; II UNKNOWN   # pp.934-935
results:
| metric | value | unit | technology / device | baseline | condition | page |
| error range | 0.045 | UNKNOWN | UNKNOWN; 2009 | none | proposed method; N = 2-4 comparison range | pp.931, 934 |
| percent error range | 3.339 | % | UNKNOWN; 2009 | none | proposed method; N = 2-4 comparison range | pp.931, 934 |
| error-range reduction | 47.7 | % | UNKNOWN; 2009 | Mitchell [10] | same simulated comparison range | p.934 |
| percent-error-range reduction | 40.6 | % | UNKNOWN; 2009 | Mitchell [10] | same simulated comparison range | p.934 |
| error-range reduction | 24.2 | % | UNKNOWN; 2009 | Abed and Siferd [13] | two-region methods | p.934 |
| percent-error-range reduction | 31.4 | % | UNKNOWN; 2009 | Abed and Siferd [13] | two-region methods | p.934 |
| latency | 2.8 | ns | TSMC 0.13-µm CMOS; 2009 | none | complete log2 N converter; 32-bit input | p.935 |
| area | 5586 | µm2 | TSMC 0.13-µm CMOS; 2009 | none | complete log2 N converter; 32-bit input | p.935 |
errors_and_checks: error = log2(1+x)-log2(1+x)′. The error range sums the absolute maximum positive and negative errors. The percent error divides the error by log2 N. The reported ranges are 0.045 and 3.339%, respectively; no formal accuracy guarantee or fault checker is reported.   # pp.933-934
conditions: The N = 2-4 range is used to expose the largest percent errors and compare methods fairly (pp.933-934). More approximation regions improve precision but require more area/control circuitry (pp.931-932). More accurate constants become more complex and may use canonic signed-digit encoding to minimize shifts (p.933). The proposed method has lower error with slightly increased hardware area relative to the simpler converters (p.935).
evidence: Section III, Fig. 4, equations (5)-(6), pp.933; Section IV, Fig. 5 and Table I, pp.933-934; Section V, Fig. 6 and Table II, pp.934-935.

### pwl  (role: extends)
mechanism: Two linear expressions approximate log2(1+x) over the uniform regions 0 ≤ x < 0.5 and 0.5 ≤ x < 1. The region boundary is selected by the first fractional bit. The coefficient products are implemented by two power-of-two shifts and an addition/subtraction. The construction couples the region slopes through symmetry and inverse-slope geometry rather than optimizing each region independently. (pp.932-933)
choices:
  segments: 2 [outside domain]   # pp.932-933
  segmentation: uniform   # pp.932-933
  x_frac_bits: 26 [outside domain]   # p.934
  slope_encoding: signed_po2_pair   # p.933
new_choices:
  region_symmetry: symmetric_inverse_slopes — constrains the two segment approximations through geometric symmetry   # p.933
  active_approximation_bits: 9 — distinguishes processed fraction bits from unchanged low bits   # pp.934-935
slots:
  segmenter: uniform_high_bit_decode   # p.932
parameters: two segments; boundary x = 0.5; four-MSB truncated term x4MSBits in the equations; 26 input fraction bits; 9 actively converted fraction bits   # pp.932-934
results:
| metric | value | unit | technology / device | baseline | condition | page |
| error range | 0.045 | UNKNOWN | UNKNOWN; 2009 | Mitchell [10]/Sangregory [12]/Abed [13] | proposed two-region approximation; N = 2-4 comparison range | pp.931, 934 |
| percent error range | 3.339 | % | UNKNOWN; 2009 | Mitchell [10]/Sangregory [12]/Abed [13] | proposed two-region approximation; N = 2-4 comparison range | pp.931, 934 |
| latency | 2.8 | ns | TSMC 0.13-µm CMOS; 2009 | none | complete 32-bit converter | p.935 |
| area | 5586 | µm2 | TSMC 0.13-µm CMOS; 2009 | none | complete 32-bit converter | p.935 |
errors_and_checks: The simulated approximation reports an error range of 0.045 and a percent-error range of 3.339%; no worst-case proof is reported.   # pp.931, 933-934
conditions: The two-region construction targets lower error without the LUT/control cost associated with increasing the number of approximation regions (pp.931-932). The implemented coefficient forms prioritize two-shift hardware over the more accurate constants available through more complex CSD encodings (p.933).
evidence: Section II, pp.932-933; Section III, Fig. 4 and equations (5)-(6), p.933; Section IV, Fig. 5 and Table I, pp.933-934; Section V, Fig. 6 and Table II, pp.934-935.

## new_families
none

## space_gaps
* `pwl.segments` excludes the demonstrated two-segment design because its declared domain starts at 8 (pp.932-933).
* `pwl` lacks a choice for coupling segment slopes through symmetry/inversion (p.933).
* `pwl` lacks a choice distinguishing actively approximated fraction bits from low bits passed through unchanged (pp.934-935).
* `pwl.x_frac_bits` excludes the implemented 26-bit fraction width (p.934).

## open_questions
* The supplied text does not reproduce the numeric cells of Table I beyond the values and reductions stated in the abstract/prose, so the merge pass must not reconstruct the remaining comparison values.
* The supplied text does not reproduce the Table II delay/area expressions for the compared converters, so their detailed baselines remain UNKNOWN.
