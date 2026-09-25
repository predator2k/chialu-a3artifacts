---
handle: vazquez_2009b
citation: Vazquez, Villalba, Antelo, "Computation of Decimal Transcendental Functions Using the CORDIC Algorithm", 19th IEEE Symposium on Computer Arithmetic (ARITH-19), 2009
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [bcd, decimal128]
authority: incremental
pages_read: 179-186 / 8 pages
---

## summary
The paper proposes a decimal floating-point CORDIC algorithm for circular/hyperbolic transcendental functions using a redundant 5221-derived angle sequence and a constant scale factor. The paper maps carry-propagate and decimal carry-save implementations onto an assumed IBM Power6/Z10-class DFPU.

## families
### decimal_cordic_transcendental  (role: proposes)
mechanism: A 5221-derived elementary-angle sequence performs four bit-weighted rotations per decimal digit using only x5/x2 scaling. The recurrence supports circular/hyperbolic coordinates and rotation/vectoring modes with a constant scale factor. Floating-point operation scales the y/z recurrences and selects a variable starting index J from the reduced argument exponent. Fast termination replaces the latter rotations with multiplication-add or division-add operations.
choices:
  recurrence: cordic_rotation   # p.180
  digit_representation: nonredundant_bcd   # pp.179-180
new_choices:
  elementary_angle_code: 5221 — redundant decimal code that supplies the rotation weights {1, 5, 2, 2}   # p.180
  coordinate_set: unified_circular_hyperbolic — the same angle sequence supports both coordinate systems   # pp.180-181
  operation_mode: rotation_and_vectoring — σi is selected from z[i] or y[i]   # p.180
  scale_factor: constant — the scale factor is independent of the rotation directions   # p.180
  floating_point_start_index: variable_J — J = 4Ezin − 3 for rotation or 4Eyin − 3 for vectoring   # p.182
  termination: multiply_add_or_divide_add — fast termination replaces approximately half the rotations   # p.183
slots:
  angle_table: UNKNOWN   # p.183
parameters: cos/sin/tan−1/sinh/cosh/tanh−1/exp/10x/ln/log10/sqrt; Decimal128 p=34; m=p+1=35; 4(p+1)=140 elementary rotations; p+4 decimal-digit datapath; 4 cycles/iteration; 562 cycles without fast termination; about 4B angles and 8B/3 scale factors stored for B fractional decimal digits   # pp.181-183
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency: sin/cos/sinh/cosh | 328 | cycles | assumed IBM Power6/Z10-class DFPU; 2009 | estimated 70-cycle Decimal128 fixed-point multiply; ratio 4.7 | fast termination; fixed-point range-reduced computation | p.184 |
| latency: tan−1(a/b)/tanh−1(a/b) | 375 | cycles | assumed IBM Power6/Z10-class DFPU; 2009 | estimated 70-cycle Decimal128 fixed-point multiply; ratio 5.4 | fast termination; fixed-point range-reduced computation | p.184 |
| latency: ln | 378 | cycles | assumed IBM Power6/Z10-class DFPU; 2009 | estimated 70-cycle Decimal128 fixed-point multiply; ratio 5.4 | fast termination; fixed-point range-reduced computation | p.184 |
| latency: exp | 328 | cycles | assumed IBM Power6/Z10-class DFPU; 2009 | estimated 70-cycle Decimal128 fixed-point multiply; ratio 4.7 | fast termination; fixed-point range-reduced computation | p.184 |
| latency: sqrt | 292 | cycles | assumed IBM Power6/Z10-class DFPU; 2009 | estimated 70-cycle Decimal128 fixed-point multiply; ratio 4.2 | fast termination; fixed-point range-reduced computation | p.184 |
| latency | between 300 and 400 | cycles | assumed state-of-the-art DFPU; 2009 | table-driven polynomial: about 560 or about 880 cycles | fixed-point reduced-range portion | p.186 |
| constant storage | 14 | Kbits | UNKNOWN; 2009 estimate | radix-10 BKM: about 380 Kbits; ratio 27 | fixed-point implementation | pp.185-186 |
| coefficient/constant storage | 9.4K | BCD digits | UNKNOWN; 2009 estimate | table-driven polynomial: about 120K or 4.5K BCD digits per function | CORDIC storage serves several functions | p.186 |
errors_and_checks: The target is one ulp, defined as maximum significand error ±10−(p−1). The derived configuration uses m=p+1 and B=p+3 fractional decimal digits; the paper states that these parameters assure one-ulp accuracy for the considered functions.   # p.182
conditions: A fully parallel decimal multiplier is assumed too costly in area/power for this use.   # p.179; The mapping adds an angle/scale-factor lookup table, table-to-datapath multiplexing, and minor control changes.   # p.183; The reported function-cycle counts exclude floating-point pre/postprocessing.   # p.184; Fast termination assumes 16-digit fixed-point multiply/divide latencies of 20/67 cycles.   # p.183
evidence: §§3-6, 8; equations (2)-(11); Figures 1-2; Table 1; pp.180-184, 185-186

