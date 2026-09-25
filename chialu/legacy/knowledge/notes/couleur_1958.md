---
handle: couleur_1958
citation: Couleur, "BIDEC - A Binary-to-Decimal or Decimal-to-Binary Converter", IRE Transactions on Electronic Computers, 1958
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [binary_integer, binary_coded_octal, gray_code, bcd8421]
authority: landmark
pages_read: 4 / 4
---

## summary
BIDEC converts binary/reflected-binary numbers to binary-coded decimal and converts binary-coded decimal back to binary through shift-register decades and conditional add-or-subtract-three logic. The basic design uses separate test and shift operations, while a proposed fused implementation performs one operation per binary bit.

## families
### binary_decimal_conversion  (role: proposes)
mechanism: Binary-to-decimal conversion shifts the source most-significant bit first through 4-stage BCD decades and adds binary 3 to every decade containing 5 or greater before each left shift. Decimal-to-binary conversion shifts least-significant bit first in the opposite direction and subtracts 3 from every decade containing 8 or greater after each shift. Each decade has independent correction logic, so decades can be cascaded without a stated limit. # p.314, p.316
choices:
  direction: both   # p.313
  structure: sequential_shift_adjust   # p.314, p.316
new_choices:
  test_shift_fusion: {separate_test_and_shift, fused_test_shift} — separate operations provide the basic implementation; blocking and setting selected stages during the shift theoretically doubles conversion speed.   # p.313, p.316
  input_loading: {serial, parallel} — binary input and BCD input can be loaded serially or in parallel with switches/disable gating.   # p.315, p.316
slots: none
parameters: 4N shift-register stages grouped into N 4-bit decades; one decade per output decimal digit; one binary bit shifted per conversion step; basic implementation uses two operations per binary bit; fused implementation uses one operation per binary bit theoretically.   # p.313, p.314, p.316
results:
| metric | value | unit | technology / device | baseline | condition | page |
| shift-register storage | 4 | stages per decimal digit | UNKNOWN / 1958 | UNKNOWN | basic BIDEC circuitry | p.313 |
| correction logic | 1 | 30-diode network per decimal digit | UNKNOWN / 1958 | UNKNOWN | basic BIDEC circuitry | p.313 |
| basic conversion work | 2 | operations per binary bit | UNKNOWN / 1958 | UNKNOWN | separate test and shift operations | p.313 |
| theoretical conversion work | 1 | operation per binary bit | UNKNOWN / 1958 | 2 operations per binary bit | test operation eliminated at increased complexity | p.313, p.316 |
| example conversion time | 20 | μsec | UNKNOWN / 1958 | UNKNOWN | 20-digit binary number or 6-digit decimal number using 1-μsec stages | p.316 |
errors_and_checks: none
conditions: The method imposes no stated limit on digit count, and one decade is required for each decimal digit in the result. # p.313, p.314 The basic circuit changes conversion direction through wiring, while a bidirectional device requires increased complexity. # p.313 Parallel binary loading requires per-decade disable gates to prevent premature correction. # p.315 Gray-code input requires a serial Gray-to-binary converter before the first shift-register stage. # p.315 The built model uses flip-flop shift-register stages and dc logic, and its logic inputs require a delay approximately equal to the test-pulse width because correction changes the tested stages. # p.316
evidence: Theory and binary-to-decimal recurrence on pp.313-315; Figs. 1-3 on pp.314-315; decimal-to-binary recurrence and Figs. 4-6 on pp.315-316; implementation and fused-operation observation on p.316.

## new_families
none

## space_gaps
* `binary_decimal_conversion` lacks a choice for separate versus fused correction/shift operations, which changes the stated operation count from two to one per binary bit. # p.313, p.316
* `binary_decimal_conversion` lacks a choice for serial/parallel loading and the associated disable gating. # p.315, p.316
* `binary_decimal_conversion` lacks an input-code choice covering binary/reflected binary/binary-coded octal sources. # p.313, p.315

## open_questions
* The summary names binary-coded octal input, but the detailed circuit discussion does not specify its additional input circuitry. # p.313
* The paper states that one device can support both directions at increased complexity, but it does not give the combined circuit or its component count. # p.313
* The paper gives no semiconductor technology, area, power, or measured conversion-time results for the built model. # p.316
