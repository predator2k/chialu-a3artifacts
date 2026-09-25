---
handle: alippi_1991
citation: C. Alippi, G. Storti-Gajani, "Simple Approximation of Sigmoidal Functions: Realistic Design of Digital Neural Networks Capable of Learning", IEEE International Symposium on Circuits and Systems (ISCAS), pp. 1505-1508, 1991
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [UNKNOWN]
authority: landmark
pages_read: 4 / 4
---

## summary
The document proposes discontinuous sum-of-steps and continuous piecewise-linear approximations for digital neural-network sigmoid units. The piecewise-linear design uses integer breakpoints/power-of-two values and requires only shifts/sums, which permits generalized-delta-rule learning. # p.1505, p.1506, p.1508

## families
### sigmoid_tanh_pwl  (role: proposes)
mechanism: The sigmoid is divided at consecutive integer arguments. Function values are selected as powers of two, and symmetry about the sigmoid midpoint supplies the positive half from the negative half. The resulting formulas use shifts and sums. A shift register produces the value, while a counter controlled by the integer part of the input supplies the shift amount and forces asymptotic zero/one values outside the retained range.
choices:
  approximation: shift_add_powers_of_two   # p.1505, p.1508
  symmetry_folding: true   # p.1508
new_choices:
  breakpoint_placement: consecutive_integer_grid — each linear segment spans consecutive integer input values   # p.1506, p.1508
slots:
  segmenter: none
parameters: sigmoid activation; unit-width input intervals; three or four significant counter bits according to chosen precision; shift-register-and-counter implementation   # p.1506, p.1508
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
errors_and_checks: No numerical maximum-error or ulp contract is reported. Figure 1 plots the sigmoid and approximation, while Figure 2 plots the derivative approximation used for learning.   # p.1507, p.1508
conditions: The continuous approximation supports generalized-delta-rule learning because a first derivative exists.   # p.1505, p.1506
evidence: §3 equations 11-15 and Figures 1-3, p.1506-p.1508; §4 and Figure 4, p.1508

### pwl  (role: instantiates)
mechanism: Consecutive integer breakpoints define linear sigmoid segments. The ordinate values and segment slopes reduce the evaluation to powers-of-two scaling plus addition. The integer part of the input determines the segment and shift count; input bits above the retained three or four counter bits select an asymptotic output.
choices:
  segmentation: uniform   # p.1506, p.1508
  slope_encoding: power_of_two   # p.1505, p.1508
new_choices:
  none
slots:
  range_reducer: none
  segmenter: none
parameters: degree 1; segment width 1 input unit; segment count UNKNOWN; coefficient/input word lengths UNKNOWN; three or four significant counter bits according to precision   # p.1506, p.1508
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
errors_and_checks: No numerical approximation bound is reported for the piecewise-linear construction.   # p.1507-p.1508
conditions: The design is slightly more complex than the discontinuous construction, but its continuity permits gradient-descent learning.   # p.1505-p.1506
evidence: §3 equations 11-15 and Figures 1-3, p.1506-p.1508; §4 and Figure 4, p.1508

## new_families
### sum_of_steps_activation  (domain: sfu: elementary-function units, closest: sigmoid_tanh_pwl, why_not: the mechanism is a discontinuous comparator-selected sum of steps rather than a piecewise-linear evaluator)
mechanism: Output-layer sigmoid units are replaced by one threshold step after learning. Hidden-layer sigmoid units are replaced by a sum of h steps whose subdivision points minimize the square integral norm. The subdivision values may be approximated by powers-of-two values with little change in the norm, so output evaluation uses comparators and weighted-input evaluation uses shifts rather than multipliers.
choices:
  layer_role: {output, hidden}
  step_structure: {single_step, error_selected_sum}
  breakpoint_encoding: {optimal_real, power_of_two_approximated}
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
evidence: §2, Theorem 2.1, Corollary 2.1, and Theorem 2.2, p.1505-p.1506

## space_gaps
* `sigmoid_tanh_pwl` lacks a breakpoint-placement choice for the consecutive-integer grid used by the piecewise-linear construction.   # p.1506, p.1508
* `pwl` lacks an evaluator slot for the shift/add implementation implied by power-of-two slopes.   # p.1508
* The segmentation vocabulary lacks an integer-part counter segmenter that saturates when more-significant input bits are set.   # p.1508
* The elementary-function vocabulary lacks a discontinuous sum-of-steps activation family.   # p.1505-p.1506

## open_questions
* The supplied text does not report the fixed-point input/output/coefficient widths.
* The supplied text does not fix a finite segment count for the piecewise-linear design.
* The formula defining the maximum allowed sum-of-steps error from k is not legible in the supplied text, so the merge pass must not reconstruct it.
* No synthesized/fabricated area, delay, power, technology, or device results are reported.
