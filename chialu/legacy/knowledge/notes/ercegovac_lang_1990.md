---
handle: ercegovac_lang_1990
citation: Ercegovac, Lang, "Redundant and On-Line CORDIC: Application to Matrix Triangularization and SVD", IEEE Transactions on Computers, 1990
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fixed_point, floating_point, carry_save, signed_digit]
authority: landmark
pages_read: 725-740 / 16 pages
---

## summary
The paper replaces carry-propagate addition in CORDIC recurrences with carry-save or signed-digit addition and replaces variable shifters with delays in on-line implementations. Decomposed angle digits permit angle calculation, rotation, scale-factor correction, matrix triangularization, and SVD operations to overlap. The estimated speedups are about 4.5 for triangularization and about 4 for SVD relative to cited conventional CORDIC implementations.

## families
### redundant_cordic  (role: proposes)
mechanism: The angle CORDIC transforms its recurrences to eliminate one shifter and selects digits from {-1,0,1} using an estimate of the redundant residual. Carry-save or signed-digit addition removes carry propagation. The redundant digits make the CORDIC scale factor variable, so an on-line recurrence computes its square, an on-line square root computes K, and on-line division corrects the rotated results. # p.726-p.731
choices:
  internal_representation: carry_save; signed_digit [outside domain]   # p.726
  scale_factor_fix: online_scale_computation_and_division [outside domain]   # p.730-p.731
  radix: 2   # p.726
new_choices:
  angle_output_form: {decomposed_digits, carry_save} — selects transmission as the digit sequence a_j or as a carry-save angle   # p.727
  selection_estimate_fraction_bits: {1, 2} — fixes the residual-estimate precision used for redundant digit selection   # p.726, p.735, p.739
slots:
  none
parameters: n recurrence steps; digit set a_j={-1,0,1}; 2's-complement carry-save and signed-digit selection use 1 fractional bit; SVD angle recomposition uses on-line delay p=2 and 2 fractional bits   # p.726, p.735, p.739
results:
| metric | value | unit | technology / device | baseline | condition | page |
| speedup | between 4 and 6 | speedup | UNKNOWN / 1990 | nonredundant CORDIC recurrence | technology-dependent estimate | p.727 |
| triangularization latency | 3n+3 | cycles | UNKNOWN / 1990 | conventional CORDIC at 2.25dn cycles | rotation determines the iteration time | p.734 |
| triangularization speedup | approximately 4.5 | times faster | UNKNOWN / 1990 | conventional CORDIC with d=6 | same clock period assumed | p.734 |
| overlap contribution | 1.8 | speedup | UNKNOWN / 1990 | original nonoverlapped scheme | conventional scheme modified to overlap operations | p.734 |
| redundant-adder contribution | 2.5 | speedup factor | UNKNOWN / 1990 | overlapped carry-propagate scheme | estimated decomposition of total speedup | p.734 |
| SVD latency | 5n+10 | clock cycles | UNKNOWN / 1990 | implementation in [7] at 3.25nd cycles | complete system | p.736-p.737 |
| SVD speedup | about 4 | times faster | UNKNOWN / 1990 | implementation in [7] with d=6 | estimated complete system | p.737 |
| SVD speedup | 1.5 | times faster | UNKNOWN / 1990 | nonredundant scheme in [13] | estimated complete system | p.737 |
errors_and_checks: No quantified numerical-error bound or fault check is reported; the angle computation is evaluated to n-bit implementation precision.   # p.729
conditions: The digit-selection intervals require normalized x[j]; floating-point operands obtain normalized x[1] through the initial addition/subtraction, while fixed-point operands require scaling of a and b.   # p.726, p.729
conditions: The variable scale factor follows from allowing zero digits, so constant-factor compensation methods do not apply and actual division is required.   # p.730
conditions: The speed results are architectural estimates rather than measurements from a VLSI realization, and the paper makes no significant physical-area comparison.   # p.737
evidence: Sections II-IV; Figs. 1-11; Appendices A-B; p.726-p.731, p.737-p.739

### cordic  (role: extends)
mechanism: Circular CORDIC performs both vectoring for tan^-1(a/b) and rotations. The angle is retained as most-significant-first decomposed digits, so rotation omits the angle recurrence and overlaps with angle calculation. Unfolded on-line rotation uses delays instead of variable shifters, followed by variable scale-factor correction and on-the-fly conversion. # p.730-p.731
choices:
  mode: both   # p.725, p.730
  coordinate_set: circular   # p.726, p.730
  topology: unrolled_pipelined   # p.727, p.730
  iterations: n [outside domain]   # p.726, p.730
  scale_compensation: online_scale_computation_and_division [outside domain]   # p.730-p.731
  angle_recoding: true   # p.727, p.730
