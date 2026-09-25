---
handle: brown_1960
citation: D. T. Brown, "Error Detecting and Correcting Binary Codes for Arithmetic Operations", IRE Transactions on Electronic Computers, vol. EC-9, pp. 333-337, 1960
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary, decimal_digit]
authority: landmark
pages_read: 333-337 / 5
---

## summary
The paper derives affine arithmetic codes C(n)=An+B that permit conventional binary addition followed by a constant/digit-carry correction. The codes detect or correct single-bit errors through minimum-distance constraints and residue arithmetic modulo A. The paper also gives minimum-length codes for power-of-two/power-of-ten bases and a B=0 single-digit variant. # p.333-p.336

## families
### an_code  (role: proposes)
mechanism: Each message n is encoded as An+B. Adding two codewords in a conventional binary adder produces A(i+j)+2B, which differs from the code A(i+j)+B by B. An odd A other than 1 guarantees minimum distance at least two. The minimum-redundancy detecting construction uses A=3. A received word is checked by subtracting B and testing divisibility by A, or by testing directly for residue B modulo A. For A=3, the residue equals the difference between the one-counts in even and odd bit positions modulo 3. # p.333-p.336
choices:
  A: 3   # p.334
  code_distance: d2_detect   # p.333-p.334
new_choices:
  offset_B: nonnegative_integer — affine offset selected with A, base b, and code length g   # p.333-p.335
  digit_base_b: positive_integer — number base represented by each coded digit   # p.333
  complement_condition: A(b-1)+2B=2^g-1 — permits complementing a number by complementing every code bit   # p.333
  detection_method: {division_by_A, residue_B_mod_A, mod3_even_odd_weight} — arithmetic or combinational legality test   # p.336
slots:
  none
parameters: code length g; base b; A=3 for minimum-redundancy single-error detection; B determined from A(b-1)+2B=2^g-1 when bitwise complementation is required   # p.333-p.334
results:
| metric | value | unit | technology / device | baseline | condition | page |
| code redundancy | 1 to 3 | bits | UNKNOWN / 1960 | none | A=3 and minimum g | p.334 |
errors_and_checks: Minimum distance at least two detects every single-bit error. The residue test is zero, or B modulo A when B is not subtracted, if and only if no single error has occurred. False-alarm behavior outside the single-error model is not reported. # p.333, p.336
conditions: A=3 gives the least redundancy among the guaranteed single-error-detecting An+B codes. Multidigit addition requires a corrective addition determined by each digit's carry-in/carry-out, and interdigit carries must be blocked during that corrective cycle. Division-based checking is expensive in time, while the A=3 residue has a combinational implementation. # p.334-p.337
evidence: Theorems 1 and 4; Table I; “Error Detection and Correction”; Appendix I, pp.333-337.

### an_code  (role: proposes)
mechanism: A code with minimum distance at least three assigns a unique residue modulo A to every possible single-bit error and to the no-error case. The residue identifies the error position through table lookup or repeated arithmetic. The correction also covers any multi-bit pattern whose total numeric corruption is ±2^k. Codes with B=0 eliminate post-add correction when the whole operand is one digit and the base exceeds every result value. # p.334-p.337
choices:
  A: odd positive integer satisfying the rmin constraint [outside domain]   # p.334
  code_distance: d3_correct   # p.334, p.336
new_choices:
  offset_B: nonnegative_integer — B=0 permits an unadjusted coded sum in a single-digit representation   # p.335
  error_location_method: {table_lookup, arithmetic_residue_sequence} — maps a residue modulo A to the erroneous bit position   # p.336-p.337
slots:
  none
parameters: base b≤rmin under Theorem 2; minimum code length g from A(b-1)≤2^g-1; B from A(b-1)+2B=2^g-1 when complementation is required   # p.334-p.335
results:
| metric | value | unit | technology / device | baseline | condition | page |
| code length | 8 | bits | UNKNOWN / 1960 | none | base 10; codes 19n+42, 23n+24, 25n+15, or 27n+6 | p.335 |
| code length | 35 | binary symbols | UNKNOWN / 1960 | none | B=0 code 71n | p.336 |
| largest coded number | 483,939,977 | integer | UNKNOWN / 1960 | none | 35-symbol 71n code | p.336 |
| redundancy | 6.15 | bits | UNKNOWN / 1960 | 35-digit Hamming code: 6 bits | 35-symbol 71n code | p.336 |
errors_and_checks: Minimum distance at least three corrects every single-bit error. A received word differing by ±2^k is also correctable even when several bit positions differ. Detection may use an A divisible by 3 for the fast modulo-3 test, with division by A deferred until an error occurs. # p.336-p.337
conditions: General multidigit An+B addition needs correction for B and digit carry-in/carry-out. A B=0 design removes correction only when a base larger than every encountered number permits a single coded digit. Theorem 2 does not establish a correcting B=0 code, while Theorem 3 establishes one when Armin=2^k-1 and b=rmin+1. # p.335-p.336
evidence: Theorems 2, 3, and 5; Tables II-IV; “Codes with B=0”; “Error Detection and Correction”; Appendix II, pp.334-337.

## new_families
none

## space_gaps
* The an_code A domain needs arbitrary odd positive integers rather than only {3, 7, 15, 31}; the admissible value depends on the required distance and base. # p.333-p.335
* The an_code family needs an affine offset_B choice because B controls complementation, addition correction, and the B=0 single-digit variant. # p.333-p.335
* The an_code family needs detection_method/error_location_method choices for division, modulo-3 one-count logic, table lookup, and arithmetic residue decoding. # p.336-p.337

## open_questions
* Several entries in Tables I-III are corrupted in the supplied text extraction, so any code coefficients not recorded above require inspection of the page images.
