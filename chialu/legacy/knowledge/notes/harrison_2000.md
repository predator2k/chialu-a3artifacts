---
handle: harrison_2000
citation: Harrison, "Formal Verification of IA-64 Division Algorithms", TPHOLs, LNCS 1869, 2000
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [single, double, double-extended, register, SIMD single]
authority: incremental
pages_read: 233-251 / 19
---

## summary
The paper formally verifies IA-64 software division algorithms built from `frcpa` and fused multiply-add instructions. The algorithms refine reciprocal/quotient approximations and establish correctly rounded IEEE results with correct flags for scalar/SIMD formats. Stronger final-correction theorems reduce the extended-precision algorithm by one `fma` latency. 

## families
### newton_raphson  (role: extends)
mechanism: `frcpa` supplies an initial approximation `y` to `1/b`; `e = 1-by` and `y' = y+ey` square the reciprocal relative error. Quotient refinement uses `r = a-bq` and `q' = q+ry`. The scalar single algorithm uses higher intermediate precision, while the SIMD single algorithm keeps every intermediate operation at single precision. # pp.239-249
choices:
  iterations: 2 (scalar single algorithm)   # p.247
new_choices:
  refinement_schedule: repeated_newton | direct_power_series — reciprocal refinement may repeat the linear Newton correction or evaluate a longer polynomial in `e` directly   # p.242
  intermediate_precision: register | single — the scalar algorithm uses higher register precision, while the SIMD algorithm uses single precision throughout   # pp.246-248
slots:
  seed: UNKNOWN [`frcpa` supplies the seed, but its hardware mechanism is not described]   # p.239
  iter_mult: UNKNOWN [`fma`/`fnma` instructions perform the iteration, but their multiplier microarchitecture is not described]   # pp.240-249
  final_round: exclusion_zone_proof (scalar single); back_multiply_remainder (SIMD single/extended)   # pp.247-249
parameters: scalar single: 6 parallel stages, final `q3` rounded to register double and then single; SIMD single: 6 parallel stages; improved extended: 8 stages rather than 9   # pp.246-249
results:
| metric | value | unit | technology / device | baseline | condition | page |
| reciprocal-seed error | `<2^-8.886` | relative error | UNKNOWN node; IA-64/Itanium; 2000 | exact `1/b` | nonexceptional `frcpa` result | p.239 |
| reciprocal-seed precision | `at most 11` | significant bits | UNKNOWN node; IA-64/Itanium; 2000 | exact `1/b` | nonexceptional `frcpa` result | p.239 |
| scalar `q3` pre-round error | `<197509/2^60` | relative error | UNKNOWN node; IA-64/Itanium; 2000 | exact `a/b` | scalar single algorithm | p.247 |
| SIMD `y3` pre-round error | `<=657/2^50` | relative error | UNKNOWN node; IA-64/Itanium; 2000 | exact `1/b` | SIMD single algorithm | p.248 |
| extended algorithm reduction | `1` | `fma` latency | UNKNOWN node; IA-64/Itanium; 2000 | 9-stage Markstein-based sequence | stronger reciprocal-error theorem permits an 8-stage sequence | p.249 |
errors_and_checks: The verified algorithms produce the IEEE-correct quotient and set IEEE flags/exceptions appropriately. The SIMD proof explicitly checks the 165 largest divisor mantissas after the general reciprocal-error argument excludes other cases. # pp.239-240,248-249
conditions: Higher intermediate precision permits a simple exclusion-zone proof. SIMD/extended operation lacks higher precision and requires the refined Markstein theorem plus explicit treatment of exceptional mantissas. The parallel `frcpa` predicate selects another algorithm when intermediate overflow/underflow is possible. # pp.239,243,247-249
evidence: §§3.2-3.3; §§4.1-4.2; scalar/SIMD instruction schedules on pp.246-249

### back_multiply_remainder  (role: extends)
mechanism: The final correction computes an exact residual `r = a-bq` with `fnma`, then computes `q' = q+ry` with `fma`. The strengthened theorem requires `q` within 1 ulp of `a/b` and `y` within relative error `1/2^p` of `1/b`; `y` need not be a perfectly rounded reciprocal. # pp.242-245
choices:
new_choices:
  reciprocal_requirement: correctly_rounded | relative_error_bounded — the strengthened theorem replaces Markstein's correctly rounded reciprocal requirement with a relative-error bound   # pp.243-245
slots: none
parameters: two final floating-point operations; precision parameter `p`; round-to-nearest theorem # pp.243-244
results:
| metric | value | unit | technology / device | baseline | condition | page |
| initial quotient tolerance | `<=1` | ulp | UNKNOWN node; IA-64/Itanium; 2000 | true quotient `a/b` | normalized quotient and theorem preconditions | p.244 |
| reciprocal tolerance | `<1/2^p` | relative error | UNKNOWN node; IA-64/Itanium; 2000 | exact reciprocal `1/b` | strengthened final-correction theorem | p.244 |
errors_and_checks: The two operations yield the correctly rounded-to-nearest quotient. Exact representable cases/directed rounding modes are handled separately in the SIMD proof, and correctness in all rounding modes implies correct inexact-flag behavior. # pp.238,243-244,248
conditions: The residual is exactly representable when the stated format/range/normalization and 1-ulp hypotheses hold. # pp.243-244
evidence: Theorems 1-4, pp.243-246; SIMD application, pp.248-249

