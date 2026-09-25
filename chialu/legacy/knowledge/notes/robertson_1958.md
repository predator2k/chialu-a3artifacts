---
handle: robertson_1958
citation: Robertson, "A New Class of Digital Division Methods", IRE Transactions on Electronic Computers, 1958
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [radix4_fraction, excess3_decimal]
authority: landmark
pages_read: 218-222 / 5 pages
---

## summary
The paper proposes digit-recurrence division with redundant quotient digits \(-n,\ldots,0,\ldots,n\), where \((r-1)/2<n<r-1\), and gives radix-4 and radix-10 implementations (pp. 218-221). The radix-4 implementation uses one binary adder, while the radix-10 implementation uses one sequential excess-three decimal adder and decomposes each quotient digit into two selection steps (pp. 220-222).

## families
### srt_high_radix  (role: proposes)
mechanism: Each iteration computes \(x_{j+1}=rx_j-q_{j+1}d\). The quotient digit is selected from \(-n,\ldots,n\) so that \(|x_{j+1}|<k|d|\), with \(k=n/(r-1)\). The radix-4 example uses \(n=2\), selects \(0,\pm1,\pm2\), and determines the operation through sign comparison and magnitude comparisons of \(4x_j\) against \(0.5d\) and \(1.5d\) (pp. 218-220).
choices:
  radix: 4   # p.220
  digit_redundancy: minimal   # p.220
new_choices:
  quotient_digit_bound: n=2 — The maximum absolute quotient digit; the general class requires \((r-1)/2<n<r-1\).   # pp.219-220
  digit_selection_implementation: sign_and_threshold_comparisons — The selector compares signs and truncated magnitudes rather than indexing a table.   # p.220
  divisor_multiple_generation: conditional_doubling — The datapath forms \(d\) or \(2d\) conditionally and complements the selected multiple for subtraction.   # p.220
slots:
  digit_select: none   # p.220
parameters: radix \(r=4\); \(n=2\); \(k=2/3\); quotient digits \(\{-2,-1,0,1,2\}\); one quotient digit per recurrence; seven binary comparison digits when \(1/4<|d|<1\)   # pp.220, 222
results:
| metric | value | unit | technology / device | baseline | condition | page |
| selection precision | 7 | binary digits | UNKNOWN; 1958 | UNKNOWN | \(r=4\), \(n=2\), \(1/4<|d|<1\) | pp.220, 222 |
| binary-adder requirement | 1 | binary adder | UNKNOWN; 1958 | conventional radix-4 division requires two sequential/parallel adder uses or full-precision formation/storage of \(3d\) | conditional doubling and complementing are provided | p.220 |
errors_and_checks: The recurrence preserves \(Qd+r^{-m}x_m=x_0\); no numerical error rate, fault model, or detection coverage is reported.   # p.218
conditions: The dividend and every partial remainder must satisfy \(|x_j|<k|d|\). Divisor standardization reduces selection precision. The method is best suited to floating-point units; fixed-point use requires facilities for simultaneous divisor/dividend shifting. Increasing overlap reduces selector precision but increasing the digit set requires more divisor multiples.   # pp.219-220
evidence: Introduction and recurrence on p.218; arithmetic-procedure analysis and Fig. 1 on pp.219-220; radix-4 implementation, Fig. 2, and Table I on p.220; selection-precision appendix on p.222.

### decimal_digit_recurrence  (role: proposes)
mechanism: The radix-10 design uses excess-three digits and one sequential decimal adder. Each digit is decomposed as \(q_{j+1}=q'_{j+1}+q''_{j+1}\), where \(q'_{j+1}\in\{-5,0,5\}\) and \(q''_{j+1}\in\{-2,-1,0,1,2\}\). The first step conditionally adds/subtracts \(5d\); the second conditionally adds/subtracts \(d\) or \(2d\). A shared circuit forms \(2d\) and \(5d\) through signal permutation (pp. 221-222).
choices:
  quotient_digit_set: redundant_m7_p7   # p.221
  digit_split: radix2_times_radix5   # pp.221-222
  divisor_prescaling: true   # p.222
new_choices:
  internal_digit_code: excess_three — The decimal adder and divisor-multiple circuits use excess-three representation.   # p.221
  multiple_storage: divisor_only — The design stores \(d\), but stores no divisor multiples.   # p.221
  multiple_generation: shared_doubling_quintupling — One permuted circuit sequentially forms \(2d\) and \(5d\).   # p.221
  digit_selection_implementation: sign_and_threshold_comparisons — The selection circuit compares truncated partial-remainder/divisor values.   # pp.221-222
slots:
  digit_select: none   # pp.221-222
parameters: radix \(r=10\); \(n=7\); \(k=7/9\); quotient digits \(\{-7,\ldots,7\}\); \(q'\in\{-5,0,5\}\); \(q''\in\{-2,-1,0,1,2\}\); one sequential excess-three decimal adder; three decimal comparison digits when \(1/10<|d|<1\)   # pp.221-222
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average operations | 2⅓ | operations per quotient digit | UNKNOWN; 1958 | 3.4 operations per quotient digit for conventional nonrestoring division with doubling/quintupling circuits | quotient digits \(-7,\ldots,+7\) assumed equally likely | p.222 |
| selection precision | 3 | decimal digits | UNKNOWN; 1958 | UNKNOWN | \(r=10\), \(n=7\), \(1/10<|d|<1\) | p.222 |
| decimal-adder requirement | 1 | decimal adder | UNKNOWN; 1958 | UNKNOWN | excess-three adder used sequentially | p.221 |
errors_and_checks: The exact recurrence contract applies; no numerical error rate, fault model, or detection coverage is reported.   # pp.218, 221-222
conditions: The divisor must be standardized to \(1/10<|d|<1\) for three-digit selection. The reported average assumes all quotient digits from \(-7\) through \(+7\) are equally likely. Step 1 is omitted when \(q'_{j+1}=0\).   # p.222
evidence: Radix-10 design choices and multiple-generation equations on p.221; Fig. 3, Table II, operation count, and selection-precision appendix on pp.221-222.

## new_families
### serial_redundant_quotient_conversion  (domain: dividers / square root, closest: srt_high_radix, why_not: The mechanism converts redundant quotient digits after recurrence rather than generating quotient digits or updating the residual.)
mechanism: Quotient digits are inspected serially from most significant to least significant. A negative digit is increased by the radix, and one unit is borrowed from the next more-significant digit. Because zero is a permissible digit, the signs of the divisor and partial remainder determine the sign of the next nonzero quotient digit, which permits borrow propagation through zero sequences (pp. 219-220).
choices: scan_direction: {most_significant_first}; zero_digit_sign_source: {divisor_partial_remainder_signs, attached_zero_sign}; terminal_overflow_handling: {quotient_register_add, decrement_lsd_and_add_divisor_to_remainder}
results: none
evidence: Quotient Conversion on pp.219-220 and Preliminary and Terminal Operations on p.220.

## space_gaps
* The `digit_select` slot permits only `qds_table`, while both examples use sign/magnitude comparison circuits with truncated operands (pp.220-222).
* The divider families lack a quotient-conversion slot for the paper's serial redundant-to-conventional conversion mechanism (pp.219-220).
* `decimal_digit_recurrence` lacks choices for excess-three internal encoding and shared on-demand \(2d/5d\) generation (p.221).

## open_questions
* The paper reports no technology/device, circuit delay, area, power, or implementation year distinct from the 1958 publication year.
* The paper does not specify whether the comparison-based selection circuit should be classified as a form of `qds_table`.
* The paper does not quantify the hardware or latency cost of serial quotient conversion.
