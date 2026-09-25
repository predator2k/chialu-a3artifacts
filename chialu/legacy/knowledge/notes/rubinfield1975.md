---
handle: rubinfield1975
citation: L. P. Rubinfield, "A Proof of the Modified Booth's Algorithm for Multiplication", IEEE Transactions on Computers, vol. C-24, pp. 1014-1015, 1975
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [twos_complement_binary]
authority: incremental
pages_read: 2 / 2
---

## summary
The paper proves a modified Booth recoding that examines three multiplier bits and processes two multiplier bits per iteration. The algorithm reduces the iteration count from n to n/2 for an even n-bit two's-complement multiplier, at the cost of increased complexity per iteration (p.1014-p.1015).

## families
### booth_recoded_parallel  (role: analyzes)
mechanism: Three overlapping multiplier bits select z_i ∈ {-2, -1, 0, 1, 2} through z_i = y_i + y_i+1 - 2y_i-1. Table I maps each triplet to 0, ±X, or ±2X, and equations (1)-(6) prove that the selected multiples reconstruct the two's-complement product. Although the vocabulary family is parallel, the paper presents the recoding through an iterative partial-product recurrence rather than a parallel reduction tree (p.1014-p.1015).
choices:
  booth_radix: 4   # p.1014
  hard_multiple_gen: none   # p.1014
new_choices:
  scan_direction: least_to_most — Table I and the proof scan from the least-significant end, while the text states that decoding may begin from either end   # p.1014-p.1015
slots:
  reduction: none
  hard_multiple_adder: none
parameters: even n-bit multiplier; n+1 multiplier bits after appending y_n = 0; three-bit overlapping decode; two multiplier bits processed per iteration; multiples 0, ±X, ±2X   # p.1014-p.1015
results:
| metric | value | unit | technology / device | baseline | condition | page |
| iterations | n/2 | iterations | UNKNOWN; 1975 | original Booth algorithm: n iterations | n > 0 and even; three-bit decode with a two-place shift per iteration | p.1014-p.1015 |
errors_and_checks: The derivation proves exact two's-complement multiplication under the stated even-n and appended-zero assumptions; no approximate-error or fault-detection result is reported.   # p.1014-p.1015
conditions: The multiplier length must be positive and even (p.1015). An extra zero bit y_n must be appended to the multiplier before the first least-significant triplet is decoded (p.1015). The modified algorithm halves the iteration count but increases the complexity of each iteration (p.1014). The uniform two-place shift suits clocked systems better than data-dependent variable shifts according to the paper's framing (p.1014).
evidence: Table I and equations (1)-(6), p.1014; equations (7)-(8) and the four-step algorithm summary, p.1015.

### sequential_shift_add  (role: extends)
mechanism: The multiplier maintains one partial product and repeatedly applies PP_i = z_iX + (1/4)PP_i+2. Each iteration decodes the next overlapping three-bit window, adds or subtracts the selected multiplicand multiple, and shifts the new partial product and multiplier right by two places. A final one-place shift produces XY = (1/2)PP_1 (p.1015).
choices:
  bits_per_cycle: 2   # p.1015
new_choices:
  multiplier_digit_recoding: modified_booth_radix4 — overlapping three-bit windows select one of 0, ±X, or ±2X before each partial-product update   # p.1014-p.1015
slots:
  step_adder: UNKNOWN   # p.1015
parameters: n/2 iterations; initial partial product 0; two-place shift after each update; final one-place shift; n > 0 and even   # p.1015
results:
| metric | value | unit | technology / device | baseline | condition | page |
| additions/subtractions per iteration | 0 or 1 | operation | UNKNOWN; 1975 | UNKNOWN | selected multiple is 0, ±X, or ±2X according to Table I | p.1014-p.1015 |
errors_and_checks: The recurrence is algebraically proved to produce the exact product; no hardware fault model or checker is described.   # p.1014-p.1015
conditions: The implementation requires selection of ±2X as well as ±X and zero (p.1014). The paper does not specify the circuit family used for the reused addition/subtraction step (p.1015).
evidence: Table I, p.1014; equations (7)-(8) and the algorithm summary, p.1015.

## new_families
none

## space_gaps
* `sequential_shift_add` lacks a multiplier-recoding choice for the modified Booth three-bit/two-bit-per-iteration scheme (p.1014-p.1015).
* `booth_recoded_parallel` lacks an execution-organization choice that distinguishes iterative partial-product reuse from parallel partial-product generation/reduction (p.1015).

## open_questions
* The paper does not identify the adder architecture used for adding or subtracting z_iX from the shifted partial product.
* The paper states that decoding may begin from either end, but the displayed recurrence and procedural summary establish only the least-to-most-significant scan.
