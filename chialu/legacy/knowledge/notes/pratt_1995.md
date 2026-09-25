---
handle: pratt_1995
citation: Pratt, "Anatomy of the Pentium Bug", TAPSOFT/CAAP, LNCS 915, 1995
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [single_precision, double_precision, extended_precision]
authority: landmark
pages_read: 97-107 / 11
---

## summary
The paper reconstructs the Intel Pentium radix-4 SRT floating-point divider and analyzes five accessible quotient-digit table entries that contain 0 instead of 2. The defective entries can produce relative errors as large as 2^-14, with rates that depend strongly on operand distribution. The paper also shows that testing reachable components cannot detect entries mistakenly classified as unreachable.

## families
### srt_high_radix  (role: analyzes)
mechanism: The divider keeps partial remainder P in carry-save form as S+C and selects each radix-4 quotient digit m from chopped leading bits of P and D. Each cycle subtracts mD, shifts the partial remainder left two positions, and appends the positive or negative digit to separate R/L quotient registers. The final quotient is obtained from R-L after 34 cycles. # pp.99-102
choices:
  radix: 4   # p.99
new_choices:
  residual_form: carry_save — P is represented as S+C to bound carry-propagation time independently of word length.   # pp.101-102
  quotient_digit_set: [-2, -1, 0, 1, 2] — the PD-plot entries select one of five signed quotient digits.   # p.101
  quotient_accumulation: separate_positive_negative — positive/negative digits accumulate in R/L registers to avoid carry propagation.   # pp.99-102
slots:
  digit_select: qds_table   # pp.100-101
parameters: radix 4; exactly 34 cycles; 64-bit extended-precision mantissa plus guard/round/sticky bits; partial-remainder register at least 68 bits including sign; quotient estimate (R-L)/4^34.   # pp.100,102
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 34 | cycles | Intel Pentium / process UNKNOWN / 1994 | none | complete extended-precision division | p.100 |
| maximum observed relative error | 2^-14 | relative error | Intel Pentium / process UNKNOWN / 1994 | correctly operating divider | defective quotient-digit table | p.97 |
| random single-precision error rate | one in 40 billion | divisions | Intel Pentium / process UNKNOWN / 1994 | all random single-precision operand pairs | errors exceeding normal single-precision error | p.97 |
| random double-precision error rate | one in 9 billion | divisions | Intel Pentium / process UNKNOWN / 1994 | all random double-precision operand pairs | errors exceeding normal double-precision error | p.97 |
| faulty single-precision pairs | 1738 | dividend-divisor pairs | Intel Pentium / process UNKNOWN / 1994 | all single-precision operand pairs | single-precision quotient errors | p.103 |
| direct error rate in random computation | one in 4 million | divisions | Intel Pentium / process UNKNOWN / 1994 | one in 9 billion uniform-pair model | random arithmetic starting from constant 1 | p.106 |
| direct-plus-propagated error rate | one in 30,000 | divisions | Intel Pentium / process UNKNOWN / 1994 | direct errors only | 12 direct errors plus 1700 indirectly caused errors | p.107 |
| cycle-10 error probability | 0.08% | divisions | Intel Pentium / process UNKNOWN / 1994 | random operand model | integers 1 to 100 with 10^-6 subtracted | p.107 |
| cycle-11 error probability | 0.15% | divisions | Intel Pentium / process UNKNOWN / 1994 | random operand model | integers 1 to 100 with 10^-6 subtracted | p.107 |
| cycle-12 error probability | 0.17% | divisions | Intel Pentium / process UNKNOWN / 1994 | random operand model | integers 1 to 100 with 10^-6 subtracted | p.107 |
errors_and_checks: The intended 34-cycle computation supplies the guard/round/sticky bits needed for correct IEEE rounding. Five table entries containing 0 instead of 2 can cause relative error up to 2^-14; the 1738 single-precision errors have their most significant error bit distributed from bit 14 through bit 23. No hardware detection coverage or false-alarm behavior is reported.   # pp.97,100,102-104
conditions: The SRT recurrence is correct only when each selected m keeps P within the stated interval. Error rates based on uniformly distributed operands do not predict applications with structured data, where direct errors and propagated errors occur more frequently.   # pp.101,103,105-107
evidence: §2, Figures 1-2, pp.99-102; §3, pp.102-103; Tables 1-3, pp.103-106; §5, pp.105-107.

### qds_table  (role: analyzes)
mechanism: The PD-plot maps chopped partial-remainder/divisor values P'/D' to quotient digits in [-2,2]. Homogeneous digit regions are separated by thresholds that must remain inside correctness intervals. The top threshold is one cell position too low, so five reachable entries contain 0 where 2 is required. # pp.100-103
choices: none
new_choices:
  partial_remainder_chop: P' = floor(8P)/8 — the White Paper samples the first 7 significant bits of P.   # p.100
  divisor_chop: D' = floor(16D)/16 — the White Paper samples the first 5 significant bits of D.   # p.100
  carry_save_partial_remainder_chop: P' = (floor(8S)+floor(8C))/8 — carry-save representation widens the approximation interval to 1/4.   # p.102
  unreachable_entry_value: 0 — locations corresponding to no possible P/D are assigned to minimize power.   # p.101
slots: none
parameters: depicted as an 89 x 6 array under Coe's six-divisor-sample conjecture; entries are integers in [-2,2]; five accessible entries are erroneous.   # pp.100-103
results:
| metric | value | unit | technology / device | baseline | condition | page |
| erroneous accessible entries | 5 | entries | Intel Pentium / process UNKNOWN / 1994 | complete correct PD-plot | top threshold one position too low | p.102 |
| classified extended-precision errors | 9915 | errors | Intel Pentium / process UNKNOWN / 1994 | correct PD-plot | detected across cycles 9 through 33 | p.104 |
errors_and_checks: The defect is modeled as five entries set to 0 instead of 2. Approximately 600 cycle-33/34 errors may be absent from the classification because their magnitude is difficult to distinguish from normal truncation error.   # pp.102,104
conditions: Missing entries believed unreachable evade fabricated coverage tests. Randomly generated tests have a better chance of reaching such entries.   # p.98
evidence: Figure 2, pp.100-102; §3, pp.102-103; Tables 1-2, pp.103-104.

## new_families
none

## space_gaps
* `srt_high_radix` lacks a `residual_form` choice for the documented carry-save partial remainder.   # pp.101-102
* `srt_high_radix` lacks choices for the signed quotient-digit set and separate R/L quotient accumulation.   # pp.99-102
* `qds_table` lacks choices for P/D sampling precision, threshold placement, unreachable-entry initialization, and table-completeness verification.   # pp.100-103

## open_questions
* The paper cannot determine whether the Pentium uses Coe's six chopped divisor values or the White Paper's 16 values.   # pp.100,102
* The depicted 89-row PD-plot may contain one or two more rows than the physical Pentium table.   # p.100
* The classification may miss approximately 600 errors in cycles 33 and 34.   # p.104
