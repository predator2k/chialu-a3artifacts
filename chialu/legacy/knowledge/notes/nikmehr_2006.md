---
handle: nikmehr_2006
citation: Nikmehr, Phillips, Lim, "Fast Decimal Floating-Point Division", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, 2006
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [decimal32, decimal64, decimal128, bcd, dsd]
authority: incremental
pages_read: 951-961 / 11
---

## summary
The paper proposes a radix-10 SRT decimal floating-point divider whose carry-free recurrence uses a maximally redundant decimal signed-digit partial remainder and comparison-multiple quotient selection rather than a lookup table (pp.951, 953-959). A synthesized decimal128 implementation completes division in 37 cycles/86.2 ns and occupies 48100 2-input NAND gates (p.960).

## families
### decimal_digit_recurrence  (role: extends)
mechanism: The divider normalizes unpacked BCD coefficients, generates one maximally redundant quotient digit per radix-10 SRT iteration, and maintains the partial remainder in decimal signed-digit form using decimal carry-free addition. Nine truncated comparisons determine quotient-digit magnitude, while limited-range partial-remainder sign detection determines polarity concurrently. An on-the-fly convert-and-round unit produces the nonredundant RNE result and adjusts exact quotients. (pp.953-959)
choices:
  quotient_digit_set: maximally_redundant_m9_p9 [outside domain]   # pp.953-954
  digit_split: none   # pp.953-954
  divisor_prescaling: false   # pp.953-954
new_choices:
  quotient_selection: comparison_multiples — truncated partial remainders are compared with truncated divisor multiples instead of using a lookup table   # pp.955-959
  residual_encoding: decimal_signed_digit_8bit — each maximally redundant decimal digit is represented by an 8-bit BSD vector   # pp.952-953
slots:
  digit_select: comparison_multiple_qds [comparisons=9, quotient_digit_encoding=sign_magnitude]   # pp.955-959
parameters: radix 10; quotient digits -9 through 9; decimal32/decimal64/decimal128 coefficients of 7/16/34 digits; p+3 cycles including initialization and rounding; decimal128 p=34 and 37 cycles; four-digit limited-range comparators/sign detectors   # pp.953-954, 957-960
results:
| metric | value | unit | technology / device | baseline | condition | page |
| critical-path delay | 2.33 | ns | Artisan 0.18- m typical standard-cell library; 2006 | none | recurrence in Fig. 2 | p.960 |
| register contribution | 0.23 | ns | Artisan 0.18- m typical standard-cell library; 2006 | none | includes setup and hold times | p.960 |
| multiplexor contribution | 0.85 | ns | Artisan 0.18- m typical standard-cell library; 2006 | none | recurrence critical path | p.960 |
| QDS contribution | 1.25 | ns | Artisan 0.18- m typical standard-cell library; 2006 | none | recurrence critical path | p.960 |
| latency | 37 | cycles | Artisan 0.18- m typical standard-cell library; 2006 | none | decimal128, p=34 | p.960 |
| execution time | 86.2 | ns | Artisan 0.18- m typical standard-cell library; 2006 | none | decimal128, p=34 | p.960 |
| area | 48100 | 2-input NAND gates | Artisan 0.18- m typical standard-cell library; 2006 | none | unpacking/packing excluded | pp.959-960 |
| normalized latency | 1332 | FO4 | Artisan 0.18- m typical standard-cell library; 2006 | Wang-Schulte Newton-Raphson: 1733 FO4 fastest and 3772 FO4 slowest | decimal128 | p.960 |
| baseline latency | 113 | cycles | LSI Logic 0.11- m gflx-p standard-cell library, 1.2 V; 2004 | proposed divider: 37 cycles | Wang-Schulte, four-digit-per-cycle multiplier | p.960 |
| baseline execution time | 77.97 | ns | LSI Logic 0.11- m gflx-p standard-cell library, 1.2 V; 2004 | proposed divider: 86.2 ns | Wang-Schulte, four-digit-per-cycle multiplier | p.960 |
| baseline latency | 246 | cycles | LSI Logic 0.11- m gflx-p standard-cell library, 1.2 V; 2004 | proposed divider: 37 cycles | Wang-Schulte, reasonable lookup table and one-digit-per-cycle multiplier | p.960 |
| baseline execution time | 169.74 | ns | LSI Logic 0.11- m gflx-p standard-cell library, 1.2 V; 2004 | proposed divider: 86.2 ns | Wang-Schulte, reasonable lookup table and one-digit-per-cycle multiplier | p.960 |
errors_and_checks: RNE is the implemented default mode, including decimal halfway handling; zero detection of the final/earlier partial remainder identifies exact quotients and triggers coefficient/exponent adjustment. No numerical-error metric or fault checker is reported. Nonzero/nonspecial operands are assumed, so exception handling is excluded.   # pp.953-955
conditions: The architecture is optimized for speed at the expense of power and area, while low-power architectures remain open (p.951). The synthesis excludes operand unpacking/result packing (pp.959-960). The comparison uses different technologies through FO4 normalization, and the cited Newton-Raphson figures include unpacking/packing and other rounding modes (p.960).
evidence: Sections IV-VII; Table I; Figs. 1-2; equations (6), (10), (22), (26), and (34)-(43); pp.952-960.

