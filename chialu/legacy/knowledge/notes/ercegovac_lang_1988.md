---
handle: ercegovac_lang_1988
citation: Ercegovac, Lang, "On-Line Scheme for Computing Rotation Factors", Journal of Parallel and Distributed Computing, 1988
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [sign-and-magnitude floating-point]
authority: incremental
pages_read: 209-227 / 19
---

## summary
The document proposes an integrated radix-2 on-line pipeline that computes Givens rotation factors from aligned floating-point fractions using sum-of-squares, square-root, and division recurrences (pp.209-211). Carry-save residual arithmetic, low-precision selection estimates, and on-the-fly conversion produce n-bit results in 10 + n clock cycles (pp.210, 221).

## families
### online_pipeline_composition  (role: proposes)
mechanism: Exponents are processed conventionally while significands pass through on-line alignment, sum of squares z = x² + y², square root d = z¹/², and two divisions c = g/d and s = h/d. Successive operations begin after their predecessors emit sufficient leading digits, so sequentially dependent stages overlap. The square-root and division algorithms are modified to reduce interface delay and implementation complexity. (pp.210-211)
choices:
  scheduling: digit_slice_overlapped   # pp.210-211
new_choices:
  operand_interface: parallel_or_byte_serial_input_online_output — The inputs may be loaded byte-serially, and results are available in bit-parallel and on-line forms.   # p.210
slots:
  none
parameters: n-bit significands; alignment delay 1 cycle; sum-of-squares delay 0 cycles; square-root delay 4 cycles; division delay 3 cycles; overall on-line delay 11 cycles; latency 10 + n clock cycles   # pp.212, 214, 216, 219, 221
results:
| metric | value | unit | technology / device | baseline | condition | page |
| execution time | 42 | Basic cycles | UNKNOWN | multiplier + adder: 120 Basic cycles | single-chip; 32-bit significands; year 1988 | p.221 |
| speed-up | 3 | UNKNOWN | UNKNOWN | multiplier + adder: 1 | single-chip; 32-bit significands; year 1988 | p.221 |
| execution time | 64 | Basic cycles | UNKNOWN | on-line design in this paper: 42 Basic cycles | redundant/on-line CORDIC; 32-bit significands; year 1988 | p.221 |
| execution time | 96 | Basic cycles | UNKNOWN | on-line design in this paper: 42 Basic cycles | 2MULT + ADD + SQR + 2DIV; 32-bit significands; year 1988 | p.221 |
| execution time | 160 | Basic cycles | UNKNOWN | on-line design in this paper: 42 Basic cycles | MULT + ADD + SQR + DIV; 32-bit significands; year 1988 | p.221 |
| execution time | 226 | Basic cycles | UNKNOWN | on-line design in this paper: 42 Basic cycles | CORDIC; 32-bit significands; year 1988 | p.221 |
| implementation width | approximately n/2 | bit slices per operation | UNKNOWN | UNKNOWN | carry-save implementation; year 1988 | p.221 |
errors_and_checks: The sum-of-squares residual bound gives (X[n]² + Y[n]² - Z[n]) < 2^-n for p = 0; no final rounding or fault-detection contract is reported.   # p.213
conditions: The scheme targets sequentially dependent arithmetic expressions and Givens rotation factors used in matrix triangularization/QR decomposition.   # pp.209-210 The comparison uses estimated basic-cycle equivalences rather than detailed implementations or a specified technology.   # pp.221-222 Special cases G = 0 and H = 0 are omitted.   # p.210
evidence: §1 and Fig. 1 (pp.209-211); §7 and Table I (pp.220-222)

### online_arithmetic_unit  (role: extends)
mechanism: Each significand stage maintains a scaled residual in redundant form and selects one output digit per cycle from a low-precision residual estimate. The sum-of-squares stage emits over-redundant digits, while square root and division emit digits in {-1, 0, 1}. Carry-save arithmetic avoids full carry propagation in the recurrence, and on-the-fly conversion forms conventional outputs. (pp.213-220)
choices:
  radix: 2   # p.209
  online_delay: 0 for sum of squares [outside domain]; 4 for square root; 3 for division   # pp.214, 216, 219
  residual_form: carry_save   # pp.210, 213-220
new_choices:
  selection_estimate_fraction_bits: 3 — Square-root and division digit selection uses residual estimates with three fractional bits.   # pp.216, 219
  input_digit_set: over-redundant_0_to_6 — The sum-of-squares output uses an over-redundant radix-2 digit set.   # p.214
  dividend_delivery: parallel — The specialized division recurrence receives h in parallel while d arrives on-line.   # p.218
  conventional_output_conversion: on_the_fly — Signed-digit outputs are converted without a separate terminal conversion pass.   # pp.210, 217, 219
slots:
  none
