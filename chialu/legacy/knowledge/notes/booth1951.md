---
handle: booth1951
citation: A. D. Booth, "A Signed Binary Multiplication Technique", Quarterly Journal of Mechanics and Applied Mathematics, vol. 4, no. 2, pp. 236-240, 1951
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [signed_binary]
authority: landmark
pages_read: 236-240 / 5
---

## summary
The document proposes a uniform sequential technique for multiplying signed binary numbers represented in complementary form. Adjacent multiplier digits select addition, subtraction, or no arithmetic before a right shift, without separate sign examination or product correction. # p.236-238

## families
### sequential_shift_add  (role: extends)
mechanism: The multiplier is scanned from the least significant digit with an appended digit m_n+1 = 0. A 01 transition adds r to the partial-product sum, a 10 transition subtracts r, and 00 or 11 performs no addition or subtraction. Each step shifts the partial-product sum one place right, except the m_0 step. The same procedure applies to every sign combination. # p.238
choices:
  bits_per_cycle: 1   # p.238
  accumulator_form: carry_propagate   # p.238
  string_skipping: false   # p.238
new_choices:
  multiplier_recoding: adjacent_bit_transition_add_sub — Adjacent multiplier digits encode +r, -r, or zero while scanning from the least significant digit.   # p.238
  terminal_shift: omitted_at_m0 — The final m_0 operation does not shift the partial-product sum.   # p.238
slots:
  none
parameters: An n-digit multiplier is processed one digit at a time; m_n+1 is initialized to 0; the worked examples use four multiplier digits.   # p.238-240
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
errors_and_checks: The algebraic proof establishes the correct product modulo 2 for every sign combination of m and r; no numerical error metric or hardware checker is reported.   # p.238
conditions: The process assumes complementary representation modulo 2, begins with the least significant multiplier digit, and uses successive right shifts to realize multiplication by negative powers of two.   # p.236-238
evidence: Procedure and proof on p.238; four sign-combination examples on p.239-240.

## new_families
none

## space_gaps
* `sequential_shift_add` lacks a multiplier-recoding choice for Booth's adjacent-bit transition encoding with add/subtract/zero actions.   # p.238
* `booth_recoded_parallel.booth_radix` excludes radix 2, although the document establishes the original radix-2 adjacent-bit Booth recoding in a sequential implementation.   # p.238

## open_questions
* The document does not specify the circuit family used for the step adder.
* The document does not report area, delay, power, cycle time, technology, or implementation year.