### redundant_decimal_addition  (role: instantiates)
mechanism: The recurrence adds a DSD partial remainder to BCD divisor multiples with decimal carry-free addition. Carry propagation is limited to a small number of digit positions, so digitwise additions have length-independent execution time. BCD-to-DSD conversion requires no hardware delay in this representation, while DSD-to-BCD conversion requires carry generation. (pp.952-953, 956-959)
choices:
  digit_set: maximally_redundant_m9_p9   # pp.952-954
  operands_redundant: one   # pp.956-958
new_choices:
  digit_encoding: 8-bit BSD vector — each DSD digit uses four binary signed digits and represents values from -9 through 9   # pp.952-953
slots:
  none
parameters: one DSD addend and one BCD augend in recurrence/comparison adders; four-digit DCF comparators; full recurrence adder width follows coefficient precision   # pp.956-958
results: none reported for the adder alone
errors_and_checks: Exact carry-free arithmetic is claimed; no fault model or standalone error measurement is reported.   # pp.952-953
conditions: The paper attributes the DCF adder to earlier work and instantiates it here; DSD-to-BCD conversion remains time consuming.   # pp.952-953
evidence: Section IV; Sections VI-F and VI-H; pp.952-953, 956-959.

## new_families
### comparison_multiple_qds  (domain: div: quotient digit selection, closest: qds_table, why_not: the mechanism explicitly replaces the conventional QDS lookup table with comparators/sign detectors)
mechanism: Nine positive and nine 9's-complement comparison multiples are generated once during initialization. Symmetry reduces quotient-magnitude selection to nine limited-range DCF comparisons. Parallel limited-range sign detectors and a coder produce a sign-magnitude quotient digit, while duplicated partial-remainder sign detectors operate outside the next iteration's critical path. (pp.955-959)
choices: comparison_count: {9_symmetry_reduced, 18_direct}; comparison_precision: Int[4..4:1]; quotient_digit_encoding: {sign_magnitude}; pr_sign_detection: {limited_range_parallel}; multiple_generation: {initialization_cycle}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| integrated recurrence critical path | 2.33 | ns | Artisan 0.18- m typical standard-cell library; 2006 | lookup-table QDS not separately synthesized | Fig. 2 decimal divider | p.960 |
| integrated normalized latency | 1332 | FO4 | Artisan 0.18- m typical standard-cell library; 2006 | Wang-Schulte divider: 1733 FO4 and 3772 FO4 | decimal128 division | p.960 |
evidence: Section VI-D through VI-H; Tables II-IV; Figs. 1-2; pp.955-959.

## space_gaps
* `decimal_digit_recurrence.quotient_digit_set` lacks `maximally_redundant_m9_p9`, which the radix-10 carry-free recurrence requires (pp.953-954).
* `decimal_digit_recurrence.digit_select` accepts only `qds_table`, while this design replaces the table with comparison multiples/sign detectors (pp.951, 955-959).
* `redundant_decimal_addition` lacks a digit-encoding choice for the paper's 8-bit BSD-vector DSD representation (pp.952-953).

## open_questions
* The synthesis does not isolate the area or delay of the comparison-multiple QDS function from the complete recurrence.
* The power cost is not reported despite the stated speed-for-power/area optimization (p.951).
* The extracted equations omit some parameter symbols, so the prose-supported four-digit truncation values are recorded without reconstructing the missing notation (pp.957-958).