### exclusion_zone_proof  (role: extends)
mechanism: Every floating-point number or midpoint `c` has an exclusion zone around it. For representable `a`/`b`, either `a/b = c` or `abs(a/b-c) >= abs(a/b)/2^(2*p+2)`. A computed quotient closer than this bound rounds identically to the exact quotient. # pp.237-239
choices:
new_choices: none
slots: none
parameters: operand precision `p`; floating-point numbers and midpoints represented by a format with one extra precision bit # pp.237-238
results:
| metric | value | unit | technology / device | baseline | condition | page |
| exclusion-zone distance | `>=abs(a/b)/2^(2*p+2)` | absolute error | UNKNOWN node; theoretical result; 2000 | floating-point number or midpoint `c` | `a/b != c` and theorem preconditions | p.238 |
errors_and_checks: The proof covers all rounding modes when the approximation lies closer to `a/b` than every floating-point number or midpoint. Exact floating-point quotients and denormal midpoint cases require separate treatment. # pp.237-238
conditions: The scalar single algorithm satisfies the bound after register-double rounding. Extended/SIMD algorithms cannot generally obtain the required bound from higher intermediate precision and require more precise theorems. # pp.239,247-248
evidence: §§2.1-2.3, pp.237-239; scalar application, p.247

### sig_div_then_round  (role: instantiates)
mechanism: IA-64 implements floating-point division as straight-line software. `frcpa` handles exceptional inputs or supplies a reciprocal seed; predicated `fma`/`fnma` instructions refine the quotient; the last instruction rounds in the ambient IEEE mode and format. # pp.239-240,246-249
choices:
new_choices:
  optimization_target: latency | throughput — Intel supplies separate algorithm variants optimized for dependency latency or independent-operation throughput   # p.240
slots:
  sig_div: newton_raphson   # pp.240-249
  round: UNKNOWN [the final ambient rounding is performed by `fma`, which has no matching rounding-slot family]   # pp.246-249
parameters: separate algorithms for single/double/extended/SIMD; four IEEE rounding modes; scalar/SIMD examples each use 6 parallel stages # pp.234,240,246-248
results:
| metric | value | unit | technology / device | baseline | condition | page |
| scalar schedule depth | `6` | parallel stages | UNKNOWN node; IA-64/Itanium; 2000 | UNKNOWN | single precision with higher internal precision | pp.246-247 |
| SIMD schedule depth | `6` | parallel stages | UNKNOWN node; IA-64/Itanium; 2000 | UNKNOWN | SIMD single precision | p.248 |
errors_and_checks: Intel-provided algorithms target IEEE-correct results, flags, and exceptions; the printed scalar/SIMD algorithms are formally verified under the modeled IA-64 ISA. # pp.239-240,247-250
conditions: Software division benefits from pipelined `fma` issue and algorithm substitution, but correctness relies on the processor implementing the modeled ISA and does not prevent code-transcription errors. # pp.235,250
evidence: §§1.2, 3.1, 4.1-4.2

### classic_fma  (role: instantiates)
mechanism: IA-64 `fma` computes `xy+z` with one rounding. `fms` computes `xy-z`, and `fnma` computes `z-xy`. Floating-point addition/multiplication are degenerate `fma` cases, and division algorithms use the fused residual/refinement operations without intermediate rounding. # pp.233,240-249
choices:
  subsume_fp_add: true   # p.233
new_choices:
  sign_variant_instructions: `fms` | `fnma` — instruction variants switch operand signs for subtraction/negated multiplication-addition   # p.233
slots:
  align: UNKNOWN   # p.233
  lza: UNKNOWN   # p.233
  cpa: UNKNOWN   # p.233
  round: UNKNOWN   # p.233
  multiplier: UNKNOWN   # p.233
parameters: latency is several clock cycles; initiation interval is one cycle # p.235
results:
| metric | value | unit | technology / device | baseline | condition | page |
| initiation interval | `1` | cycle | UNKNOWN node; IA-64/Itanium; 2000 | typical hardware division implementation | independent basic floating-point operations | p.235 |
errors_and_checks: `fma` has one rounding error. The division verification assumes that the underlying operations are IEEE-correct rather than verifying their gate-level implementation. # pp.233,250
conditions: Pipelined `fma` permits several software divisions to proceed concurrently. The formal result depends on accurate ISA implementation. # pp.235,250
evidence: §§1.1-1.2, 3.1-3.3, 4.1-4.2

## new_families
none

## space_gaps
* The `newton_raphson.seed` slot needs a value for an opaque ISA-provided reciprocal approximation such as `frcpa`; the document specifies its output contract but not its internal seed-table mechanism. # p.239
* The `sig_div_then_round.round` slot lacks final rounding performed directly by the ambient rounding mode of the last `fma`. # pp.246-249

## open_questions
* The document does not identify the hardware structure that generates the `frcpa` approximation.
* The document gives no process node, exact `fma` latency, issue width, area, power, or measured division timing.
* The claim that `y3` is not perfectly rounded for precisely 12 divisor significands comes from an analysis that was not formalized in HOL. # p.249