parameters: sum-of-squares result range 0.25 < z < 2; square-root result range 1/2 ≤ d < 2^1/2; square-root digit set {-1, 0, 1}; division quotient digit set {-1, 0, 1}   # pp.214, 216, 219
results:
| metric | value | unit | technology / device | baseline | condition | page |
| sum-of-squares on-line delay | 0 | clock cycles | UNKNOWN | UNKNOWN | carry-save implementation; year 1988 | p.214 |
| square-root on-line delay | 4 | clock cycles | UNKNOWN | UNKNOWN | carry-save residual; 3-bit fractional estimate; year 1988 | p.216 |
| division on-line delay | 3 | clock cycles | UNKNOWN | UNKNOWN | carry-save residual; 3-bit fractional estimate; parallel dividend; year 1988 | p.219 |
errors_and_checks: Residual bounds are derived for sum of squares, square root, and division; no fault model, detection coverage, or false-alarm behavior is reported.   # pp.213, 216, 224-226
conditions: A parallel dividend reduces the division interface delay, but the recurrence requires minor modification when the dividend must arrive on-line.   # p.218 Carry-save and signed-digit implementations showed no clear difference in preliminary analysis, so the presented implementation uses carry-save adders throughout.   # p.210
evidence: §4 and Fig. 3 (pp.212-215); §5, Fig. 4, and Appendix A (pp.215-218, 223-224); §6, Fig. 5, and Appendix B (pp.217-220, 224-226)

### carry_save_datapath  (role: instantiates)
mechanism: Carry-save partial sums and stored carries hold recurrence residuals without carry assimilation across the full word. Short carry-propagate adders operate only on leading residual bits used by digit-selection functions. The sum-of-squares stage uses a 4-to-2 carry-save adder, and the square-root stage uses a 3-to-2 carry-save adder. (pp.214-217)
choices:
  compressor: 4_2 for sum of squares; 3_2 for square root   # pp.214, 217
  accumulator_redundant: true   # pp.210, 213-220
new_choices:
  mixed_compressor_by_stage: true — Different recurrence stages use different carry-save adder arities.   # pp.214, 217
slots:
  assimilator: none
parameters: sum-of-squares critical path of two multiplexers, one 4-to-2 carry-save adder, and a 3-bit carry-propagate adder; square-root critical path of a 5-bit carry-propagate adder, one multiplexer, and a 3-to-2 carry-save adder   # pp.214, 217
results:
| metric | value | unit | technology / device | baseline | condition | page |
| overall cycle-time path | roughly one multiplexer, one 4-to-2 carry-save adder, and one 3-bit carry-propagate adder | gate blocks | UNKNOWN | UNKNOWN | integrated rotation-factor scheme; year 1988 | p.221 |
errors_and_checks: none
conditions: Carry-save arithmetic is selected to make the component-operation bit slices identical.   # p.210 Approximately n/2 carry-save bit slices are required per operation because influence on selection advances about one bit per cycle.   # p.221
evidence: §1 (p.210); Figs. 3-5 (pp.214-220); §7 (p.221)

### online_msdf  (role: instantiates)
mechanism: Division computes a redundant quotient most-significant digit first. The partial remainder P[j] is updated in two carry-save steps, and qsel chooses sj ∈ {-1, 0, 1} from a four-most-significant-bit estimate with three fractional bits. The dividend h is supplied in parallel, the divisor d arrives on-line, and the quotient is converted on-the-fly. (pp.218-220)
choices:
  online_delay: 3   # p.219
  radix: 2   # pp.218-219
new_choices:
  dividend_form: bit_parallel — The specialized recurrence accepts the dividend off-line in parallel form.   # p.218
  estimate_fraction_bits: 3 — Quotient selection uses three fractional estimate bits.   # p.219
slots:
  none
parameters: n-bit quotient; quotient digit set {-1, 0, 1}; loop j = 1 through n + 3; pdiv = 3 clock cycles   # p.219
results:
| metric | value | unit | technology / device | baseline | condition | page |
| critical path | two multiplexers, one 4-bit carry-propagate adder, and one carry-save adder | gate blocks | UNKNOWN | UNKNOWN | division implementation; year 1988 | p.220 |
errors_and_checks: The quotient-selection intervals enforce |P[j]| < |D[j]|; no final rounding-error figure is reported.   # pp.218, 225-226
conditions: The bit-parallel dividend must be communicated to the division unit; an on-line dividend interface is possible with minor algorithm changes.   # p.218
evidence: §6 and Fig. 5 (pp.217-220); Appendix B (pp.224-226)

## new_families
none

## space_gaps
* online_arithmetic_unit lacks an over-redundant digit-set value for the sum-of-squares output digits 0 through 6.   # p.214
* online_arithmetic_unit lacks a choice for low-precision residual estimates used by digit-selection functions.   # pp.216, 219
* online_msdf lacks a choice distinguishing a bit-parallel dividend from an on-line dividend.   # p.218
* online_pipeline_composition lacks component slots for the aligned sum-of-squares, square-root, division, and on-the-fly conversion stages.   # pp.210-211

## open_questions
* The paper does not report a technology, device, area, power, or measured clock period; Table I contains rough cycle estimates.   # pp.221-222
* The paper does not specify a final IEEE-style rounding mode or an ulp guarantee for C and S.
* The paper states that the outputs have n-bit fractions but does not state whether the final digit is truncated or rounded.
