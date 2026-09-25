---
handle: cornea_1999
citation: Cornea-Hasegan, Golliver, Markstein, "Correctness Proofs Outline for Newton-Raphson Based Floating-Point Divide and Square Root Algorithms", 14th IEEE Symposium on Computer Arithmetic, 1999
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary single precision, binary double precision, binary double-extended precision]
authority: landmark
pages_read: 10 / 10
---

## summary
The paper proves IEEE-754 correctness for software-driven Newton-Raphson floating-point divide/square-root algorithms that use fused multiply-add operations. The proofs cover all four IEEE rounding modes/status flags and identify operand regions requiring alternate software algorithms because intermediate results may overflow, underflow, or lose precision.

## families
### newton_raphson  (role: proposes)
mechanism: The divide algorithm obtains y0 as an approximation to 1/b, performs four Newton-Raphson reciprocal iterations, and forms q0, q1, and q2 through residual corrections. Fused multiply-add operations limit each multiply-add to one rounding. The proof establishes that q1 is within 1 ulp of a/b and that the final correction produces q2 = (a/b)rnd, including the all-ones denominator-significand case. # p.3–6
choices:
  iterations: 4 [outside domain]   # p.5
  dedicated_multiplier: false   # p.1, p.5
new_choices:
  operation: divide — identifies whether the Newton-Raphson datapath computes divide or square root   # p.3
  internal_exponent_extension_bits: 2 or more — extra exponent bits sufficient to avoid intermediate overflow/underflow/precision loss   # p.6
slots:
  seed: UNKNOWN (the initial approximation is supplied by a table-lookup instruction, whose implementation is not stated)   # p.5
  iter_mult: UNKNOWN (the computations use processor fused multiply-add operations)   # p.3, p.5
  final_round: exclusion_zone_proof   # p.4–5
parameters: double-extended operands/results; |ε0| ≤ 2^-m with m ≥ 8.886; four reciprocal iterations; three quotient approximations; final rounding in any of four IEEE modes   # p.5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| Software Assistance frequency | 25% | % | UNKNOWN; year 1999 | all input pairs | double-extended precision; intermediate/final precision equal | p.6 |
| Software Assistance frequency | 31.8% | % | UNKNOWN; year 1999 | all input pairs | single precision; intermediate/final precision equal | p.6 |
errors_and_checks: q1 is within 1 ulp of a/b; q2 is correctly rounded in rn/rm/rp/rz. The last step sets the inexact flag correctly because a/b ∈ FN iff the unrounded q2* ∈ FN. Invalid/divide-by-zero are assumed handled by the reciprocal-approximation instruction. # p.5–7
conditions: Software Assistance is required when eb ≤ emin – 2, eb ≥ emax – 2, ea – eb ≥ emax, ea – eb ≤ emin + 1, or ea ≤ emin + N – 1, when intermediate/final precisions are equal. An exponent field at least two bits wider avoids these intermediate failures. # p.6
evidence: Floating-Point Divide Correctness Proof, Theorems 1–4, double-extended divide algorithm, Figure 4, Software Assistance Conditions, and Status Flags Settings, pp.3–7.

### newton_raphson  (role: proposes)
mechanism: The square-root algorithm obtains y0 as an approximation to 1/√a and performs two Newton-Raphson inverse-square-root improvements. The algorithm forms S, S1, and R as progressively refined square-root approximations through FMA-based residual corrections. Exclusion-zone bounds prove correct rounding except for enumerated difficult points, which C/assembly implementations and Mathematica programs verify separately. # p.7–10
choices:
  iterations: 2   # p.9
  dedicated_multiplier: false   # p.1, p.9
new_choices:
  operation: square_root — identifies the inverse-square-root recurrence and square-root reconstruction   # p.7
  internal_exponent_extension_bits: 1 or more — extra exponent bits sufficient to prevent intermediate precision loss   # p.10
slots:
  seed: UNKNOWN (the initial 1/√a approximation is supplied by a table-lookup instruction, whose implementation is not stated)   # p.9
  iter_mult: UNKNOWN (the computations use processor fused multiply-add operations)   # p.7, p.9
  final_round: exclusion_zone_proof   # p.7–9
parameters: double-extended operand/result; |ε0| ≤ 2^-m with m ≥ 8.831; 17 computational steps; two inverse-square-root improvements; three square-root approximations; final rounding in any IEEE mode   # p.9
results:
| metric | value | unit | technology / device | baseline | condition | page |
| Software Assistance frequency | 0.05% | % | UNKNOWN; year 1999 | all input values | double-extended precision; intermediate/final precision equal | p.9 |
| Software Assistance frequency | 9.6% | % | UNKNOWN; year 1999 | all input values | single precision; intermediate/final precision equal | p.9 |
errors_and_checks: The unrounded R* lies within half the applicable exclusion-zone width of √a; R is correctly rounded in rn/rm/rp/rz. The last step sets the inexact flag correctly because √a ∈ FN iff R* ∈ FN. # p.8–10
conditions: Software Assistance is required when ea ≤ emin + N – 1 because an intermediate di may lose precision. An exponent field at least one bit wider prevents this precision loss. Difficult rounding cases require separate verified sequences. # p.9–10
evidence: Floating-Point Square Root Correctness Proof, Theorems 5–6, Figures 5–8, double-extended square-root algorithm, Software Assistance Conditions, and Status Flags Settings, pp.7–10.

### exclusion_zone_proof  (role: extends)
mechanism: The proof bounds the distance between an exact quotient/square root and floating-point numbers or rounding midpoints. If the final unrounded approximation differs from the exact result by less than half the minimum exclusion-zone width, both values round identically. Enumerated quotient/square-root cases nearest a boundary are handled by strengthened theorems or separately verified algorithms. # p.4, p.7–9
choices: none
new_choices: none
slots: none
parameters: divide bounds 2^-N ulp around floating-point numbers and 2^-N-1 ulp around midpoints; square-root generic bounds 2^-N-1 ulp and 2^-N-3 ulp; four IEEE rounding modes   # p.4, p.8
results:
| metric | value | unit | technology / device | baseline | condition | page |
| rounding modes proven | 4 | IEEE rounding modes | UNKNOWN; year 1999 | exact infinite-precision result | divide and square root | p.2, p.5, p.9 |
errors_and_checks: The contract is correct IEEE rounding rather than a bounded approximate result. The proof also covers correct overflow/underflow/inexact flag behavior under its stated Software Assistance assumptions. # p.6–7, p.9–10
conditions: The exclusion-zone argument requires proved approximation-error bounds and separate treatment of the finite sets of difficult boundary cases. # p.4–5, p.8–9
evidence: Figure 2, Theorems A–D, Theorems 1 and 5–6, and Figures 3, 5, 6, and 7, pp.3–9.

## new_families
none

## space_gaps
* `newton_raphson.iterations` excludes the four reciprocal iterations used by the double-extended divide example. # p.5
* `newton_raphson` lacks an operation choice distinguishing divide/reciprocal-square-root/square-root algorithms. # p.3, p.7
* `newton_raphson` lacks an internal exponent-width choice, although two extra exponent bits for divide and one for square root change the Software Assistance requirement. # p.6, p.10
* `newton_raphson.iter_mult` cannot name `classic_fma`, although fused multiply-add is the required iterative arithmetic primitive. # p.3, p.5, p.7, p.9

## open_questions
* The dimensions/encoding/implementation of the initial-approximation lookup tables are not stated.
* The iteration counts and schedules of the other single/double/double-extended latency-optimized and throughput-optimized variants are not reported.
* The alternate Software Assistance algorithms are described as devised and verified, but their computational sequences are not included.
