---
handle: avizienis_1961
citation: Avizienis, "Signed-Digit Number Representations for Fast Parallel Arithmetic", IRE Transactions on Electronic Computers, 1961
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [signed_digit_radix_r, signed_digit_radix2_modified]
authority: landmark
pages_read: pp.389-400 / 12 pages
---

## summary
The paper defines redundant signed-digit representations that limit transfer propagation to one position during addition/subtraction, so operation time is independent of operand length (pp.389-390). The paper develops arithmetic procedures for addition, multiplication, Robertson division, roundoff, and multiple-precision operation (pp.394-397). The paper also reports existence-design complexity for radix-4 and radix-10 digit-adders (pp.397-398).

## families
### generalized_signed_digit  (role: proposes)
mechanism: A radix-r digit assumes symmetric positive/negative integer values. Addition first forms an interim digit and one-position transfer, `zi + yi = rti-1 + wi`, then forms `si = wi + ti`. Each result digit therefore depends only on two adjacent operand positions. A modified form uses two successive transfers and three addition steps, which permits radix 2 with digits `-1, 0, 1` (pp.390, 393-394).
choices:
  radix: integer r > 2; modified form permits r = 2 [outside domain]   # pp.391-394
  redundancy: minimal, intermediate, maximal   # pp.391-392
  digit_encoding: twos_complement   # p.398
  addition_scheme: carry_free; two_stage_limited_carry for the modified form   # pp.390, 393-394
  final_conversion: cpa   # p.393
new_choices:
  allowed_digit_set: `{-a, ..., -1, 0, 1, ..., a}` — selects the digit-value range for a radix   # pp.391-392
  transfer_span: {one_position, two_positions} — selects totally-parallel or modified two-transfer addition   # pp.390, 393-394
  space_zero: Bool — adds `0'` to mark a continuous string of nonsignificant positions   # p.397
slots:
  none
parameters: Standard addition uses `ti ∈ {-1,0,1}` and two steps; modified addition uses three steps. Radix-4 storage uses digit values `-3` through `3`; radix-10 minimal storage uses 13 values (pp.391, 393-394, 398).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| digit-adder logic | approximately 12 | conventional half-adder equivalents | UNKNOWN / 1961 | conventional radix-4 stage | radix-4 existence design | p.398 |
| digit-adder logic ratio | 2.5 to 3 | times | UNKNOWN / 1961 | conventional radix-4 stage with serial carry | auxiliary carry circuitry excluded | p.398 |
| storage per radix-4 digit | 3 | binary storage elements | UNKNOWN / 1961 | 2 elements for conventional radix 4 | seven signed-digit values | p.398 |
| digit-adder complexity ratio | about two | times | UNKNOWN / 1961 | conventional excess-three adder stage | radix-10 investigation | p.398 |
| simultaneous digits added | 2 / 3 / 5 | digits | UNKNOWN / 1961 | none | radix 4 / radix 5 / radix 10 | p.393 |
errors_and_checks: Zero has a unique representation when the digit magnitude does not exceed `r-1` (pp.390-392). Symmetric digit values with equally probable values give zero average truncation error (p.397). Overflow inspection uses the two most significant digits, but some representations near the range limit can indicate overflow while their algebraic values remain within range (p.392).
conditions: Addition/subtraction time is independent of operand length because every digit-adder operates simultaneously (p.397). Larger radix reduces relative storage overhead but increases digit-adder logic complexity (pp.397-398). The modified radix-2 form reduces digit-value redundancy but increases addition complexity and transfer propagation length (p.394).
evidence: Sections II-A-II-G, III-A, III-D, IV; Figs. 1-2; equations (1)-(30) (pp.390-398).

### sequential_shift_add  (role: instantiates)
mechanism: Multiplication maintains a signed-digit partial product and processes one multiplier digit per step. Each step adds or subtracts the selected multiple of the multiplicand and shifts the result right according to `pj+1 = (pj + zym-j)/r` (pp.395-396).
choices:
  bits_per_cycle: one radix-r digit [outside domain]   # p.395
  accumulator_form: signed_digit [outside domain]   # p.395
new_choices:
  multiplier_digit_recoding: minimal_canonical — reduces the maximum multiplier-digit magnitude before each step   # p.395
slots:
  step_adder: generalized_signed_digit [outside slot domain]   # pp.394-395
parameters: An `m+1`-digit multiplier uses the initialization in (32) followed by `m` recurrence steps; the example uses radix 10 (p.395).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| additions per step | 1 | addition | UNKNOWN / 1961 | conventional digit multiplication | odd radix with minimal-canonical multiplier and expanded adder inputs | p.395 |
| maximum additions per step | 2 | additions | UNKNOWN / 1961 | 1 for smaller multiplier digits | even radix when `|ym-j| = re/2` | p.395 |
errors_and_checks: Product overflow requires a terminal test when either operand lies in the potential-overflow range (p.395).
conditions: Minimal-canonical recoding requires fewer additions or multiple-generating circuits on average than conventional multiplier digits (p.395). Higher representation redundancy and greater adder complexity permit faster multiplication (p.395).
evidence: Section III-B, equations (32)-(34), Example 2 (pp.395-396).

## new_families
### signed_digit_robertson_division  (domain: div: dividers / square root, closest: srt_high_radix, why_not: The residual is signed-digit rather than carry-save, the radix is arbitrary, and quotient selection may use repeated add/subtract rather than a QDS table.)
mechanism: Division maintains signed-digit partial remainders using `pj+1 = rpj - dqj+1`. Redundant quotient digits permit an inexact magnitude comparison using a few leading digits. The simplest implementation repeatedly adds or subtracts the divisor after each left shift until the range test is satisfied; added comparators and divisor-multiple generators can select a quotient digit in one addition cycle (pp.396-399).
choices: radix: integer r > 2; residual_representation: signed_digit; quotient_digit_redundancy: minimal_to_maximal; digit_selection: {repeated_add_subtract, parallel_multiple_compare}; comparison_prefix_digits: Int[3..4:1] (pp.396-399)
results:
| metric | value | unit | technology / device | baseline | condition | page |
| comparison precision | first four | digits | UNKNOWN / 1961 | full partial-remainder comparison | minimal-redundancy quotient digits | p.396 |
| quotient-digit generation | 1 | addition cycle | UNKNOWN / 1961 | repeated divisor addition/subtraction | extra comparators and multiple generators | p.396 |
evidence: Section III-C, equations (35)-(38), Example 3, Appendix equations (40)-(49) (pp.396-399).

## space_gaps
* `generalized_signed_digit` should be allowed in the `sequential_shift_add.step_adder` slot because the multiplication recurrence uses a signed-digit adder (pp.394-395).
* `generalized_signed_digit.radix` should admit arbitrary integer radix greater than 2 and the modified radix-2 case (pp.391-394).
* `generalized_signed_digit` needs choices for the allowed digit set/transfer span/space-zero marker (pp.391-394, 397).
* The divider vocabulary lacks Robertson division with signed-digit residuals and redundant quotient digits at arbitrary radix (pp.396-399).

## open_questions
* The radix-4/radix-10 logic designs are existence demonstrations and make no claim of minimum complexity (p.398).
* The paper does not report a technology, clock rate, physical area, power, or measured delay.
* The statement that serial addition may begin at the most significant digit does not specify an online delay or a complete online interface (p.394).