new_choices:
  angle_transport: decomposed_msd_first — transmits a_j digits directly and eliminates the rotation module's angle recurrence   # p.727, p.730
slots:
  none
parameters: n angle/rotation steps; partial rotation CORDIC; two clock cycles between consecutive rotation iterations; two on-line divisions for scale correction   # p.730-p.731
results:
| metric | value | unit | technology / device | baseline | condition | page |
| rotation initiation interval | 2 | clock cycles | UNKNOWN / 1990 | UNKNOWN | radix-4 on-line additions with one-cycle on-line delay | p.730 |
errors_and_checks: none
conditions: Decomposed angles remove angle accumulation only when the producing CORDIC supplies the a_j digits most significant first.   # p.730
evidence: Sections II and IV; Figs. 3, 10, and 11; p.727, p.730-p.731

### online_arithmetic_unit  (role: instantiates)
mechanism: The recurrence is unfolded into digit-serial signed-digit adders. Fixed shifts become wiring plus delay cells, which replaces variable shifters and permits dependent angle, rotation, square-root, multiplication, and division operations to overlap. The angle implementation groups three signed binary digits per clock, while the rotation uses radix-4 on-line addition. # p.727-p.730
choices:
  radix: 2 for angle addition; 4 for rotation addition   # p.727, p.730
  online_delay: 1   # p.727, p.730
  residual_form: signed_digit   # p.727
new_choices:
  digits_per_cycle: 3 — groups three signed binary digits for angle-recurrence addition   # p.727
slots:
  none
parameters: three sbits per clock for angle addition; two cycles per a_j component; one-clock-cycle addition delay; two-cycle interval between recurrence initiations   # p.727-p.730
results:
| metric | value | unit | technology / device | baseline | condition | page |
| component latency | 2 | cycles per a_j | UNKNOWN / 1990 | redundant-parallel scheme at one cycle | on-line angle recurrence | p.728 |
errors_and_checks: none
conditions: The on-line and redundant-parallel angle schemes are estimated to have similar speed; the on-line scheme replaces the shifter with delays but requires more adders.   # p.728
conditions: The redundant-parallel version is preferred for SVD because one unit can be pipelined to compute two concurrent angles.   # p.735
evidence: Figs. 3-7 and 17-21; p.727-p.728, p.735-p.737

### online_pipeline_composition  (role: instantiates)
mechanism: Decomposed angle digits start rotations before angle calculation finishes, and digit-serial square root/division operations overlap scale-factor computation with the CORDIC recurrences. SVD reuses one rotation unit because the right rotation begins after all input digits have entered the left rotation. # p.730-p.731, p.736
choices:
  scheduling: digit_slice_overlapped   # p.730-p.731, p.736
new_choices:
  none
slots:
  none
parameters: triangularization iteration 3n+3 cycles; SVD operation 5n+10 clock cycles   # p.734, p.736
results:
| metric | value | unit | technology / device | baseline | condition | page |
| two-sided rotation latency | 5n+6 | cycles | UNKNOWN / 1990 | UNKNOWN | one unit reused for left/right rotations | p.736 |
errors_and_checks: none
conditions: Rotation-unit reuse requires the right rotation to start only after every input digit has entered the left rotation.   # p.736
evidence: Figs. 15, 18, and 21; p.733-p.736

## new_families
none

## space_gaps
* `redundant_cordic.internal_representation` lacks `signed_digit`, which the paper implements alongside carry-save representation.   # p.726
* `redundant_cordic.scale_factor_fix` lacks `online_scale_computation_and_division` for the variable factor caused by zero-valued rotation digits.   # p.730-p.731
* `cordic.scale_compensation` lacks variable-factor computation by on-line product recurrence/square root/division.   # p.730-p.731
* `cordic` lacks an angle-output/transport choice for decomposed most-significant-first rotation digits.   # p.727, p.730

## open_questions
* The symbolic precision n is not fixed, so the paper does not establish an absolute latency for a specific operand width.   # p.726, p.734, p.736
* Technology/device, silicon area, clock frequency, and measured power are `UNKNOWN` because no VLSI realization is reported.   # p.737
