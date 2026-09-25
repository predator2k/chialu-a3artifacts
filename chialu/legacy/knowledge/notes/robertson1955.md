---
handle: robertson1955
citation: J. E. Robertson, "Two's Complement Multiplication in Binary Parallel Digital Computers", IRE Transactions on Electronic Computers, 1955
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [twos_complement_binary]
authority: landmark
pages_read: pp.118–119 / 2 pages
---

## summary
The document extends sequential shift-add multiplication to two's-complement operands without a final correction, except when the multiplier equals -1. A negative multiplier is complemented serially, while the multiplicand is negated and each shifted partial product receives a corrected sign digit.

## families
### sequential_shift_add  (role: extends)
mechanism: Each of n steps senses one multiplier digit, conditionally adds the multiplicand to the partial product, and shifts the result right by one position. For a nonnegative multiplier, the recurrence is \(p_{k+1}=\frac{1}{2}(p_k+y_{n-k}x)\). For a negative multiplier, the machine forms \((-x)(-y)\), using least-significant-digit-first complementation of y. The shifted sign digit follows the common operand sign when the partial product and conditional addend signs agree; otherwise, the sum sign is used. # pp.118–119
choices:
  bits_per_cycle: 1  # p.118
new_choices:
  negative_multiplier_handling: negate_both_operands — A negative y is handled by forming (-x)(-y).  # pp.118–119
  multiplier_complementation: lsd_first_through_first_one — Digits through the first 1 remain unchanged, and all subsequent digits are complemented.  # p.119
  shifted_sign_generation: common_operand_sign_else_sum_sign — The inserted sign digit depends on whether the partial-product and addend signs agree.  # pp.118–119
slots:
  none
parameters: x and y use n+1 binary digits with one sign digit and n nonsign digits; -1 < x < 1 and -1 < y < 1; n steps; one conditional addition and one one-position right shift per step.  # pp.118–119
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| operation count | n | conditional additions | UNKNOWN | UNKNOWN | y < 0; accompanied by n right shifts | p.119 |
| operation count | n | right shifts | UNKNOWN | UNKNOWN | y < 0; accompanied by n conditional additions | p.119 |
errors_and_checks: The method forms the exact product under its stated restrictions and fails when y = -1; no fault-detection mechanism or numerical-error metric is reported.  # p.119
conditions: The multiplier digits must be sensed serially from the least significant digit, and hardware must complement the multiplicand and insert the correct partial-product sign digit. The proposed method may reduce multiplication time and sequencing hardware in ORDVAC or ILLIAC relative to their corrective-step methods.  # p.119
evidence: Recurrence and sign-digit analysis on p.118; serial complementation rule, restrictions, historical comparison, and implementation claim on p.119.

## new_families
none

## space_gaps
* sequential_shift_add lacks choices for signed-operand handling, serial two's-complement generation, and partial-product sign insertion.  # pp.118–119

## open_questions
* The document does not identify the adder circuit used for each conditional addition.
* The document does not quantify the claimed multiplication-time or hardware reduction relative to ORDVAC or ILLIAC.
