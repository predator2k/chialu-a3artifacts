---
handle: volder_1959
citation: J. E. Volder, "The CORDIC Trigonometric Computing Technique", IRE Transactions on Electronic Computers, vol. EC-8, no. 3, pp. 330-334, 1959
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [twos_complement_fixed_point]
authority: landmark
pages_read: 330-334 / 5
---

## summary
CORDIC computes plane rotations and rectangular-to-polar conversions through sequential conditional shift-and-add pseudo-rotations in ROTATION/VECTORING modes (pp.330-333). The prototype arithmetic unit uses three shift registers and three adder-subtractors, with multiplication routines compensating for the constant magnitude gain (pp.330, 332, 334).

## families
### cordic  (role: proposes)
mechanism: Three registers hold Y, X, and angle values. Each step cross-adds shifted X/Y values while the angle register adds or subtracts a stored ATR constant. ROTATION selects the direction from the angle-remainder sign; VECTORING selects it from the Y sign. The first rotation is 90°, and subsequent angles are α_i = tan^-1 2^-(i-2). Every step uses a nonzero digit ξ_i ∈ {+1, -1}, so the accumulated scale factor K depends only on the predetermined step count. # pp.331-333
choices:
  mode: both   # p.331
  coordinate_set: circular   # pp.331-332
  topology: folded_sequential   # pp.330, 332-333
  scale_compensation: constant_multiplier   # pp.332, 334
  angle_recoding: true   # pp.332-333
new_choices:
  first_rotation_angle: 90° — the selected first and most-significant rotation magnitude   # pp.331-332
  rotation_digit_set: {+1, -1} — the permitted direction operator at every step   # pp.331-332
  digit_selection_source: angle_register_sign_or_Y_register_sign — ROTATION senses the angle remainder; VECTORING senses Y   # p.333
slots:
  none
parameters: three shift registers; three adder-subtractors; n finite pre-established steps; n depends on desired accuracy; K = 1.646760255 when n = 24; operation word times equal the word length   # pp.330, 332, 334
results: none
errors_and_checks: The ROTATION angle remainder after n steps satisfies |X_(n+1)| < α_n, and the VECTORING convergence proof follows by replacing X with θ; the worked sequences truncate shifted quantities without round-off. No fault model or detection coverage is reported.   # p.333
conditions: Angular increments must occur in decreasing order, and zero rotation is prohibited at every step. The represented input angle must satisfy -180° < X or θ < +180°. The method targets special-purpose computers dominated by trigonometric work. Constant scale-factor compensation requires multiplication routines; the navigation example uses two multiplications for five trigonometric operations.   # pp.331-334
evidence: Functional description and Fig. 1 (p.331); recurrence, scale factor, ATR constants, and Fig. 2 (p.332); convergence argument and Tables I-II (p.333); navigation flow and conclusion (p.334).

## new_families
none

## space_gaps
* `cordic.first_rotation_angle` is absent; the implementation selects 90° while noting that several first-step magnitudes are permissible.   # p.331
* `cordic.rotation_digit_set` and its mode-dependent selection source are absent.   # pp.331-333

## open_questions
* The constructed CORDIC I prototype's word length and step count n are not reported.
* The implementation technology is not reported.
* The paper does not state whether scale compensation is integrated into the arithmetic unit or always performed by separate multiplication routines.
