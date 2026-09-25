---
handle: clarke_1996
citation: Clarke, German, Zhao, "Verifying the SRT Division Algorithm Using Theorem Proving Techniques", CAV, LNCS 1102, 1996
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [fp64]
authority: incremental
pages_read: 111-122 / 12
---

## summary
The paper formalizes and automatically proves the correctness of a radix-4 SRT floating-point division core similar to the Intel Pentium divider. The verified circuit selects each quotient digit from an estimated partial remainder while the full-width remainder subtraction proceeds in parallel.

## families
### srt_high_radix  (role: analyzes)
mechanism: The divider applies the recurrence p_j+1 = 4(p_j - q_j·Divisor) and uses redundant quotient digits {-2,-1,0,1,2}. A full-width DALU computes the next partial remainder while an 8-bit GALU estimates its leading bits. QUO LOGIC combines the estimate with four leading divisor bits to select the next digit from a lookup table. QPOS and QNEG accumulate positive and negative digits separately, and a final subtraction produces the quotient.   # pp.113-116
choices:
  radix: 4   # p.113
new_choices:
  quotient_digit_set: {-2,-1,0,1,2} — the redundant digit set avoids multiplication of the divisor by 3   # p.114
slots:
  digit_select: qds_table   # pp.116-119
parameters: radix 4; b/2 iterations for b quotient bits; four full-width registers; full-width DALU; 8-bit GALU; 4 leading divisor bits for table selection; 64-bit subtraction per cycle for double precision; 34 calculation cycles; proof applies to word lengths n > 8 bits   # pp.112-116, p.120
results:
| metric | value | unit | technology / device | baseline | condition | page |
| quotient-generation iterations | b/2 | iterations | UNKNOWN / 1996 | radix-2 division: b iterations | b bits of quotient accuracy | p.113 |
| inner-cycle subtraction width | 64 | bits | UNKNOWN / 1996 | UNKNOWN | double-precision arguments | p.113 |
| calculation latency | 34 | cycles | UNKNOWN / 1996 | UNKNOWN | modeled division computation | p.120 |
| formally verified word-length range | n > 8 | bits | UNKNOWN / 1996 | finite-state verification of a single word length | algebraic proof over real-valued signals | pp.112, 121 |
errors_and_checks: Analytica proves that Quotient·d + rout scales by four each cycle, the GALU estimate bounds rout, the remainder stays inside the defined quotient-table region, and -2d/3 ≤ rout ≤ 2d/3 is invariant. The scaled remainder therefore converges to zero by a factor of 1/4 per cycle. The paper does not specify final rounding accuracy or a hardware fault model.   # pp.120-121
conditions: The circuit is the significand arithmetic core of a floating-point divider; separate hardware handles signs and exponents. The proof treats circuit signals as arbitrary real numbers and covers all word lengths n > 8, but this abstraction may fail for circuits whose correctness depends on a finite representable set. The divisor is normalized so its four-bit prefix is one of 1.000 through 1.111.   # pp.112, 118, 121
evidence: §2.2 recurrence and digit set, pp.113-114; Fig. 1 and §2.3 circuit structure, pp.114-116; Table 1 quotient prediction, pp.116-119; §4 axioms and correctness proof, pp.118-121.

## new_families
none

## space_gaps
* srt_high_radix lacks a quotient_digit_set choice for the explicitly verified redundant set {-2,-1,0,1,2}.   # p.114
* qds_table lacks choices for the estimated-remainder width, divisor-prefix width, and boundary-dependent use of low estimate bits.   # pp.116-119

## open_questions
* The paper does not map {-2,-1,0,1,2} to minimal/intermediate/maximal digit_redundancy, so the merge pass must not assign that choice.
* The modeled word length is not fixed: the discussion gives a 64-bit double-precision subtraction and 34 cycles, while the proof covers every n > 8.   # pp.112-113, p.120
* The abridged paper omits initialization details and the complete convergence development.   # pp.112, 120