### decimal_cordic_transcendental  (role: extends)
mechanism: The redundant version represents each coordinate as two decimal carry-save words and uses a decimal 3-to-2 adder. The rotation direction comes from leading bits of the scaled carry-save control coordinate. The redundancy of the 5221 angle sequence tolerates an incorrect estimated sign without repeating iterations.
choices:
  recurrence: cordic_rotation   # pp.184-185
  digit_representation: redundant_decimal   # p.184
new_choices:
  elementary_angle_code: 5221 — angle redundancy permits sign estimation without repeated iterations   # pp.184-185
  direction_selection: truncated_sign_estimate — σi is selected from leading bits of the redundant control coordinate   # pp.184-185
  sign_estimate_width: 10_bits — one sign/five integer/four fractional bits are assimilated   # p.185
  iteration_repetition: none — the basic angle sequence retains convergence after permitted sign-estimation errors   # pp.184-185
slots:
  angle_table: UNKNOWN   # pp.183-185
parameters: circular rotation analysis; t=4 fractional estimation bits; 10-bit sign detector; three pipeline stages; 13 FO4 assumed cycle time; two shifts/two 3-to-2 additions for each x/y iteration; 5 cycles/iteration   # pp.184-185
results:
| metric | value | unit | technology / device | baseline | condition | page |
| iteration latency | 5 | cycles | Power6-referenced 13 FO4 assumption; 2009 | carry-propagate implementation: 4 cycles/iteration; paper states 1.25 more cycles | redundant decimal carry-save implementation | p.185 |
errors_and_checks: A 10-bit sign estimate assures convergence for circular rotation despite the bounded wrong-sign case. Numerical error for the complete redundant floating-point implementation is UNKNOWN.   # pp.184-185
conditions: The convergence derivation is restricted to circular rotation because of space limits.   # p.184; The terminal carry-propagate adder remains necessary for conversion/rounding.   # p.185; The redundant implementation increases iteration latency while replacing the faster carry-propagate iteration adder with simpler carry-save hardware.   # p.185
evidence: §7, equations (12)-(14), §7.1, pp.184-185

### carry_save_datapath  (role: instantiates)
mechanism: Each CORDIC coordinate remains as two decimal carry-save words across iterations. Decimal 3-to-2 additions update the coordinates, while a leading-bit assimilation network estimates the sign of the control coordinate. Carry propagation is deferred until final conversion and rounding.
choices:
  compressor: 3_2   # p.185
  assimilation_point: end_of_chain   # p.185
  accumulator_redundant: true   # pp.184-185
new_choices:
  partial_assimilation_width: 10_bits — only the sign/five integer/four fractional bits needed for direction selection are assimilated each iteration   # p.185
slots:
  assimilator: UNKNOWN   # p.185
parameters: two-word decimal carry-save operands; 10-bit sign detector; three pipeline stages; 5 cycles/iteration   # p.185
results:
| metric | value | unit | technology / device | baseline | condition | page |
| iteration latency | 5 | cycles | Power6-referenced 13 FO4 assumption; 2009 | carry-propagate iteration: 4 cycles | CORDIC coordinate update | p.185 |
errors_and_checks: The partial sign assimilation preserves convergence under the derived wrong-sign bound; no fault-detection result is reported.   # pp.184-185
conditions: A carry-propagate adder is still used for final conversion/rounding.   # p.185
evidence: §§7-7.1, pp.184-185

## new_families
none

## space_gaps
* `decimal_cordic_transcendental` lacks choices for coordinate system, rotation/vectoring mode, elementary-angle code, constant-scale-factor handling, floating-point iteration indexing, and fast termination.   # pp.180-183
* `decimal_cordic_transcendental` lacks an iteration-adder slot that distinguishes carry-propagate from `carry_save_datapath`.   # pp.179, 184-185
* The `angle_table` slot accepts reciprocal-seed families whose `function` domain does not describe CORDIC angle/scale-factor constants.   # pp.182-183
* `carry_save_datapath` lacks a partial-assimilation/sign-estimation choice for redundant control recurrences.   # pp.184-185

## open_questions
* The carry-propagate adder topology used in the assumed DFPU mapping is not specified.
* The lookup-table organization, technology node, synthesized area, power, and clock frequency are not reported.
* The cycle results are architectural estimates and exclude floating-point pre/postprocessing rather than measured silicon results.
