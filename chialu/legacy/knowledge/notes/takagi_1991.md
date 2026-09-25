---
handle: takagi_1991
citation: N. Takagi, T. Asada, S. Yajima, "Redundant CORDIC Methods with a Constant Scale Factor for Sine and Cosine Computation", IEEE Transactions on Computers, vol. 40, no. 9, pp. 989-995, 1991
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [binary_fixed_point, redundant_binary]
authority: incremental
pages_read: 989-995 / 989-995
---

## summary
The paper proposes double-rotation and correcting-rotation redundant CORDIC methods for sine/cosine computation with an operand-independent constant scale factor. Both methods use redundant binary arithmetic to eliminate carry propagation within each addition/subtraction while avoiding runtime scale-factor calculation and result correction. The paper proves errors below 2^-n when computational rounding errors are excluded.

## families
### redundant_cordic  (role: proposes)
mechanism: The double rotation method represents Xj, Yj, and Zj with redundant binary digits {-1,0,1}. Each iteration implements a negative rotation, nonrotation, or positive rotation through two rotation-extensions selected from the three pairs (qj,pj). Exactly two rotation-extensions occur for every input angle, so the scale factor K1 is constant and can be incorporated into X0. The rotation direction is selected from the three most significant digits of Zj-1, and the final redundant Xn/Yn values are converted to unsigned binary. # pp.989-991
choices:
  internal_representation: redundant_binary_digit_set_{-1,0,1} [outside domain]   # p.990
  scale_factor_fix: double_rotation   # pp.989-990
  radix: 2   # pp.989-990
new_choices:
  rotation_extensions_per_iteration: exactly_two — fixes the scale factor by pairing two subrotations in every iteration   # pp.989-990
slots:
  none
parameters: n-bit unsigned binary-fraction angle 0 <= θ <= π/4; 1-bit integer plus n-bit fractional outputs; n iterations; three Zj-1 digits inspected; Xj/Yj/Zj computed to about n + ⌈log2 n⌉ + 2 fractional positions when rounding errors are considered   # pp.989-991
results:
| metric | value | unit | technology / device | baseline | condition | page |
| combinational depth (computation time) | proportional to n | UNKNOWN | UNKNOWN; 1991 | conventional CORDIC with ripple carry adders: proportional to n^2 | combinational logic gates with restricted fan-in | p.993 |
| gate count | proportional to n^2 | gates | UNKNOWN; 1991 | conventional CORDIC: proportional to n^2 | combinational implementation | p.993 |
errors_and_checks: Ignoring rounding errors during computation, |X-cosθ| < 2^-n and |Y-sinθ| < 2^-n. Detailed rounding-error analysis is outside the paper's scope.   # p.991
conditions: The method removes carry propagation from each addition/subtraction and requires no runtime scale-factor calculation or result correction. Its iteration equations are more complex than those of the previous redundant CORDIC. In roughly the latter half of the iterations, the third operand of the Xj/Yj calculation can be neglected about half the time, and 2·arctan(2^-j-1) can be treated as 2^-j in roughly two thirds of those iterations.   # pp.991, 993
evidence: Section III, Algorithm SINCOS1, Lemma 1, Theorem 1, Fig. 1, and Section V, pp.990-993.

### redundant_cordic  (role: proposes)
mechanism: The correcting rotation method performs one rotation-extension in every step and an additional correcting rotation-extension every mth step. The correcting period m is an arbitrary integer. The fixed schedule gives every input angle the same number of rotation-extensions, so the scale factor K2 is constant and can be incorporated into X0. Xj, Yj, and Zj use redundant binary representation, and rotation directions are selected by inspecting leading digits of the remaining angle. # pp.989, 991-992
choices:
  internal_representation: redundant_binary_digit_set_{-1,0,1} [outside domain]   # pp.989, 991
  scale_factor_fix: correcting_iterations   # pp.989, 991-992
  radix: 2   # pp.991-992
new_choices:
  correcting_period: arbitrary_integer — controls how often an extra correcting rotation is performed   # pp.989, 991-992
slots:
  none
parameters: n-bit unsigned binary-fraction angle 0 <= θ <= π/4; 1-bit integer plus n-bit fractional outputs; n + 1 iterations; correcting period m; m + 2 leading digits inspected for the extra rotation, with a regular variant inspecting m + 2 digits throughout and a stated referee suggestion of m + 1 digits   # p.992
results:
| metric | value | unit | technology / device | baseline | condition | page |
| combinational depth (computation time) | proportional to n | UNKNOWN | UNKNOWN; 1991 | conventional CORDIC with ripple carry adders: proportional to n^2 | combinational logic gates with restricted fan-in | p.993 |
| gate count | proportional to n^2 | gates | UNKNOWN; 1991 | conventional CORDIC: proportional to n^2 | combinational implementation | p.993 |
errors_and_checks: Ignoring rounding errors during computation, |X-cosθ| < 2^-n and |Y-sinθ| < 2^-n.   # p.992
conditions: A larger m reduces the number of extra rotations but increases the maximum number of digits inspected to select a rotation direction. The method performs extra rotations and inspects more digits than the previous redundant CORDIC, but it avoids runtime scale-factor calculation and result correction. The correcting technique can be adapted to hyperbolic sine/cosine with a slight modification.   # pp.992-993
evidence: Section IV, Algorithm SINCOS2, Lemma 2, Theorem 2, Fig. 2, and Section V, pp.991-993.

## new_families
none

## space_gaps
* The `internal_representation` domain of `redundant_cordic` lacks the redundant binary digit set {-1,0,1}; the paper also states that carry-save form may be substituted with the same effect.   # pp.990, 993
* `redundant_cordic` lacks a `correcting_period` choice for the arbitrary integer m that trades extra rotations against rotation-direction selection width.   # pp.991-992

## open_questions
* The paper gives asymptotic depth/gate counts but no technology, device, concrete hardware area, clock period, or power result.   # p.993
* Detailed computational rounding-error analysis is explicitly outside the paper's scope.   # p.991
* The suggested hybrid that uses correcting rotations in the former half and double rotations in the latter half is not specified or evaluated as a complete algorithm.   # p.993
