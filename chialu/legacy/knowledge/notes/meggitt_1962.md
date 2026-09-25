---
handle: meggitt_1962
citation: J. E. Meggitt, "Pseudo Division and Pseudo Multiplication Processes", IBM Journal of Research and Development, vol. 6, no. 2, pp. 210-226, 1962
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [decimal, binary]
authority: landmark
pages_read: 16 / 17
---

## summary
The paper proposes digit-by-digit pseudo-division/pseudo-multiplication processes for division/multiplication/logarithm/exponential/trigonometric/square-root/square operations. A modifier register updates the divisor or multiplicand so one microprogrammed or conventional arithmetic unit can execute the operation-specific recurrences. The paper reports decimal examples, accuracy bounds, register sizes, and execution times measured in multiply times.

## families
### decimal_cordic_transcendental  (role: proposes)
mechanism: A repeated-subtraction pseudo divider forms digits \(q_j\) while a modifier register updates the pseudo divisor after each subtraction. A reversed repeated-addition pseudo multiplier processes the digits while updating the pseudo multiplicand. Operation-dependent modifiers and stored constants implement \(\log[1+(y/x)]\), \(\tan^{-1}(y/x)\), \(\sqrt{y/x}\), \(x(e^p-1)\), \(\tan p\), and \(xq^2\); shared flow paths also provide ordinary multiplication/division. The assumed radix is 10, although the paper states that the processes are not restricted to decimal arithmetic. # pp.210-226
choices:
  recurrence: pseudo_multiply_divide   # pp.210-226
new_choices:
  function_modes: {multiply, divide, log, exp, atan, tan, sqrt, square, sin, cos} — operations selected through branches of the common pseudo multiplier/divider routine   # pp.210, 220, 225-226
  modifier_source: {zero, divisor, shifted_remainder, precomputed_constant, shifted_pseudo_multiplicand} — operation-dependent source used to update the pseudo divisor or multiplicand   # pp.211-212, 216-218, 221-222
  digit_processing_order: {msd_first, lsd_first} — exponentials/squares process the most-significant digit first, while tangent uses the reverse order   # pp.220, 224-225
slots:
  none
parameters: radix 10; \(n\)-digit inputs and \(n\) pseudo-quotient digits; decimal quotient digits less than 10; operation-dependent registers of \(n+1\), \(n+2\), \(2n\), or \(2n+1\) digits   # pp.213, 217-218, 222-225
results:
| metric | value | unit | technology / device | baseline | condition | page |
| execution time | about three | multiply times | UNKNOWN / 1962 | current subroutine methods | \(\log[1+(y/x)]\), including division of \(y\) by \(x\) | p.216 |
| execution time | about three | multiply times | UNKNOWN / 1962 | current subroutine methods | \(\tan^{-1}(y/x)\), including division | p.218 |
| execution time | approximately three | multiply times | UNKNOWN / 1962 | UNKNOWN | \(xe^p\) or \(x(e^p-1)\) | p.223 |
| execution time | three | multiply times | UNKNOWN / 1962 | UNKNOWN | intermediate \(x\) and \(y\) for tangent | p.225 |
| execution time | four | times | UNKNOWN / 1962 | UNKNOWN | \(\tan p\), including final division | p.225 |
| execution time | approximately seven | multiply times | UNKNOWN / 1962 | UNKNOWN | \(\sin p\) or \(\cos p\) | p.225 |
| execution time | two | multiply times | UNKNOWN / 1962 | UNKNOWN | \(xq^2\) | p.225 |
errors_and_checks: Shifted-modifier rounding gives a worst-case pseudo-quotient error below 2.5 in its last digit for the logarithm process and 2.5 for inverse tangent. # pp.214, 217. The exponential result has at most 3 units of error in the least-significant digit after scaling. # p.223. The tangent phase error is at worst 2.5 units in the least-significant figure of \(p\). # p.225. The square result has at most 3 units of error in its least-significant digit. # p.225
conditions: The logarithm process requires \(y/x < 2^{10}-1\) so \(q_0<10\). # p.213. The direct \(\log z\) setup applies for \(0.1 \le z < 1\). # p.216. The inverse-tangent process imposes no restriction on \(y/x\). # p.217. The exponential treatment assumes positive \(p\), with \(p<10\log 2\) keeping \(q_0<10\). # pp.220-221. The tangent process assumes \(0\le p\le\pi/2\). # p.223. The reported speed comparison assumes repeated-addition multiplication without acceleration tricks. # p.216. Common hardware or microprogram control is presented as economical for small machines. # pp.210, 226
evidence: Equations (1)-(74); Figures 2-6; Tables 1, 2, 4, and 5; Sections 1 and 2, pp.210-226.

### decimal_digit_recurrence  (role: instantiates)
mechanism: The ordinary division mode repeatedly subtracts the divisor until the remainder would become negative, records the subtraction count as one quotient digit, restores after the extra subtraction, shifts the remainder by 10, and repeats for \(n\) digits. The same registers and control provide the baseline flow from which the pseudo divider adds modifier-driven divisor updates. # pp.210-212
choices:
  quotient_digit_set: nonredundant_0_9   # p.210
new_choices:
  digit_selection: repeated_subtraction_count — a counter records how many subtractions form each quotient digit   # p.210
slots:
  none
parameters: \(n\)-digit dividend/divisor; one decimal quotient digit per iteration; \(n\) iterations; \(A\) has \(n+1\) digits; \(Q\) has \(n\) digits   # p.210
results:
| metric | value | unit | technology / device | baseline | condition | page |
| accuracy | exact, except for the remainder | UNKNOWN | UNKNOWN / 1962 | UNKNOWN | ordinary division | p.210 |
errors_and_checks: The ordinary quotient is exact except for the remainder. # p.210
conditions: The input ratio must satisfy \(y/x<10\) so each quotient digit remains less than 10. # p.210
evidence: Section 1 and Figure 1, p.210; shared modified-divider flow in Figures 2-3, pp.211-212.

### iterative_decimal_multiplication  (role: instantiates)
mechanism: The ordinary multiplication mode holds the multiplier in \(Q\), the multiplicand in \(B\), and the product in \(A\). Each multiplier digit controls repeated additions before the next digit is processed. The pseudo-multiplication modes reuse this datapath while loading stored constants or updating the pseudo multiplicand through the modifier register. # pp.215, 221-222
choices:
  multiplier_digit_recoding: none   # pp.215, 221-222
  digits_per_cycle: 1   # pp.215, 221-222
new_choices:
  digit_multiple_generation: repeated_addition_count — a digit is implemented through repeated additions rather than a precomputed multiple mux   # pp.215-216
slots:
  none
parameters: decimal digit-serial processing; multiplier in \(Q\); multiplicand in \(B\); product in \(A\)   # p.215
results:
| metric | value | unit | technology / device | baseline | condition | page |
| implementation assumption | repeated addition | UNKNOWN | UNKNOWN / 1962 | UNKNOWN | timing comparisons for the pseudo processes | p.216 |
errors_and_checks: none
conditions: The execution-time assessment assumes multiplication by repeated addition without acceleration tricks. # p.216
evidence: Figure 4, p.215; execution-time qualification, p.216; Figure 6, p.222.

## new_families
none

## space_gaps
* `decimal_cordic_transcendental` lacks choices for function mode/modifier source/digit-processing order, although these choices distinguish the paper’s shared recurrences. # pp.210-226
* `decimal_cordic_transcendental` lacks a slot for an operation-constant ROM containing \(\log(1+10^{-j})\) or \(\tan^{-1}(10^{-j})\); the existing `angle_table` slot admits reciprocal-seed families rather than this constant store. # pp.215, 218, 221, 224
* `decimal_digit_recurrence` lacks repeated-subtraction/count digit selection because its only `digit_select` filler is `qds_table`. # p.210
* `iterative_decimal_multiplication` lacks repeated-addition digit-multiple generation because `multiple_set` only describes precomputed multiple sets. # pp.215-216
* Radix 10 is absent from the radix domain of related `sfu` digit-recurrence/CORDIC families even though this paper develops the recurrences explicitly in base 10. # p.210

## open_questions
* Page 219 is absent from the supplied document text, so omitted square-root register-size/accuracy details must not be reconstructed from the surrounding pages.
* The paper states that base 10 is not a restriction and gives binary simplifications, but it does not report a separate binary implementation or binary performance result. # pp.210, 218
